from fastapi import FastAPI, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from models import SessionLocal, LicenseKey
from webhook import router as webhook_router
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import hashlib

def ip_and_key_func(request: Request) -> str:
    ip = get_remote_address(request)
    key = request.headers.get("x-license-key", "no-key")
    key_hash = hashlib.sha256(key.encode()).hexdigest()[:16]
    return f"{ip}:{key_hash}"

limiter = Limiter(key_func=ip_and_key_func)

app = FastAPI(title="UA-MCP License API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(webhook_router, prefix="/stripe")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ValidateRequest(BaseModel):
    key: str

class ValidateResponse(BaseModel):
    valid: bool
    tier: str

@app.post("/validate", response_model=ValidateResponse)
@limiter.limit("5/minute")
def validate_license(request: Request, req: ValidateRequest, db: Session = Depends(get_db)):
    license_key = db.query(LicenseKey).filter(LicenseKey.key == req.key).first()
    if not license_key:
        raise HTTPException(status_code=404, detail="License key not found")
    if not license_key.active:
        raise HTTPException(status_code=400, detail="License key is inactive")
    
    return {"valid": True, "tier": license_key.tier}

@app.get("/")
def read_root(db: Session = Depends(get_db)):
    # Run a lightweight query to ensure Supabase registers API activity
    # and doesn't auto-pause the project after 7 days.
    from sqlalchemy import text
    db.execute(text("SELECT 1"))
    return {"message": "UA-MCP License API is running", "database": "connected"}
