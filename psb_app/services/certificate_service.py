"""Digital PSB certificate rendering based on controlled PSB templates.

The visual layout and wording follow PSB-PTQ20-F03 (Training Course Attestation)
and PSB-PTQ20-F02 (Authorization Certificate). Certificates are generated as
print-ready HTML, carry a verification QR, and are backed by immutable database
records. The left signature block is the PSB Chief Executive Officer; the right
signature block is the assigned Trainer.
"""
from __future__ import annotations

import base64
import html as _html
from pathlib import Path

from psb_app.legacy_runtime import (
    LOGO_PATH,
    STANDARDS,
    VERIFY_PUBLIC_URL,
    clean,
    make_qr_data_uri,
    pd,
    uid,
)

CEO_NAME_ATTESTATION = "Cdre Dr. M Saeed Khalid SI(M)"
CEO_NAME_AUTHORIZATION = "Cdre (R) Dr. M Saeed Khalid"
CEO_TITLE = "Chief Executive Officer"
ATTESTATION_DOCUMENT = "PSB-PTQ20-F03"
AUTHORIZATION_DOCUMENT = "PSB-PTQ20-F02"
INITIAL_ISSUE_DATE = "25-05-2022"
REVISION_NO = "01"
REVISION_DATE = "11-02-2026"


def _e(value) -> str:
    return _html.escape(clean(value), quote=True)


def _logo_data_uri() -> str:
    try:
        p = Path(LOGO_PATH)
        if p.exists():
            encoded = base64.b64encode(p.read_bytes()).decode("ascii")
            return f"data:image/png;base64,{encoded}"
    except Exception:
        pass
    return ""


def _template_css() -> str:
    return """
    @page { size: A4 portrait; margin: 0; }
    * { box-sizing: border-box; }
    body { margin: 0; background: #eef1f3; font-family: Arial, Helvetica, sans-serif; color:#111; }
    .sheet { position: relative; width: 210mm; min-height: 297mm; margin: 0 auto; overflow:hidden; background:#fff; padding: 18mm 18mm 24mm; }
    .watermark { position:absolute; inset:0; opacity:.14; z-index:0; overflow:hidden; font:700 12px/18px Arial; color:#667085; word-spacing:8px; letter-spacing:.5px; }
    .watermark span { display:block; transform: rotate(0deg); width:220mm; }
    .band-top-navy { position:absolute; top:0; right:0; width:58%; height:13mm; background:#020735; clip-path:polygon(18% 0,100% 0,100% 100%,38% 100%); z-index:1; }
    .band-top-green { position:absolute; top:0; left:0; width:55%; height:11mm; background:#005c23; clip-path:polygon(0 0,82% 0,100% 100%,0 100%); z-index:1; }
    .band-bottom-navy { position:absolute; left:0; bottom:16mm; width:69%; height:14mm; background:#020735; clip-path:polygon(0 0,82% 0,100% 100%,0 100%); z-index:1; }
    .band-bottom-green { position:absolute; right:0; bottom:16mm; width:42%; height:14mm; background:#005c23; clip-path:polygon(22% 0,100% 0,100% 100%,0 100%); z-index:1; }
    .footer-tag { position:absolute; bottom:4mm; left:50%; transform:translateX(-50%); background:#07123f; color:white; padding:2.4mm 7mm; font-weight:700; font-size:10pt; z-index:3; }
    .meta-left,.meta-right { position:absolute; top:18mm; z-index:3; font-size:9.5pt; line-height:1.35; }
    .meta-left { left:13mm; } .meta-right { right:13mm; text-align:left; }
    .content { position:relative; z-index:2; text-align:center; padding-top:35mm; }
    .logo { width:31mm; max-height:38mm; object-fit:contain; margin-bottom:5mm; }
    .org { color:#06396f; font-size:23pt; font-weight:800; letter-spacing:.5px; margin:0 0 4mm; }
    .title { font-family: Georgia, 'Times New Roman', serif; font-size:36pt; font-weight:700; line-height:1.05; margin:2mm 0 7mm; }
    .lead { font-size:12pt; margin:2mm auto; max-width:165mm; }
    .candidate { display:inline-block; font-size:18pt; font-weight:800; border-bottom:1.5px solid #222; padding:0 7mm 1.5mm; margin:5mm 0 4mm; min-width:115mm; }
    .qualification { font-size:18pt; font-weight:800; margin:4mm auto; max-width:165mm; }
    .module-list { width:168mm; margin:4mm auto 2mm; text-align:left; font-size:9.7pt; line-height:1.35; columns:2; column-gap:10mm; }
    .module-list div { break-inside:avoid; margin-bottom:1.2mm; }
    .signatures { position:absolute; z-index:3; left:16mm; right:16mm; bottom:34mm; display:grid; grid-template-columns:1fr 1fr; gap:35mm; text-align:left; }
    .signature { border-top:1px solid #222; padding-top:2mm; font-size:10pt; line-height:1.35; }
    .signature.right { text-align:left; }
    .signed { color:#0b6b35; font-size:8.5pt; font-weight:700; }
    .qr { position:absolute; z-index:3; right:15mm; bottom:3.5mm; display:flex; gap:2mm; align-items:center; font-size:7pt; color:#334155; }
    .qr img { width:15mm; height:15mm; }
    .serial { position:absolute; z-index:3; left:13mm; bottom:5mm; font-size:7.5pt; color:#475467; }
    @media print { body { background:white; } .sheet { margin:0; box-shadow:none; page-break-after:always; } }
    """


