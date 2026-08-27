from psb_app.common import (
    clean,
    datetime,
    days_until,
    db_insert,
    db_where,
    hashlib,
    now,
    os,
    pd,
    st,
    timedelta,
    uid,
)
from core.system_write import system_write

QR_RATE_LIMIT = int(os.getenv("QR_RATE_LIMIT_PER_MINUTE", "30"))

def _request_fingerprint() -> str:
    try:
        headers = getattr(st, "context", None)
        headers = getattr(headers, "headers", {}) if headers else {}
        raw = str(headers.get("X-Forwarded-For") or headers.get("CF-Connecting-IP") or headers.get("X-Real-IP") or "unknown")
    except Exception:
        raw = "unknown"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def _qr_rate_limited(fingerprint: str) -> bool:
    try:
        window_start = (datetime.utcnow() - timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S")
        recent = db_where("qr_verification_events", "client_fingerprint = :fp and verified_on >= :since", (("fp", fingerprint), ("since", window_start)))
        return len(recent) >= QR_RATE_LIMIT
    except Exception:
        return True

def _log_qr_event(cert_id: str, result: str, fingerprint: str, response_code: str, requested_path: str) -> None:
    try:
        with system_write("qr_verification_event"):
            db_insert("qr_verification_events", {
                "event_id": uid("QR"), "certificate_id": cert_id[:128], "verified_on": now(),
                "result": result, "client_fingerprint": fingerprint, "response_code": response_code,
                "requested_path": requested_path[:512],
            })
    except Exception:
        pass

def public_qr_verify_page(cert_id: str) -> None:
    apply_style()
    cert_id = clean(cert_id)[:128]
    fingerprint = _request_fingerprint()
    path = "/?verify=" + cert_id
    if not cert_id:
        _log_qr_event("", "InvalidRequest", fingerprint, "400", path)
        st.error("Certificate ID is required.")
        return
    if _qr_rate_limited(fingerprint):
        _log_qr_event(cert_id, "RateLimited", fingerprint, "429", path)
        st.error("Too many verification attempts. Please try again later.")
        return
    certs = db_where("authorization_certificates", "certificate_id = :cid", (("cid", cert_id),))
    if certs.empty:
        _log_qr_event(cert_id, "NotFound", fingerprint, "404", path)
        st.title("Pakistan Shipping Bureau")
        st.caption("Certificate Verification")
        st.error("Certificate not found.")
        return
    row = certs.iloc[0]
    valid = str(row.get("status", "")).lower() == "valid" and days_until(row.get("expiry_date", "")) >= 0
    _log_qr_event(cert_id, "Valid" if valid else "Invalid", fingerprint, "200", path)
    st.title("Pakistan Shipping Bureau")
    st.caption("Certificate Verification")
    (st.success if valid else st.error)("Certificate is valid." if valid else "Certificate is expired, revoked, suspended, withdrawn, or otherwise invalid.")
    c1, c2 = st.columns(2)
    c1.metric("Certificate", str(row.get("certificate_id", cert_id)))
    c2.metric("Status", "Valid" if valid else "Invalid")
    public = {
        "certificate_id": row.get("certificate_id", ""), "holder": row.get("name", ""),
        "scope": row.get("scope", ""), "job_type": row.get("job_type", ""),
        "issue_date": row.get("issue_date", ""), "expiry_date": row.get("expiry_date", ""),
        "status": "Valid" if valid else "Invalid",
    }
    st.dataframe(pd.DataFrame([public]), use_container_width=True, hide_index=True)
    st.caption("This public endpoint shows verification information only; confidential PSB records are not exposed.")

def qr_verify_page(actor):
    st.header("QR / Public Certificate Verification")
    cert_id = st.text_input("Certificate ID")
    if st.button("Verify") and cert_id:
        public_qr_verify_page(cert_id)
