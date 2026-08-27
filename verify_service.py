from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
import os, hashlib, time, html
from sqlalchemy import create_engine, text

app=FastAPI(title="PSB Certificate Verification", docs_url=None, redoc_url=None)
DB=os.getenv("DATABASE_URL","")
RATE_LIMIT=int(os.getenv('QR_RATE_LIMIT_PER_MINUTE','30'))

def engine():
    u=DB.replace("postgresql://","postgresql+psycopg2://",1) if DB.startswith("postgresql://") else DB
    return create_engine(u,pool_pre_ping=True)

def fingerprint(request: Request) -> str:
    raw=request.headers.get('x-forwarded-for') or request.headers.get('cf-connecting-ip') or request.client.host if request.client else 'unknown'
    return hashlib.sha256(str(raw).encode()).hexdigest()

def valid_id(cid: str) -> bool:
    return len(cid)<=128 and cid.replace('-','').replace('_','').isalnum()

@app.get("/health")
def health(): return {"status":"ok","service":"certificate-verification"}

@app.get("/verify/{certificate_id}")
def verify(certificate_id: str, request: Request):
    if not valid_id(certificate_id): raise HTTPException(400,"Invalid certificate reference")
    fp=fingerprint(request)
    with engine().begin() as conn:
        recent=conn.execute(text("select count(*) from qr_verification_events where client_fingerprint=:fp and verified_on >= CURRENT_TIMESTAMP - interval '1 minute'"),{"fp":fp}).scalar() or 0
        if int(recent)>=RATE_LIMIT:
            conn.execute(text("insert into qr_verification_events(event_id,certificate_id,verified_on,result,client_fingerprint,response_code,requested_path) values (:eid,:cid,CURRENT_TIMESTAMP,'RateLimited',:fp,'429',:path)"),{"eid":os.urandom(12).hex(),"cid":certificate_id,"fp":fp,"path":"/verify/"+certificate_id})
            raise HTTPException(429,"Too many verification attempts. Please try again later.")
        row=conn.execute(text("select certificate_id,name,scope,job_type,issue_date,expiry_date,public_status,status from authorization_certificates where certificate_id=:cid limit 1"),{"cid":certificate_id}).mappings().first()
        if not row:
            result={'certificate_id':certificate_id,'verified':False,'status':'Not Found'}
            conn.execute(text("insert into qr_verification_events(event_id,certificate_id,verified_on,result,client_fingerprint,response_code,requested_path) values (:eid,:cid,CURRENT_TIMESTAMP,'NotFound',:fp,'404',:path)"),{"eid":os.urandom(12).hex(),"cid":certificate_id,"fp":fp,"path":"/verify/"+certificate_id})
            raise HTTPException(404,"Certificate not found")
        verified=str(row.get('public_status') or row.get('status') or '').lower() in {'valid','active','issued'}
        safe={k:row.get(k) for k in ('certificate_id','name','scope','job_type','issue_date','expiry_date','public_status','status')}
        safe['verified']=verified
        conn.execute(text("insert into qr_verification_events(event_id,certificate_id,verified_on,result,client_fingerprint,response_code,requested_path) values (:eid,:cid,CURRENT_TIMESTAMP,:result,:fp,'200',:path)"),{"eid":os.urandom(12).hex(),"cid":certificate_id,"result":"Valid" if verified else "Invalid","fp":fp,"path":"/verify/"+certificate_id})
    return JSONResponse(safe)

@app.get("/verify/{certificate_id}/page", response_class=HTMLResponse)
def verify_page(certificate_id: str, request: Request):
    response = verify(certificate_id, request)
    data = response.body.decode() if hasattr(response, 'body') else ''
    return HTMLResponse(f"<html><head><title>PSB Certificate Verification</title></head><body><h1>Pakistan Shipping Bureau</h1><pre>{html.escape(data)}</pre></body></html>")