def _watermark_html() -> str:
    line = " ".join(["PSB"] * 22)
    return "<div class='watermark'>" + "".join(f"<span>{line}</span>" for _ in range(48)) + "</div>"


def _shell(meta_left: str, meta_right: str, inner: str, cert_id: str, verification_url: str, qr: str) -> str:
    return f"""<!doctype html><html><head><meta charset='utf-8'><title>Pakistan Shipping Bureau Certificate</title>
    <style>{_template_css()}</style></head><body><section class='sheet'>
    {_watermark_html()}<div class='band-top-green'></div><div class='band-top-navy'></div>
    <div class='band-bottom-navy'></div><div class='band-bottom-green'></div>
    <div class='meta-left'>{meta_left}</div><div class='meta-right'>{meta_right}</div>
    {inner}
    <div class='serial'>Digital Certificate ID: {_e(cert_id)}</div>
    <div class='qr'><img src='{qr}' alt='Verification QR'><span>Verify<br>{_e(verification_url)}</span></div>
    <div class='footer-tag'>PAKISTAN SHIPPING BUREAU</div>
    </section></body></html>"""


def build_training_attestation(cert: pd.Series | dict) -> tuple[str, str]:
    cert_id = clean(cert.get('certificate_id')) or uid('ATT')
    verification_url = clean(cert.get('verification_url')) or f'{VERIFY_PUBLIC_URL}/?verify={cert_id}'
    qr = make_qr_data_uri(verification_url)
    logo = _logo_data_uri()
    candidate = _e(cert.get('name'))
    module_code = _e(cert.get('module_code'))
    module_name = _e(cert.get('module_name') or cert.get('training_title'))
    conducted_on = _e(cert.get('conducted_on') or cert.get('completed_on') or cert.get('issue_date'))
    issued_on = _e(cert.get('issue_date'))
    trainer = _e(cert.get('trainer_name') or 'Assigned Trainer')
    ceo = _e(cert.get('ceo_name') or CEO_NAME_ATTESTATION)
    meta_left = f"Issued at: PSB Head Office<br>Issued on: {issued_on}"
    meta_right = f"Document: {ATTESTATION_DOCUMENT}<br>Initial Issue Date: {INITIAL_ISSUE_DATE}<br>Revision No: {REVISION_NO}<br>Revision Date: {REVISION_DATE}"
    inner = f"""<div class='content'>
      {f"<img class='logo' src='{logo}' alt='PSB Logo'>" if logo else ''}
      <div class='org'>PAKISTAN SHIPPING BUREAU</div>
      <div class='title'>Training Course<br>Attestation</div>
      <div class='lead'>This is to attest that,</div>
      <div class='candidate'>{candidate}</div>
      <div class='lead'>has successfully completed the Theoretical training of</div>
      <div class='qualification'>{module_code}{' – ' if module_code and module_name else ''}{module_name}</div>
      <div class='lead'>Conducted on: <b>{conducted_on}</b></div>
    </div>
    <div class='signatures'>
      <div class='signature'><div class='signed'>DIGITALLY SIGNED</div><b>{ceo}</b><br>{CEO_TITLE}</div>
      <div class='signature right'><div class='signed'>DIGITALLY SIGNED</div><b>{trainer}</b><br>Trainer</div>
    </div>"""
    return _shell(meta_left, meta_right, inner, cert_id, verification_url, qr), qr


