"""Extracted service boundary from the legacy runtime.
The module consumes the established runtime context for compatibility.
"""
from __future__ import annotations
from psb_app.legacy_runtime import (
    STANDARDS,
    VERIFY_PUBLIC_URL,
    clean,
    make_qr_data_uri,
    pd,
    uid,
)

def build_certificate(auth: pd.Series) -> tuple[str, str, str]:
    cert_id = clean(auth.get('certificate_id')) or uid('CERT')
    verification_url = f'{VERIFY_PUBLIC_URL}/verify/{cert_id}'
    qr = make_qr_data_uri(verification_url)
    html = f"\n<!doctype html>\n<html><head><meta charset='utf-8'><title>PSB Authorization Certificate</title>\n<style>\nbody{{font-family:Arial,Helvetica,sans-serif;padding:34px;color:#101828;background:#f4f7f6}}\n.cert{{border:2px solid #061b36;border-top:8px solid #095b25;padding:36px;border-radius:12px;background:#fff;box-shadow:0 16px 42px rgba(1,8,25,.10)}}\nh1{{color:#010819;text-align:center;margin-bottom:0;letter-spacing:.03em}} h2{{text-align:center;color:#095b25;margin-top:6px;letter-spacing:.02em}}\n.row{{margin:12px 0;font-size:16px}} .sig{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:45px}\n.box{{border-top:1px solid #0f172a;padding-top:8px;font-size:12px}} .qr{{text-align:center;margin-top:25px}}\n@media (prefers-color-scheme: dark) {{\n    body{{color:#e6eef8}}\n    .cert{{background:#071122;border-color:rgba(255,255,255,0.06)}}\n    h1{{color:#e6eef8}} h2{{color:#bfe0ff}}\n    .box{{border-top:1px solid rgba(255,255,255,0.06)}}\n}}\n</style></head><body><div class='cert'>\n<h1>Pakistan Shipping Bureau</h1><h2>Digital Certificate of Authorization</h2>\n<div class='row'><b>Certificate ID:</b> {cert_id}</div>\n<div class='row'><b>Authorization ID:</b> {auth['authorization_id']}</div>\n<div class='row'><b>Name:</b> {auth['name']}</div>\n<div class='row'><b>Role/Path:</b> {auth['trainee_path']}</div>\n<div class='row'><b>Job Type:</b> {auth['job_type']}</div>\n<div class='row'><b>Authorized Scope:</b> {auth['scope']}</div>\n<div class='row'><b>Status:</b> {auth['status']}</div>\n<div class='row'><b>Issue Date:</b> {auth.get('decision_date', auth.get('issue_date',''))}</div>\n<div class='row'><b>Valid Until:</b> {auth['expiry_date']}</div>\n<div class='row'><b>Standards Basis:</b> {', '.join(STANDARDS)}</div>\n<div class='sig'>\n<div class='box'><b>Department Recommendation</b><br>{auth.get('principal_signature', '')}</div>\n<div class='box'><b>CRB Outcome</b><br>{auth.get('crb_decision', '')}</div>\n<div class='box'><b>Final Approving Authority</b><br>{auth.get('management_signature', '')}</div>\n</div>\n<div class='qr'><img src='{qr}' width='125'><br><small>Verify: {verification_url}</small></div>\n</div></body></html>\n"
    return (cert_id, html, qr)



def record_certificate_history(db_insert, uid, now, actor, certificate_id: str, authorization_id: str, user_id: str, from_status: str, to_status: str, event_type: str, reason: str=''):
    db_insert('authorization_certificate_history', {
        'history_id': uid('CHG'), 'certificate_id': certificate_id, 'authorization_id': authorization_id, 'user_id': user_id,
        'from_status': from_status, 'to_status': to_status, 'event_type': event_type, 'reason': reason,
        'actor_id': str((actor or {}).get('user_id','')), 'actor_name': str((actor or {}).get('name','')), 'event_on': now(), 'metadata': ''
    })
