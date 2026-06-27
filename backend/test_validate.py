from fastapi.testclient import TestClient
from main import app, get_db
from models import LicenseKey, Base, engine, SessionLocal
import pytest

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_validate_success():
    # Setup
    db = SessionLocal()
    db.query(LicenseKey).delete()
    test_key = LicenseKey(key="UA-TEST12345", tier="Pro", email="test@test.com")
    db.add(test_key)
    db.commit()
    db.close()

    # Test with correct schema
    response = client.post("/validate", json={"key": "UA-TEST12345"})
    assert response.status_code == 200
    assert response.json() == {"valid": True, "tier": "Pro"}

def test_validate_not_found():
    response = client.post("/validate", json={"key": "UA-NONEXISTENT"})
    assert response.status_code == 404
