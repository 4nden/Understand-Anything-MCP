import os
os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test"
os.environ["STRIPE_SECRET_KEY"] = "sk_test"
import time
import requests
import stripe
from fastapi.testclient import TestClient
from main import app, get_db
from models import LicenseKey, Base
from webhook import STRIPE_WEBHOOK_SECRET
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import time

# Use in-memory SQLite for testing so we don't hit locks from the running Uvicorn server
engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
from webhook import get_db as webhook_get_db
app.dependency_overrides[webhook_get_db] = override_get_db

client = TestClient(app)

from unittest.mock import patch

def test_e2e_flow():
    # Mock SMTP to avoid sending real emails
    mock_smtp_patcher = patch("smtplib.SMTP")
    mock_smtp = mock_smtp_patcher.start()
    mock_server = mock_smtp.return_value.__enter__.return_value
        
    db = SessionLocal()
    db.query(LicenseKey).delete()
    db.commit()
    db.close()
    
    # 1. Simulate Stripe Webhook for Free Tier (should fallback to Pro or whatever metadata says)
    timestamp = int(time.time())
    payload = '{"id":"evt_1","object":"event","type":"checkout.session.completed","data":{"object":{"id":"cs_test_1","customer_details":{"email":"team@example.com"},"metadata":{"tier":"Team"}}}}'
    secret = STRIPE_WEBHOOK_SECRET or "whsec_test"
    
    # Generate mock signature manually
    import hmac
    import hashlib
    timestamp = int(time.time())
    signed_payload = f"{timestamp}.{payload}"
    signature = hmac.new(secret.encode('utf-8'), signed_payload.encode('utf-8'), hashlib.sha256).hexdigest()
    header = f"t={timestamp},v1={signature}"
    
    response = client.post("/stripe/webhook", content=payload, headers={"stripe-signature": header})
    assert response.status_code == 200, f"Webhook failed: {response.text}"
    
    # 2. Check Database for generated key
    db = SessionLocal()
    key_record = db.query(LicenseKey).filter(LicenseKey.email == "team@example.com").first()
    assert key_record is not None
    assert key_record.tier == "Team"
    team_key = key_record.key
    db.close()
    
    print(f"Webhook processed successfully. Generated Team key: {team_key}")
    
    # 3. Simulate MCP Server calling /validate with Team key
    validate_res = client.post("/validate", json={"key": team_key}, headers={"x-license-key": team_key})
    assert validate_res.status_code == 200
    assert validate_res.json() == {"valid": True, "tier": "Team"}
    print("MCP Server successfully validated the Team key.")
    
    # 4. Assert Free-tier key is rejected by Team tools
    db = SessionLocal()
    free_key_record = LicenseKey(key="UA-FREE123", tier="Free", email="free@example.com")
    db.add(free_key_record)
    db.commit()
    db.close()
    
    validate_free = client.post("/validate", json={"key": "UA-FREE123"}, headers={"x-license-key": "UA-FREE123"})
    assert validate_free.json()["tier"] == "Free"
    
    # Asserting how requireTier('Team') would behave
    assert validate_free.json()["tier"] != "Team", "Free key should not have Team access"
    print("Free-tier key correctly identified as Free (would be rejected by ua_ci_check).")

    # 5. Test new backend analysis endpoints with Team key
    res_ci = client.post("/analyze/ci-check", json={"data": {"pr_diff": "+++ b/test.py"}}, headers={"x-license-key": team_key})
    assert res_ci.status_code == 200
    assert "analyzed_files" in res_ci.json()

    # 6. Test Daily Quota limits (Team limit = 500)
    db = SessionLocal()
    team_record = db.query(LicenseKey).filter(LicenseKey.key == team_key).first()
    team_record.daily_calls = 499
    db.commit()
    db.close()

    # Request 500 should succeed
    res_success = client.post("/analyze/validate-graph", json={"data": {"graphData": "{}"}}, headers={"x-license-key": team_key})
    assert res_success.status_code == 200

    # Request 501 should fail with 429
    res_fail = client.post("/analyze/validate-graph", json={"data": {"graphData": "{}"}}, headers={"x-license-key": team_key})
    assert res_fail.status_code == 429
    assert res_fail.json()["detail"] == "Daily usage limit exceeded"
    
    print("Quota logic and backend analysis endpoints verified successfully.")
    
    # 7. Test Graph Traversal (maxHops logic)
    db = SessionLocal()
    pro_key_record = LicenseKey(key="UA-PRO123", tier="Pro", email="pro@example.com")
    db.add(pro_key_record)
    db.commit()
    db.close()
    
    # Mock Graph: A -> B -> C
    # This means C is called by B, and B is called by A.
    mock_graph = {
        "edges": [
            {"source": "A", "target": "B"},
            {"source": "B", "target": "C"}
        ]
    }
    
    # Query callers of C with maxHops = 1 (should return exactly B)
    res_c_1hop = client.post("/analyze/find-callers", json={"data": {"target": "C", "maxHops": 1, "graph": mock_graph}}, headers={"x-license-key": "UA-PRO123"})
    assert res_c_1hop.status_code == 200
    assert set(res_c_1hop.json()["callers"]) == {"B"}
    
    # Query callers of C with maxHops = 2 (should return B and A)
    res_c_2hop = client.post("/analyze/find-callers", json={"data": {"target": "C", "maxHops": 2, "graph": mock_graph}}, headers={"x-license-key": "UA-PRO123"})
    assert res_c_2hop.status_code == 200
    assert set(res_c_2hop.json()["callers"]) == {"A", "B"}
    
    # Query impact analysis of A (should return B and C)
    res_a_impact = client.post("/analyze/impact-analysis", json={"data": {"target": "C", "graph": mock_graph}}, headers={"x-license-key": "UA-PRO123"})
    assert res_a_impact.status_code == 200
    # Wait! Impact analysis searches reverse dependencies!
    # If the mock graph is A -> B -> C, then callers of C are B and A. 
    # But wait, impact analysis of A? The prompt said "impact analysis ... full transitive closure of reverse dependencies".
    # Wait, reverse dependencies of A? A has no callers.
    # Impact analysis of C: callers of C are B, callers of B are A. So impact of C is {A, B}.
    assert set(res_a_impact.json()["impacted"]) == {"A", "B"}
    
    print("Graph Traversal logic (maxHops and impact) verified successfully.")

    print("End-to-End Test Passed!")

if __name__ == "__main__":
    test_e2e_flow()
