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

import json

def get_incoming_edges(graph: dict, target: str) -> list:
    if not graph:
        return []
    rev_deps = set()
    edges = graph.get("edges")
    if isinstance(edges, list):
        for edge in edges:
            if isinstance(edge, dict) and edge.get("target") == target:
                rev_deps.add(edge.get("source"))
    files = graph.get("files")
    if isinstance(files, dict):
        for file_id, file_data in files.items():
            if isinstance(file_data, dict):
                imports = file_data.get("imports")
                if isinstance(imports, list) and target in imports:
                    rev_deps.add(file_id)
    return list(rev_deps)

def normalize_node_id(node_id: str, default_type: str = 'file') -> str:
    prefixes = ['file:', 'func:', 'class:']
    for prefix in prefixes:
        if node_id.startswith(prefix):
            return node_id
    return f"{default_type}:{node_id}"

def validate_complexity(complexity: str) -> str:
    valid_complexities = ['simple', 'moderate', 'complex']
    if complexity in valid_complexities:
        return complexity
    raise ValueError(f"Invalid complexity: {complexity}. Must be simple, moderate, or complex.")

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
    graph_data_str = req.data.get("graphData")
    if not graph_data_str:
         raise HTTPException(status_code=400, detail="Missing graphData")
    try:
        graph = json.loads(graph_data_str)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format for graphData")
        
    valid_nodes = 0
    invalid_nodes = 0
    errors = []
    
    nodes = graph.get("nodes", [])
    if isinstance(nodes, list):
        for node in nodes:
            try:
                node_id = node.get("id")
                if not node_id:
                    raise ValueError("Node is missing id")
                norm_id = normalize_node_id(node_id)
                comp = node.get("complexity")
                if comp:
                    validate_complexity(comp)
                valid_nodes += 1
            except Exception as e:
                invalid_nodes += 1
                errors.append(str(e))
                
    return {
        "valid_nodes": valid_nodes,
        "invalid_nodes": invalid_nodes,
        "errors": errors[:5]
    }

@app.post("/analyze/find-callers")
@limiter.limit("20/minute")
def analyze_find_callers(request: Request, req: AnalyzeRequest, db: Session = Depends(get_db)):
    enforce_quota_and_tier(request, db, ["Pro", "Team"])
    target = req.data.get("target")
    max_hops = req.data.get("maxHops", 2)
    graph = req.data.get("graph")
    
    if not target or not graph:
        raise HTTPException(status_code=400, detail="Missing target or graph")
        
    visited = set()
    result = set()
    
    current_level = [target]
    for _ in range(max_hops):
        next_level = set()
        for node in current_level:
            if node in visited:
                continue
            visited.add(node)
            
            callers = get_incoming_edges(graph, node)
            for caller in callers:
                result.add(caller)
                next_level.add(caller)
        current_level = list(next_level)
        if not current_level:
            break
            
    return {"callers": list(result)}

@app.post("/analyze/impact-analysis")
@limiter.limit("20/minute")
def analyze_impact_analysis(request: Request, req: AnalyzeRequest, db: Session = Depends(get_db)):
    enforce_quota_and_tier(request, db, ["Pro", "Team"])
    target = req.data.get("target")
    graph = req.data.get("graph")
    
    if not target or not graph:
        raise HTTPException(status_code=400, detail="Missing target or graph")
        
    result = set()
    queue = [target]
    
    while queue:
        node = queue.pop(0)
        callers = get_incoming_edges(graph, node)
        
        for caller in callers:
            if caller not in result:
                result.add(caller)
                queue.append(caller)
                
    return {"impacted": list(result)}
