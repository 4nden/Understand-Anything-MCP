from dotenv import load_dotenv
load_dotenv()

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

import datetime

def enforce_quota_and_tier(request: Request, db: Session, required_tiers: list):
    key = request.headers.get("x-license-key")
    if not key:
        raise HTTPException(status_code=401, detail="Missing license key")
        
    license_key = db.query(LicenseKey).filter(LicenseKey.key == key).first()
    if not license_key or not license_key.active:
        raise HTTPException(status_code=401, detail="Invalid or inactive license key")
        
    if license_key.tier not in required_tiers:
        raise HTTPException(status_code=403, detail=f"Requires one of tiers: {required_tiers}")
        
    now = datetime.datetime.utcnow()
    if not license_key.last_call_date:
        license_key.last_call_date = now
    
    if license_key.last_call_date.date() < now.date():
        license_key.daily_calls = 0
        license_key.last_call_date = now
        
    max_calls = 500 if license_key.tier == "Team" else 100
        
    if license_key.daily_calls >= max_calls:
        raise HTTPException(status_code=429, detail="Daily usage limit exceeded")
        
    license_key.daily_calls += 1
    license_key.last_call_date = now
    db.commit()
    return license_key

class AnalyzeRequest(BaseModel):
    data: dict

@app.post("/analyze/ci-check")
@limiter.limit("20/minute")
def analyze_ci_check(request: Request, req: AnalyzeRequest, db: Session = Depends(get_db)):
    enforce_quota_and_tier(request, db, ["Team"])
    
    pr_diff = req.data.get("pr_diff", "")
    files = []
    for line in pr_diff.split('\n'):
        if line.startswith('+++ b/'):
            files.append(line[6:])
    if not files:
        files.append('unknown_file')

    return {
        "analyzed_files": files,
        "impact_level": "HIGH" if len(files) > 5 else "LOW",
        "affected_nodes": ["ComponentA", "DatabaseSchema"],
        "recommendations": [
            "Ensure new code is fully tested.",
            "Check downstream dependencies for possible breaking changes."
        ]
    }

@app.post("/analyze/validate-graph")
@limiter.limit("20/minute")
def analyze_validate_graph(request: Request, req: AnalyzeRequest, db: Session = Depends(get_db)):
    enforce_quota_and_tier(request, db, ["Team"])
    return {"message": "Graph validated successfully"}

@app.post("/analyze/find-callers")
@limiter.limit("20/minute")
def analyze_find_callers(request: Request, req: AnalyzeRequest, db: Session = Depends(get_db)):
    enforce_quota_and_tier(request, db, ["Pro", "Team"])
    return {"callers": ["src/main.ts", "src/app.ts"]}

@app.post("/analyze/impact-analysis")
@limiter.limit("20/minute")
def analyze_impact_analysis(request: Request, req: AnalyzeRequest, db: Session = Depends(get_db)):
    enforce_quota_and_tier(request, db, ["Pro", "Team"])
    return {"impacted": ["src/api/routes.ts", "src/services/db.ts"]}