def _module_items(auth) -> list[str]:
    raw = auth.get('completed_modules', [])
    if isinstance(raw, (list, tuple)):
        return [clean(x) for x in raw if clean(x)]
    text = clean(raw)
    if not text:
        return []
    return [x.strip(' •-\t') for x in text.replace(';', '\n').splitlines() if x.strip()]


def build_certificate(auth: pd.Series) -> tuple[str, str, str]:
    cert_id = clean(auth.get('certificate_id')) or uid('CERT')
    verification_url = f'{VERIFY_PUBLIC_URL}/?verify={cert_id}'
    qr = make_qr_data_uri(verification_url)
    logo = _logo_data_uri()
    candidate = _e(auth.get('name'))
    qualification = _e(auth.get('trainee_path') or auth.get('scope') or auth.get('job_type'))
    issue_date = _e(auth.get('decision_date') or auth.get('issue_date'))
    modules = _module_items(auth)
    trainer = _e(auth.get('trainer_name') or auth.get('tutor_signature') or 'Assigned Trainer')
    ceo = _e(auth.get('ceo_name') or CEO_NAME_AUTHORIZATION)
    module_html = ''.join(f"<div>• {_e(m)}</div>" for m in modules) or '<div>• Completed mandatory theoretical and practical modules as per PSB Training Plan.</div>'
    meta_left = f"Issued at: PSB Head Office<br>Issued on: {issue_date}"
    meta_right = f"Document: {AUTHORIZATION_DOCUMENT}<br>Initial Issue Date: {INITIAL_ISSUE_DATE}<br>Revision No: {REVISION_NO}<br>Revision Date: {REVISION_DATE}"
    inner = f"""<div class='content'>
      {f"<img class='logo' src='{logo}' alt='PSB Logo'>" if logo else ''}
      <div class='title'>Authorization<br>Certificate</div>
      <div class='lead'>This is to certify that</div>
      <div class='candidate'>{candidate}</div>
      <div class='lead'>has successfully completed the Theoretical &amp; Practical training of</div>
      <div class='qualification'>{qualification}</div>
      <div class='lead'>Authorization Date: <b>{issue_date}</b></div>
      <div class='lead' style='margin-top:4mm'>Completed Theoretical and Practical modules as per PSB Training Plan are listed below;</div>
      <div class='module-list'>{module_html}</div>
    </div>
    <div class='signatures'>
      <div class='signature'><div class='signed'>DIGITALLY SIGNED</div><b>{ceo}</b><br>{CEO_TITLE}</div>
      <div class='signature right'><div class='signed'>DIGITALLY SIGNED</div><b>{trainer}</b><br>Trainer</div>
    </div>"""
    html = _shell(meta_left, meta_right, inner, cert_id, verification_url, qr)
    return cert_id, html, qr


def record_certificate_history(db_insert, uid, now, actor, certificate_id: str, authorization_id: str, user_id: str, from_status: str, to_status: str, event_type: str, reason: str=''):
    db_insert('authorization_certificate_history', {
        'history_id': uid('CHG'), 'certificate_id': certificate_id, 'authorization_id': authorization_id, 'user_id': user_id,
        'from_status': from_status, 'to_status': to_status, 'event_type': event_type, 'reason': reason,
        'actor_id': str((actor or {}).get('user_id','')), 'actor_name': str((actor or {}).get('name','')), 'event_on': now(), 'metadata': ''
    })
