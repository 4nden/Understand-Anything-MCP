import os
os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test"
os.environ["STRIPE_SECRET_KEY"] = "sk_test"
import time
import requests
import stripe
from fastapi.testclient import TestClient
from main import app, get_db
from models import LicenseKey, Base, engine, SessionLocal
from webhook import STRIPE_WEBHOOK_SECRET
import time

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

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

    print("End-to-End Test Passed!")

if __name__ == "__main__":
    test_e2e_flow()
