
from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import quote_plus
import base64
import hashlib
import io
import json
import os
import random
import re
import secrets
import string
import uuid

import pandas as pd
import qrcode
import streamlit as st
import streamlit.components.v1 as components
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

try:
    from supabase import create_client
except Exception:
    create_client = None

APP_TITLE = "Pakistan Shipping Bureau Classification Competency Platform"
APP_SUBTITLE = "Training, Supabase Records, File Storage, Authorization, Job Allocation and Audit Readiness"

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///psb_hrdm_local.db")
PUBLIC_URL = os.getenv("PUBLIC_URL", "https://training.psbureau.org")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "psb-hrdm-files")
LOCAL_UPLOAD_DIR = Path("local_uploads")
LOGO_PATH = Path("assets/psb-logo.png")

STANDARDS = ["IMO RO Code", "ISO 9001", "ISO/IEC 17020", "IACS PR7", "Competency-Based Qualification System"]
ROLES = ["Admin", "Management", "Trainer", "Tutor/Mentor", "Surveyor", "Plan Appraiser", "Quality Management Representative", "Rule Development Rep", "Job Coordinator", "Trainee", "On Probation"]
JOB_TYPES = ["New Building Survey", "In-Service Survey", "Plan Appraisal", "Statutory Survey", "Audit", "Witness Survey"]
SCOPE_LIBRARY = ["Hull NB", "Hull IS", "Machinery NB", "Machinery IS", "Electrical NB", "Electrical IS", "Statutory SOLAS", "Statutory MARPOL", "Plan Approval Hull", "Plan Approval Machinery", "Plan Approval Electrical", "Offshore/MODU", "ISM Audit", "ISPS Audit", "MLC Inspection"]
FILE_CATEGORIES = ["Training Slide", "Training Video", "Training PDF", "Training DOC", "Training PPT", "Certificate Template", "Issued Certificate", "Logbook Evidence", "Witness Evidence", "Rule Document", "QMS Evidence", "OCR Evidence", "Other"]
ALLOWED_EXTENSIONS = ["pdf", "ppt", "pptx", "txt", "doc", "docx", "png", "jpg", "jpeg", "mp4", "xlsx", "csv", "html"]

def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def today() -> str:
    return date.today().strftime("%Y-%m-%d")

def uid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"

def phash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def clean(v) -> str:
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except Exception:
        pass
    return str(v)

def temp_password(n: int = 10) -> str:
    return "".join(secrets.choice(string.ascii_letters + string.digits + "@#$") for _ in range(n))

def split_list(v: str) -> list[str]:
    return [x.strip() for x in re.split(r"[,;|]+", clean(v)) if x.strip()]

def join_list(v: list[str]) -> str:
    return ", ".join(v)

def days_until(date_text: str) -> int:
    if not clean(date_text):
        return 9999
    try:
        return (datetime.strptime(clean(date_text)[:10], "%Y-%m-%d").date() - date.today()).days
    except Exception:
        return 9999

def actor_get(actor: dict | None, key: str, default: str = "") -> str:
    return clean(actor.get(key, default)) if isinstance(actor, dict) else default

def logo_data_uri() -> str:
    if not LOGO_PATH.exists():
        return ""
    return "data:image/png;base64," + base64.b64encode(LOGO_PATH.read_bytes()).decode()

def make_qr_data_uri(text_value: str) -> str:
    img = qrcode.make(text_value)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

@st.cache_resource
def get_engine() -> Engine:
    url = DATABASE_URL
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return create_engine(url, pool_pre_ping=True)

@st.cache_resource
def get_supabase_client():
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY or create_client is None:
        return None
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def exec_sql(sql: str, params: dict | None = None) -> None:
    with get_engine().begin() as conn:
        conn.execute(text(sql), params or {})

def query_sql(sql: str, params: dict | None = None) -> pd.DataFrame:
    with get_engine().begin() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})

def db_all(table: str) -> pd.DataFrame:
    try:
        return query_sql(f"select * from {table}")
    except Exception:
        return pd.DataFrame()

def db_insert(table: str, row: dict) -> None:
    cols = list(row.keys())
    sql = f"insert into {table} ({', '.join(cols)}) values ({', '.join([f':{c}' for c in cols])})"
    exec_sql(sql, row)

def db_update(table: str, id_col: str, id_val: str, row: dict) -> None:
    if not row:
        return
    patch = dict(row)
    patch[id_col] = id_val
    sets = ", ".join([f"{k}=:{k}" for k in row.keys()])
    exec_sql(f"update {table} set {sets} where {id_col}=:{id_col}", patch)

def init_db() -> None:
    stmts = [
        """create table if not exists users (
            user_id text primary key, name text, role text, department text, assigned_duty text,
            email text unique, login_id text unique, password_hash text, temp_password text, status text,
            availability text, current_location text, created_on text, last_login text
        )""",
        """create table if not exists trainings (
            training_id text primary key, title text, category text, standards text, target_roles text,
            trainer_id text, trainer_name text, rule_refs text, slides_link text, video_link text,
            reference_link text, scorm_package_link text, lms_course_id text, schedule_date text,
            schedule_time text, meeting_link text, recording_link text, passing_marks integer,
            validity_months integer, max_attempts integer, retest_wait_days integer, status text,
            created_on text, updated_on text
        )""",
        """create table if not exists files (
            file_id text primary key, owner_user_id text, owner_name text, linked_table text, linked_id text,
            category text, file_name text, file_ext text, mime_type text, storage_provider text,
            storage_path text, public_url text, extracted_text text, ocr_status text, review_status text,
            created_on text, updated_on text
        )""",
        """create table if not exists training_records (
            record_id text primary key, user_id text, name text, role text, training_id text, training_title text,
            status text, slides_opened text, video_opened text, live_attendance text, recording_opened text,
            lms_completed text, test_status text, score real, passing_marks integer, certificate_status text,
            certificate_link text, due_date text, completed_on text, progress integer, remarks text, updated_on text
        )""",
        """create table if not exists question_bank (
            question_id text primary key, training_id text, question text, option_a text, option_b text,
            option_c text, option_d text, correct_answer text, marks integer, generated_on text
        )""",
        """create table if not exists assessment_history (
            assessment_id text primary key, user_id text, name text, training_id text, training_title text,
            attempt_no integer, score real, result text, attempted_on text, next_retest_allowed text, remarks text
        )""",
        """create table if not exists scorm_lms_records (
            lms_record_id text primary key, user_id text, name text, training_id text, training_title text,
            lms_course_id text, scorm_status text, scorm_score real, seat_time text, completion_date text,
            last_sync text, remarks text
        )""",
        """create table if not exists competency_matrix (
            competency_id text primary key, user_id text, name text, role text, area text, level text,
            scope text, job_type text, required_training_ids text, required_logbook_count integer,
            status text, expiry_date text, evidence text, created_on text, updated_on text
        )""",
        """create table if not exists authorization_requests (
            authorization_id text primary key, user_id text, name text, job_type text, scope text,
            competency_id text, status text, tutor_remarks text, tutor_signature text, tutor_signed_on text,
            technical_remarks text, qms_remarks text, qms_signature text, qms_signed_on text,
            management_remarks text, management_signature text, management_signed_on text, expiry_date text,
            certificate_id text, certificate_html text, certificate_storage_link text, qr_data_uri text,
            created_on text, updated_on text
        )""",
        """create table if not exists authorization_certificates (
            certificate_id text primary key, authorization_id text, user_id text, name text, scope text,
            job_type text, issue_date text, expiry_date text, certificate_html text, qr_data_uri text,
            storage_link text, verification_url text, status text, created_on text
        )""",
        """create table if not exists job_requests (
            job_id text primary key, job_title text, job_type text, required_scope text, vessel_name text,
            imo_number text, location text, planned_date text, priority text, status text, created_by text,
            assigned_user_id text, assigned_user_name text, assignment_reason text, created_on text, updated_on text
        )""",
        """create table if not exists supervised_logbook (
            logbook_id text primary key, user_id text, name text, role text, vessel_name text, imo_number text,
            survey_type text, survey_date text, location text, tutor_id text, tutor_name text, findings text,
            recommendation text, status text, created_on text, updated_on text
        )""",
        """create table if not exists witness_surveys (
            witness_id text primary key, user_id text, name text, tutor_id text, tutor_name text,
            vessel_name text, job_type text, scope text, witness_date text, location text, checklist_json text,
            rating integer, outcome text, remarks text, status text, created_on text, updated_on text
        )""",
        """create table if not exists rule_library (
            rule_id text primary key, title text, standard text, revision text, category text, link text,
            mandatory text, current_version_id text, created_on text, updated_on text
        )""",
        """create table if not exists document_versions (
            version_id text primary key, rule_id text, version_no text, revision_date text,
            change_summary text, file_link text, uploaded_by text, approved_by text, status text, created_on text
        )""",
        """create table if not exists scope_library (
            scope_id text primary key, scope_name text, job_type text, category text, description text,
            required_level text, default_validity_months integer, active text
        )""",
        """create table if not exists notifications (
            notification_id text primary key, user_id text, name text, email text, subject text, message text,
            type text, status text, created_on text, sent_on text
        )""",
        """create table if not exists capa_register (
            capa_id text primary key, source text, finding text, severity text, owner_id text, owner_name text,
            due_date text, status text, corrective_action text, created_on text, updated_on text
        )""",
        """create table if not exists audit_trail (
            audit_id text primary key, date_time text, actor_id text, actor_name text, actor_role text,
            action text, details text, result text
        )""",
    ]
    for s in stmts:
        exec_sql(s)
    if db_all("users").empty:
        seed_demo()

def audit(action: str, details: str = "", result: str = "Success", actor: dict | None = None) -> None:
    actor = actor or st.session_state.get("user", {})
    db_insert("audit_trail", {
        "audit_id": uid("AUD"), "date_time": now(), "actor_id": actor_get(actor, "user_id"),
        "actor_name": actor_get(actor, "name", "System"), "actor_role": actor_get(actor, "role", "System"),
        "action": action, "details": details, "result": result
    })

def seed_demo() -> None:
    demo_users = [
        ("USR-ADMIN", "PSB Admin", "Admin", "Support/Admin", "System Control", "admin@psbureau.org", "admin", "Admin@1234"),
        ("USR-MGMT", "Management User", "Management", "Management", "Oversight", "management@psbureau.org", "management", "Mgmt@1234"),
        ("USR-TRAINER", "Training Officer", "Trainer", "Training", "Training Delivery", "trainer@psbureau.org", "trainer", "Trainer@1234"),
        ("USR-TUTOR", "Senior Surveyor Tutor", "Tutor/Mentor", "Survey", "Supervised Survey Approval", "tutor@psbureau.org", "tutor", "Tutor@1234"),
        ("USR-SURVEYOR", "Sample Surveyor", "Surveyor", "Survey", "Electrical Survey", "surveyor@psbureau.org", "surveyor", "Surveyor@1234"),
        ("USR-APPRAISER", "Sample Plan Appraiser", "Plan Appraiser", "Plan Appraisal", "Electrical Plan Review", "appraiser@psbureau.org", "appraiser", "Appraiser@1234"),
        ("USR-QMR", "QMS Representative", "Quality Management Representative", "Quality Management System", "QMS Review", "qmr@psbureau.org", "qmr", "QMR@1234"),
        ("USR-RULE", "Rule Development Rep", "Rule Development Rep", "Rule Development", "Rule Update", "rule@psbureau.org", "rule", "Rule@1234"),
        ("USR-COORD", "Job Coordinator", "Job Coordinator", "Operations", "Job Allocation", "coordinator@psbureau.org", "coordinator", "Coord@1234"),
    ]
    for u in demo_users:
        db_insert("users", {
            "user_id": u[0], "name": u[1], "role": u[2], "department": u[3], "assigned_duty": u[4],
            "email": u[5], "login_id": u[6], "password_hash": phash(u[7]), "temp_password": u[7],
            "status": "Active", "availability": "Available", "current_location": "Karachi", "created_on": today(), "last_login": ""
        })
    for scope in SCOPE_LIBRARY:
        job_type = "New Building Survey" if "NB" in scope else "In-Service Survey" if "IS" in scope else "Plan Appraisal" if "Plan Approval" in scope else "Statutory Survey" if "Statutory" in scope else "Audit" if "Audit" in scope else "Witness Survey"
        db_insert("scope_library", {
            "scope_id": uid("SCOPE"), "scope_name": scope, "job_type": job_type, "category": scope.split()[0],
            "description": f"Authorization scope for {scope}", "required_level": "L1", "default_validity_months": 36, "active": "Yes"
        })
    seed_rules = [
        ("RULE-IMO-RO", "IMO Recognized Organization Code", "IMO RO Code", "Current", "Statutory", "https://www.imo.org"),
        ("RULE-ISO9001", "Quality Management System Requirements", "ISO 9001", "2015", "QMS", "https://www.iso.org"),
        ("RULE-ISO17020", "Inspection Body Competence Requirements", "ISO/IEC 17020", "2012", "Inspection", "https://www.iso.org"),
        ("RULE-IACS-PR7", "IACS Training and Qualification Principles", "IACS PR7", "Current", "Competency", "https://iacs.org.uk"),
    ]
    for r in seed_rules:
        db_insert("rule_library", {
            "rule_id": r[0], "title": r[1], "standard": r[2], "revision": r[3], "category": r[4],
            "link": r[5], "mandatory": "Yes", "current_version_id": "", "created_on": today(), "updated_on": today()
        })
    audit("Database Seeded", "Initial PSB demo data created", actor={"name": "System", "role": "System"})

def upload_file_to_storage(uploaded_file, actor: dict, category: str, linked_table: str, linked_id: str) -> dict:
    file_id = uid("FILE")
    ext = uploaded_file.name.split(".")[-1].lower() if "." in uploaded_file.name else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"File type .{ext} is not allowed.")
    storage_path = f"{category.replace(' ', '_').lower()}/{linked_table}/{linked_id}/{file_id}_{uploaded_file.name}"
    data = uploaded_file.getvalue()
    provider = "local"
    public_url = ""
    client = get_supabase_client()
    if client is not None:
        try:
            try:
                client.storage.create_bucket(SUPABASE_BUCKET, options={"public": True})
            except Exception:
                pass
            client.storage.from_(SUPABASE_BUCKET).upload(storage_path, data, {"content-type": uploaded_file.type or "application/octet-stream", "upsert": "true"})
            public_url = client.storage.from_(SUPABASE_BUCKET).get_public_url(storage_path)
            provider = "supabase"
        except Exception as e:
            provider = "local"
            public_url = ""
    if provider == "local":
        local_path = LOCAL_UPLOAD_DIR / storage_path
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(data)
        public_url = str(local_path)
    extracted = extract_text_basic(uploaded_file.name, data)
    row = {
        "file_id": file_id, "owner_user_id": actor_get(actor, "user_id"), "owner_name": actor_get(actor, "name"),
        "linked_table": linked_table, "linked_id": linked_id, "category": category, "file_name": uploaded_file.name,
        "file_ext": ext, "mime_type": uploaded_file.type or "", "storage_provider": provider, "storage_path": storage_path,
        "public_url": public_url, "extracted_text": extracted[:10000], "ocr_status": "Extracted" if extracted else "Pending/Not Supported",
        "review_status": "Pending Review", "created_on": now(), "updated_on": now()
    }
    db_insert("files", row)
    audit("File Uploaded", f"{uploaded_file.name} -> {category}", actor=actor)
    return row

def extract_text_basic(name: str, data: bytes) -> str:
    lower = name.lower()
    try:
        if lower.endswith(".txt") or lower.endswith(".csv"):
            return data.decode("utf-8", errors="ignore")
        if lower.endswith(".pdf"):
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(io.BytesIO(data))
                return "\n".join([p.extract_text() or "" for p in reader.pages])
            except Exception:
                return ""
        if lower.endswith(".docx"):
            try:
                import docx
                doc = docx.Document(io.BytesIO(data))
                return "\n".join([p.text for p in doc.paragraphs])
            except Exception:
                return ""
        if lower.endswith(".pptx"):
            try:
                from pptx import Presentation
                prs = Presentation(io.BytesIO(data))
                texts = []
                for slide in prs.slides:
                    for shape in slide.shapes:
                        if hasattr(shape, "text"):
                            texts.append(shape.text)
                return "\n".join(texts)
            except Exception:
                return ""
    except Exception:
        return ""
    return ""

def create_notification(user_id: str, subject: str, message: str, ntype: str) -> None:
    users = db_all("users")
    u = users[users["user_id"] == user_id]
    if u.empty:
        return
    row = u.iloc[0]
    db_insert("notifications", {
        "notification_id": uid("NOT"), "user_id": row["user_id"], "name": row["name"], "email": row["email"],
        "subject": subject, "message": message, "type": ntype, "status": "Generated", "created_on": now(), "sent_on": ""
    })

def make_certificate(auth_row: pd.Series) -> tuple[str, str, str]:
    cert_id = clean(auth_row.get("certificate_id")) or uid("CERT")
    verification_url = f"{PUBLIC_URL}/verify/{cert_id}"
    qr = make_qr_data_uri(verification_url)
    html = f"""
<!doctype html><html><head><meta charset='utf-8'><title>PSB Authorization Certificate</title>
<style>
body{{font-family:Arial,sans-serif;padding:40px;color:#0f172a}}
.cert{{border:5px solid #071225;padding:35px;border-radius:18px}}
h1{{color:#071225;text-align:center;margin-bottom:0}} h2{{text-align:center;color:#0b3b76;margin-top:6px}}
.row{{margin:12px 0;font-size:16px}} .sig{{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-top:45px}}
.box{{border-top:1px solid #0f172a;padding-top:8px;font-size:13px}} .qr{{text-align:center;margin-top:25px}}
</style></head><body><div class='cert'>
<h1>Pakistan Shipping Bureau</h1><h2>Authorization Certificate / Letter</h2>
<div class='row'><b>Certificate ID:</b> {cert_id}</div>
<div class='row'><b>Authorization ID:</b> {auth_row['authorization_id']}</div>
<div class='row'><b>Name:</b> {auth_row['name']}</div>
<div class='row'><b>Job Type:</b> {auth_row['job_type']}</div>
<div class='row'><b>Authorized Scope:</b> {auth_row['scope']}</div>
<div class='row'><b>Status:</b> {auth_row['status']}</div>
<div class='row'><b>Valid Until:</b> {auth_row['expiry_date']}</div>
<div class='row'><b>Standards Basis:</b> {", ".join(STANDARDS)}</div>
<div class='sig'><div class='box'><b>Tutor/Mentor</b><br>{auth_row.get('tutor_signature','')}</div>
<div class='box'><b>QMS Representative</b><br>{auth_row.get('qms_signature','')}</div>
<div class='box'><b>Management Authority</b><br>{auth_row.get('management_signature','')}</div></div>
<div class='qr'><img src='{qr}' width='125'><br><small>Verify: {verification_url}</small></div>
</div></body></html>"""
    return cert_id, html, qr

def update_progress() -> None:
    records = db_all("training_records")
    for _, r in records.iterrows():
        checks = [
            r["slides_opened"] == "Yes",
            r["video_opened"] == "Yes" or r["recording_opened"] == "Yes",
            r["live_attendance"] in ["Present", "Recording Viewed"],
            r["lms_completed"] == "Yes",
            r["test_status"] == "Passed",
            r["certificate_status"] == "Issued",
        ]
        p = int(sum(checks) / len(checks) * 100)
        patch = {"progress": p, "status": "Completed" if p == 100 else "Pending", "updated_on": now()}
        if p == 100 and not clean(r["completed_on"]):
            patch["completed_on"] = today()
        db_update("training_records", "record_id", r["record_id"], patch)

def evidence_status(comp_row: pd.Series) -> tuple[bool, str]:
    user_id = comp_row["user_id"]
    records = db_all("training_records")
    logs = db_all("supervised_logbook")
    witnesses = db_all("witness_surveys")
    passed_training = not records[(records["user_id"] == user_id) & (records["test_status"] == "Passed") & (records["certificate_status"] == "Issued")].empty if not records.empty else False
    approved_logs = len(logs[(logs["user_id"] == user_id) & (logs["status"] == "Tutor Approved")]) if not logs.empty else 0
    passed_witness = not witnesses[(witnesses["user_id"] == user_id) & (witnesses["outcome"] == "Satisfactory")].empty if not witnesses.empty else False
    req = int(comp_row["required_logbook_count"])
    ok = passed_training and approved_logs >= req and passed_witness
    return ok, f"Training Certificate: {'Yes' if passed_training else 'No'} | Approved Logbooks: {approved_logs}/{req} | Witness Survey: {'Yes' if passed_witness else 'No'}"

def authorized_users_for_job(job_type: str, scope: str) -> pd.DataFrame:
    auths = db_all("authorization_requests")
    users = db_all("users")
    if auths.empty or users.empty:
        return pd.DataFrame()
    approved = auths[(auths["status"] == "Management Approved") & (auths["job_type"] == job_type) & (auths["scope"] == scope)]
    rows = []
    for _, a in approved.iterrows():
        if days_until(a["expiry_date"]) < 0:
            continue
        u = users[users["user_id"] == a["user_id"]]
        if u.empty:
            continue
        user = u.iloc[0]
        if user["availability"] != "Available":
            continue
        rows.append({
            "user_id": user["user_id"], "name": user["name"], "role": user["role"], "location": user["current_location"],
            "availability": user["availability"], "authorization_id": a["authorization_id"], "certificate_id": a["certificate_id"], "expiry_date": a["expiry_date"]
        })
    return pd.DataFrame(rows)

def keywords(text_value: str) -> list[str]:
    stop = {"training","system","should","shall","which","there","their","about","through","during","after","before","within","using","based","these","those","where","under","requirements","procedure","document","classification","society","survey","surveyor","appraisal","management","development"}
    out = []
    for w in re.findall(r"\b[A-Za-z][A-Za-z\-]{4,}\b", text_value):
        x = w.lower()
        t = x.title()
        if x not in stop and t not in out:
            out.append(t)
    return out[:100]

def generate_mcqs(training_id: str, text_value: str, count: int) -> pd.DataFrame:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text_value.replace("\n", " ")) if 45 <= len(s.strip()) <= 260]
    keys = keywords(text_value)
    rows = []
    if len(keys) < 4:
        return pd.DataFrame()
    random.shuffle(sentences)
    for s in sentences:
        if len(rows) >= count:
            break
        ans = next((k for k in keys if re.search(rf"\b{re.escape(k)}\b", s, re.I)), None)
        if not ans:
            continue
        distractors = [k for k in keys if k.lower() != ans.lower()]
        if len(distractors) < 3:
            continue
        opts = random.sample(distractors, 3) + [ans]
        random.shuffle(opts)
        rows.append({"question_id": uid("Q"), "training_id": training_id, "question": re.sub(rf"\b{re.escape(ans)}\b", "__________", s, flags=re.I, count=1), "option_a": opts[0], "option_b": opts[1], "option_c": opts[2], "option_d": opts[3], "correct_answer": ans, "marks": 1, "generated_on": now()})
    return pd.DataFrame(rows)

def login_page() -> None:
    if "captcha_question" not in st.session_state:
        a, b = random.randint(2, 12), random.randint(2, 12)
        st.session_state["captcha_question"] = f"{a} + {b}"
        st.session_state["captcha_answer"] = str(a + b)
    st.markdown("<div class='login-wrap'>", unsafe_allow_html=True)
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=115)
    st.title("Pakistan Shipping Bureau")
    st.subheader("Classification Competency Platform")
    with st.form("login_form"):
        login = st.text_input("Login ID or Email")
        password = st.text_input("Password", type="password")
        cap = st.text_input(f"Security Verification: {st.session_state['captcha_question']} = ?")
        submit = st.form_submit_button("Login")
    if submit:
        if cap.strip() != st.session_state.get("captcha_answer", ""):
            st.error("Security verification failed.")
            st.stop()
        users = db_all("users")
        m = users[((users["login_id"].astype(str).str.lower() == login.lower().strip()) | (users["email"].astype(str).str.lower() == login.lower().strip())) & (users["password_hash"].astype(str) == phash(password.strip())) & (users["status"].astype(str) == "Active")]
        if m.empty:
            st.error("Invalid login.")
        else:
            user = m.iloc[0].to_dict()
            st.session_state["logged_in"] = True
            st.session_state["user"] = user
            db_update("users", "user_id", user["user_id"], {"last_login": now()})
            audit("User Login", f"{user['name']} logged in", actor=user)
            st.rerun()
    with st.expander("Default Demo Logins"):
        st.code("admin / Admin@1234\ntrainer / Trainer@1234\ntutor / Tutor@1234\nsurveyor / Surveyor@1234\nappraiser / Appraiser@1234\nqmr / QMR@1234\nrule / Rule@1234\ncoordinator / Coord@1234\nmanagement / Mgmt@1234")
    st.markdown("</div>", unsafe_allow_html=True)

def require_login() -> dict:
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "user" not in st.session_state:
        st.session_state["user"] = {}
    if not st.session_state["logged_in"]:
        login_page()
        st.stop()
    return st.session_state["user"]

def apply_style() -> None:
    st.markdown("""
    <style>
    .stApp { background:#eef3f8; }
    .block-container { padding-top:1rem; padding-bottom:2rem; }
    .psb-hero { background:linear-gradient(135deg,#071225,#0b3b76); color:white; padding:1.35rem 1.55rem; border-radius:26px; margin-bottom:1.1rem; box-shadow:0 20px 55px rgba(15,23,42,.18); display:flex; gap:18px; align-items:center; }
    .psb-hero img { width:88px; height:88px; border-radius:50%; object-fit:contain; background:white; padding:4px; }
    .psb-hero h1 { margin:0; font-size:2.05rem; letter-spacing:-.02em; }
    .psb-hero p { color:#dbeafe; margin:.35rem 0 0; }
    .pill { display:inline-flex; padding:5px 10px; border-radius:999px; background:#e8eef7; color:#0f172a; font-size:12px; font-weight:700; margin:4px 5px 4px 0; }
    .psb-hero .pill { background:rgba(255,255,255,.15); color:white; border:1px solid rgba(255,255,255,.2); }
    .step { border-left:4px solid #071225; background:#f8fafc; border-radius:14px; padding:.75rem .9rem; margin:.35rem 0; }
    .login-wrap { max-width:560px; margin:2rem auto; background:white; padding:2rem; border-radius:28px; box-shadow:0 24px 70px rgba(15,23,42,.16); text-align:center; }
    </style>
    """, unsafe_allow_html=True)

def header() -> None:
    logo = f"<img src='{logo_data_uri()}' />" if LOGO_PATH.exists() else ""
    st.markdown(f"""
    <div class='psb-hero'>{logo}<div>
    <h1>{APP_TITLE}</h1><p>{APP_SUBTITLE}</p>
    <div>{"".join([f"<span class='pill'>{s}</span>" for s in STANDARDS])}</div>
    </div></div>
    """, unsafe_allow_html=True)

def table(df: pd.DataFrame) -> None:
    st.dataframe(df.fillna(""), width="stretch", hide_index=True)

def metrics(items):
    cols = st.columns(4)
    for i, (label, value) in enumerate(items):
        cols[i % 4].metric(label, value)

def sidebar(actor: dict) -> str:
    if LOGO_PATH.exists():
        st.sidebar.image(str(LOGO_PATH), width=95)
    st.sidebar.success(f"{actor_get(actor,'name')} ({actor_get(actor,'role')})")
    st.sidebar.caption(actor_get(actor, "email"))
    st.sidebar.divider()
    role = actor_get(actor, "role")
    if role == "Admin":
        pages = ["Dashboard", "Admin", "Training", "Files", "Competency", "Authorization", "Job Allocation", "Logbook", "Witness Mobile", "Rule Library", "QMS", "SCORM/LMS", "AI Gap Analysis", "Backup", "Public QR Verify", "Management"]
    elif role == "Trainer":
        pages = ["Dashboard", "Training", "Files", "Logbook", "Witness Mobile", "SCORM/LMS"]
    elif role == "Tutor/Mentor":
        pages = ["Dashboard", "Files", "Logbook", "Witness Mobile", "Authorization"]
    elif role == "Quality Management Representative":
        pages = ["Dashboard", "Files", "QMS", "Authorization", "Rule Library", "Backup"]
    elif role == "Management":
        pages = ["Dashboard", "Management", "Authorization", "Job Allocation", "Backup"]
    elif role == "Job Coordinator":
        pages = ["Dashboard", "Job Allocation", "Management"]
    elif role == "Rule Development Rep":
        pages = ["Dashboard", "Training", "Files", "Rule Library", "Logbook"]
    else:
        pages = ["Dashboard", "Training", "Files", "Logbook", "Witness Mobile", "Authorization"]
    page = st.sidebar.radio("Menu", pages)
    if st.sidebar.button("Logout"):
        audit("User Logout", f"{actor_get(actor,'name')} logged out", actor=actor)
        st.session_state["logged_in"] = False
        st.session_state["user"] = {}
        st.rerun()
    return page

def dashboard_page(actor):
    st.header(f"{actor_get(actor,'role')} Dashboard")
    users, trainings, records, comp, auths, jobs, files = [db_all(t) for t in ["users","trainings","training_records","competency_matrix","authorization_requests","job_requests","files"]]
    expiring = sum(1 for _, r in comp.iterrows() if 0 <= days_until(r["expiry_date"]) <= 90) if not comp.empty else 0
    metrics([("Users", len(users)), ("Trainings", len(trainings)), ("Files", len(files)), ("Training Records", len(records)), ("Competencies", len(comp)), ("Authorizations", len(auths[auths["status"]=="Management Approved"]) if not auths.empty else 0), ("Jobs Assigned", len(jobs[jobs["status"]=="Assigned"]) if not jobs.empty else 0), ("Expiring 90 Days", expiring)])
    st.subheader("International Classification Society Workflow")
    for i, s in enumerate(["Upload controlled training files", "Training and LMS/SCORM", "MCQ assessment", "Logbook and witness survey", "Competency matrix", "Evidence-based authorization", "QR certificate storage", "Authorized and available job allocation"], 1):
        st.markdown(f"<div class='step'><b>{i}.</b> {s}</div>", unsafe_allow_html=True)

def admin_page(actor):
    st.header("Admin")
    with st.form("user"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Name")
        email = c2.text_input("Email")
        role = c1.selectbox("Role", ROLES)
        dept = c2.text_input("Department", "Survey")
        duty = c1.text_input("Duty")
        loc = c2.text_input("Location", "Karachi")
        pw = st.text_input("Password blank=auto", type="password")
        submit = st.form_submit_button("Create User")
    if submit and name and email:
        login = re.sub(r"[^a-z0-9]", "", name.lower().replace(" ", ".")) or f"user{random.randint(100,999)}"
        password = pw or temp_password()
        db_insert("users", {"user_id": uid("USR"), "name": name, "role": role, "department": dept, "assigned_duty": duty, "email": email, "login_id": login, "password_hash": phash(password), "temp_password": password, "status": "Active", "availability": "Available", "current_location": loc, "created_on": today(), "last_login": ""})
        st.success("User created.")
        st.code(f"{login} / {password}")
    st.subheader("Availability")
    users = db_all("users")
    if not users.empty:
        person = st.selectbox("User", users["name"].astype(str)+" — "+users["user_id"].astype(str))
        uidv = person.split(" — ")[-1]
        availability = st.selectbox("Availability", ["Available", "Busy", "On Leave", "Unavailable"])
        loc = st.text_input("Current Location", users[users["user_id"]==uidv].iloc[0]["current_location"])
        if st.button("Update Availability"):
            db_update("users", "user_id", uidv, {"availability": availability, "current_location": loc})
            st.success("Updated.")
    table(db_all("users").drop(columns=["password_hash"], errors="ignore"))

def file_upload_panel(actor, linked_table="general", linked_id="general", default_category="Other"):
    category = st.selectbox("File Category", FILE_CATEGORIES, index=FILE_CATEGORIES.index(default_category) if default_category in FILE_CATEGORIES else 0)
    files = st.file_uploader("Upload PDF, PPT/PPTX, TXT, DOC/DOCX, image, video, Excel", type=ALLOWED_EXTENSIONS, accept_multiple_files=True)
    if st.button("Upload Selected Files"):
        if not files:
            st.error("Select files first.")
        else:
            uploaded = 0
            for f in files:
                try:
                    upload_file_to_storage(f, actor, category, linked_table, linked_id)
                    uploaded += 1
                except Exception as e:
                    st.error(f"{f.name}: {e}")
            st.success(f"{uploaded} file(s) uploaded.")

def files_page(actor):
    st.header("Supabase File Storage / Records")
    linked_table = st.text_input("Linked Table", "general")
    linked_id = st.text_input("Linked ID", "general")
    file_upload_panel(actor, linked_table, linked_id)
    table(db_all("files"))

def training_page(actor):
    st.header("Training")
    role = actor_get(actor, "role")
    users = db_all("users")
    trainings = db_all("trainings")
    if role in ["Admin", "Trainer"]:
        with st.expander("Create Training"):
            trainers = users[(users["role"] == "Trainer") & (users["status"] == "Active")]
            with st.form("training"):
                title = st.text_input("Title")
                category = st.selectbox("Category", ["New Building", "In-Service", "Plan Appraisal", "Statutory", "QMS"])
                target = st.multiselect("Target Roles", [r for r in ROLES if r not in ["Admin","Management","Trainer"]], default=["Surveyor"])
                trainer = st.selectbox("Trainer", trainers["name"].astype(str)+" — "+trainers["user_id"].astype(str)) if not trainers.empty else ""
                lms = st.text_input("LMS/SCORM Course ID")
                passing = st.number_input("Passing Marks", 1, 100, 75)
                submit = st.form_submit_button("Create")
            if submit and title and trainer:
                tname, tid_user = trainer.split(" — ")
                tid = uid("TRN")
                db_insert("trainings", {"training_id": tid, "title": title, "category": category, "standards": join_list(STANDARDS), "target_roles": join_list(target), "trainer_id": tid_user, "trainer_name": tname, "rule_refs": "", "slides_link": "", "video_link": "", "reference_link": "", "scorm_package_link": "", "lms_course_id": lms, "schedule_date": "", "schedule_time": "10:00", "meeting_link": "", "recording_link": "", "passing_marks": passing, "validity_months": 36, "max_attempts": 3, "retest_wait_days": 7, "status": "Draft", "created_on": now(), "updated_on": now()})
                st.success("Training created.")
    trainings = db_all("trainings")
    if trainings.empty:
        return
    if role == "Trainer":
        trainings = trainings[trainings["trainer_id"] == actor_get(actor, "user_id")]
    elif role not in ["Admin", "Trainer"]:
        rec = db_all("training_records")
        ids = rec[rec["user_id"] == actor_get(actor, "user_id")]["training_id"].tolist() if not rec.empty else []
        trainings = trainings[trainings["training_id"].isin(ids)]
    if trainings.empty:
        st.warning("No assigned training.")
        return
    selected = st.selectbox("Select Training", trainings["title"].astype(str)+" — "+trainings["training_id"].astype(str))
    tid = selected.split(" — ")[-1]
    tr = db_all("trainings")
    tr_row = tr[tr["training_id"] == tid].iloc[0]
    if role in ["Admin", "Trainer"]:
        tabs = st.tabs(["Files", "Schedule", "MCQ", "Assign", "Records"])
        with tabs[0]:
            st.info("Upload slides, videos, PDFs, DOC/DOCX, PPT/PPTX, SCORM package or training documents. Files are stored in Supabase Storage when configured.")
            file_upload_panel(actor, "trainings", tid, "Training PDF")
            table(db_all("files")[db_all("files")["linked_id"] == tid] if not db_all("files").empty else pd.DataFrame())
        with tabs[1]:
            slides = st.text_input("Slides Link", tr_row["slides_link"])
            video = st.text_input("Video Link", tr_row["video_link"])
            ref = st.text_input("Reference Link", tr_row["reference_link"])
            scorm_link = st.text_input("SCORM Package Link", tr_row["scorm_package_link"])
            sdate = st.date_input("Schedule Date")
            stime = st.text_input("Schedule Time", tr_row["schedule_time"])
            st.link_button("Open MS Teams to Create Meeting", f"https://teams.microsoft.com/l/meeting/new?subject={quote_plus(clean(tr_row['title']))}")
            meeting = st.text_input("Final Meeting Link", tr_row["meeting_link"])
            recording = st.text_input("Recording Link", tr_row["recording_link"])
            if st.button("Save Training Links"):
                db_update("trainings", "training_id", tid, {"slides_link": slides, "video_link": video, "reference_link": ref, "scorm_package_link": scorm_link, "schedule_date": str(sdate), "schedule_time": stime, "meeting_link": meeting, "recording_link": recording, "status": "Scheduled", "updated_on": now()})
                st.success("Saved.")
        with tabs[2]:
            content = st.text_area("Paste or use extracted file text for MCQs", height=200)
            if st.button("Use Extracted Text from Uploaded Files"):
                fs = db_all("files")
                content = "\n".join(fs[(fs["linked_id"] == tid) & (fs["extracted_text"] != "")]["extracted_text"].astype(str).tolist())
                st.session_state["mcq_content"] = content
            content = st.text_area("MCQ Content", value=st.session_state.get("mcq_content", content) or "", height=200)
            count = st.slider("MCQs", 5, 30, 10)
            if st.button("Generate MCQs"):
                qs = generate_mcqs(tid, content, count)
                if qs.empty:
                    st.error("Could not generate MCQs.")
                else:
                    exec_sql("delete from question_bank where training_id=:tid", {"tid": tid})
                    for _, q in qs.iterrows():
                        db_insert("question_bank", q.to_dict())
                    st.success(f"{len(qs)} MCQs generated.")
            q = db_all("question_bank")
            table(q[q["training_id"] == tid] if not q.empty else q)
        with tabs[3]:
            eligible = users[(users["role"].isin(split_list(tr_row["target_roles"]))) & (users["status"] == "Active")]
            selected_users = st.multiselect("Assign Users", eligible["name"].astype(str)+" — "+eligible["user_id"].astype(str))
            due = st.date_input("Due", date.today()+pd.Timedelta(days=30))
            if st.button("Assign"):
                rec = db_all("training_records")
                added = 0
                for item in selected_users:
                    name, user_id = item.split(" — ")
                    if not rec.empty and not rec[(rec["user_id"] == user_id) & (rec["training_id"] == tid)].empty:
                        continue
                    u = users[users["user_id"] == user_id].iloc[0]
                    db_insert("training_records", {"record_id": uid("REC"), "user_id": user_id, "name": name, "role": u["role"], "training_id": tid, "training_title": tr_row["title"], "status": "Pending", "slides_opened": "No", "video_opened": "No", "live_attendance": "Not Marked", "recording_opened": "No", "lms_completed": "No", "test_status": "Not Attempted", "score": None, "passing_marks": tr_row["passing_marks"], "certificate_status": "Not Issued", "certificate_link": "", "due_date": str(due), "completed_on": "", "progress": 0, "remarks": "Assigned", "updated_on": now()})
                    create_notification(user_id, f"Training Assigned: {tr_row['title']}", f"Training due on {due}", "Training")
                    added += 1
                st.success(f"{added} assigned.")
        with tabs[4]:
            rec = db_all("training_records")
            table(rec[rec["training_id"] == tid] if not rec.empty else rec)
    else:
        trainee_training(actor, tid)

def trainee_training(actor, tid):
    rec = db_all("training_records")
    qbank = db_all("question_bank")
    tr = db_all("trainings")
    user_id = actor_get(actor, "user_id")
    rr = rec[(rec["user_id"] == user_id) & (rec["training_id"] == tid)]
    if rr.empty:
        return
    row = rr.iloc[0]
    tr_row = tr[tr["training_id"] == tid].iloc[0]
    metrics([("Progress", f"{row['progress']}%"), ("LMS", row["lms_completed"]), ("Score", clean(row["score"]) or "0"), ("Certificate", row["certificate_status"])])
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("Slides Complete"):
        db_update("training_records", "record_id", row["record_id"], {"slides_opened": "Yes"}); update_progress(); st.rerun()
    if c2.button("Video Complete"):
        db_update("training_records", "record_id", row["record_id"], {"video_opened": "Yes"}); update_progress(); st.rerun()
    if c3.button("Recording Complete"):
        db_update("training_records", "record_id", row["record_id"], {"recording_opened": "Yes", "video_opened": "Yes", "live_attendance": "Recording Viewed"}); update_progress(); st.rerun()
    if c4.button("LMS Complete"):
        db_update("training_records", "record_id", row["record_id"], {"lms_completed": "Yes"}); update_progress(); st.rerun()
    qs = qbank[qbank["training_id"] == tid] if not qbank.empty else pd.DataFrame()
    if qs.empty:
        st.warning("MCQs not generated.")
        return
    if row["test_status"] == "Passed":
        st.success("Test already passed.")
        return
    with st.form("test"):
        answers = {}
        for i, (_, q) in enumerate(qs.iterrows(), 1):
            st.markdown(f"**Q{i}. {q['question']}**")
            opts = [q["option_a"], q["option_b"], q["option_c"], q["option_d"]]
            answers[q["question_id"]] = st.radio("Select", opts, key=q["question_id"], label_visibility="collapsed")
        submit = st.form_submit_button("Submit Test")
    if submit:
        correct = sum(1 for _, q in qs.iterrows() if answers.get(q["question_id"]) == q["correct_answer"])
        score = round(correct / len(qs) * 100, 2)
        passed = score >= int(tr_row["passing_marks"])
        result = "Passed" if passed else "Failed"
        db_insert("assessment_history", {"assessment_id": uid("ASM"), "user_id": user_id, "name": actor_get(actor,"name"), "training_id": tid, "training_title": tr_row["title"], "attempt_no": 1, "score": score, "result": result, "attempted_on": now(), "next_retest_allowed": str(date.today()+pd.Timedelta(days=7)) if not passed else "", "remarks": f"Correct {correct}/{len(qs)}"})
        db_update("training_records", "record_id", row["record_id"], {"score": score, "test_status": result, "certificate_status": "Issued" if passed else "Not Issued", "certificate_link": f"{PUBLIC_URL}/training-certificates/{user_id}/{tid}" if passed else "", "remarks": f"Correct {correct}/{len(qs)}"})
        update_progress()
        st.success(f"{result}: {score}%")
        st.rerun()

def competency_page(actor):
    st.header("Competency Matrix")
    users = db_all("users")
    scopes = db_all("scope_library")
    if actor_get(actor, "role") in ["Admin", "Quality Management Representative", "Management"]:
        with st.form("comp"):
            eligible = users[~users["role"].isin(["Admin","Management","Trainer"])]
            person = st.selectbox("Person", eligible["name"].astype(str)+" — "+eligible["user_id"].astype(str))
            scope = st.selectbox("Scope", scopes["scope_name"].tolist() if not scopes.empty else SCOPE_LIBRARY)
            job_type = st.selectbox("Job Type", JOB_TYPES)
            level = st.selectbox("Level", ["L1", "L2", "L3", "L4"])
            req_logs = st.number_input("Required Approved Logbooks", 1, 30, 3)
            expiry = st.date_input("Expiry", date.today()+pd.Timedelta(days=365*3))
            submit = st.form_submit_button("Add Competency")
        if submit:
            name, user_id = person.split(" — ")
            u = users[users["user_id"] == user_id].iloc[0]
            db_insert("competency_matrix", {"competency_id": uid("COMP"), "user_id": user_id, "name": name, "role": u["role"], "area": scope, "level": level, "scope": scope, "job_type": job_type, "required_training_ids": "", "required_logbook_count": req_logs, "status": "Pending", "expiry_date": str(expiry), "evidence": "", "created_on": now(), "updated_on": now()})
            st.success("Added.")
    comp = db_all("competency_matrix")
    if actor_get(actor, "role") not in ["Admin", "Management", "Quality Management Representative"]:
        comp = comp[comp["user_id"] == actor_get(actor, "user_id")]
    table(comp)
    st.subheader("Scope Library")
    table(scopes)

def logbook_page(actor):
    st.header("Supervised Logbook")
    users = db_all("users")
    can_approve = actor_get(actor, "role") in ["Admin", "Tutor/Mentor"]
    with st.form("logbook"):
        if can_approve:
            eligible = users[~users["role"].isin(["Admin","Management","Trainer"])]
            person = st.selectbox("Person", eligible["name"].astype(str)+" — "+eligible["user_id"].astype(str))
        else:
            person = f"{actor_get(actor,'name')} — {actor_get(actor,'user_id')}"
            st.text_input("Person", actor_get(actor, "name"), disabled=True)
        vessel = st.text_input("Vessel")
        imo = st.text_input("IMO")
        survey_type = st.selectbox("Survey Type", SCOPE_LIBRARY)
        location = st.text_input("Location")
        tutors = users[users["role"] == "Tutor/Mentor"]
        tutor = st.selectbox("Tutor", tutors["name"].astype(str)+" — "+tutors["user_id"].astype(str)) if not tutors.empty else ""
        findings = st.text_area("Findings")
        submit = st.form_submit_button("Submit")
    if submit and vessel and tutor:
        name, user_id = person.split(" — ")
        tutor_name, tutor_id = tutor.split(" — ")
        u = users[users["user_id"] == user_id].iloc[0]
        lid = uid("LOGBOOK")
        db_insert("supervised_logbook", {"logbook_id": lid, "user_id": user_id, "name": name, "role": u["role"], "vessel_name": vessel, "imo_number": imo, "survey_type": survey_type, "survey_date": today(), "location": location, "tutor_id": tutor_id, "tutor_name": tutor_name, "findings": findings, "recommendation": "", "status": "Submitted", "created_on": now(), "updated_on": now()})
        st.success("Submitted.")
    logs = db_all("supervised_logbook")
    table(logs if can_approve else logs[logs["user_id"] == actor_get(actor, "user_id")] if not logs.empty else logs)
    if can_approve and not logs.empty:
        pending = logs[logs["status"] == "Submitted"]
        if not pending.empty:
            sel = st.selectbox("Pending", pending["name"].astype(str)+" — "+pending["logbook_id"].astype(str))
            lid = sel.split(" — ")[-1]
            remarks = st.text_area("Recommendation")
            if st.button("Approve"):
                db_update("supervised_logbook", "logbook_id", lid, {"status": "Tutor Approved", "recommendation": remarks or "Approved", "updated_on": now()})
                st.rerun()

def witness_page(actor):
    st.header("Witness Survey Mobile Form")
    users = db_all("users")
    is_tutor = actor_get(actor, "role") in ["Admin", "Tutor/Mentor", "Trainer"]
    with st.form("witness"):
        if is_tutor:
            eligible = users[~users["role"].isin(["Admin","Management","Trainer"])]
            person = st.selectbox("Person", eligible["name"].astype(str)+" — "+eligible["user_id"].astype(str))
        else:
            person = f"{actor_get(actor,'name')} — {actor_get(actor,'user_id')}"
        vessel = st.text_input("Vessel / Project")
        job_type = st.selectbox("Job Type", JOB_TYPES)
        scope = st.selectbox("Scope", SCOPE_LIBRARY)
        location = st.text_input("Location")
        rating = st.slider("Rating", 1, 5, 3)
        checklist = {x: st.checkbox(x) for x in ["Rules prepared", "Safety risks identified", "Technical checks correct", "Findings recorded", "Client communication professional"]}
        outcome = st.selectbox("Outcome", ["Satisfactory", "Needs Improvement", "Unsatisfactory"])
        remarks = st.text_area("Remarks")
        submit = st.form_submit_button("Submit Witness Survey")
    if submit:
        name, user_id = person.split(" — ")
        db_insert("witness_surveys", {"witness_id": uid("WIT"), "user_id": user_id, "name": name, "tutor_id": actor_get(actor, "user_id"), "tutor_name": actor_get(actor, "name"), "vessel_name": vessel, "job_type": job_type, "scope": scope, "witness_date": today(), "location": location, "checklist_json": json.dumps(checklist), "rating": rating, "outcome": outcome, "remarks": remarks, "status": "Submitted", "created_on": now(), "updated_on": now()})
        st.success("Witness survey recorded.")
    table(db_all("witness_surveys"))

def authorization_page(actor):
    st.header("Authorization and Certificate Storage")
    comp = db_all("competency_matrix")
    if comp.empty:
        st.warning("No competencies.")
        return
    if actor_get(actor, "role") in ["Admin", "Surveyor", "Plan Appraiser", "Rule Development Rep", "Trainee", "On Probation"]:
        eligible = comp if actor_get(actor, "role") == "Admin" else comp[comp["user_id"] == actor_get(actor, "user_id")]
        if not eligible.empty:
            sel = st.selectbox("Competency", eligible["name"].astype(str)+" — "+eligible["scope"].astype(str)+" — "+eligible["competency_id"].astype(str))
            cid = sel.split(" — ")[-1]
            c = comp[comp["competency_id"] == cid].iloc[0]
            ok, msg = evidence_status(c)
            st.info(msg)
            if st.button("Create Authorization Request"):
                if not ok:
                    st.error("Evidence incomplete.")
                else:
                    db_insert("authorization_requests", {"authorization_id": uid("AUTH"), "user_id": c["user_id"], "name": c["name"], "job_type": c["job_type"], "scope": c["scope"], "competency_id": cid, "status": "Draft", "tutor_remarks": "", "tutor_signature": "", "tutor_signed_on": "", "technical_remarks": "", "qms_remarks": "", "qms_signature": "", "qms_signed_on": "", "management_remarks": "", "management_signature": "", "management_signed_on": "", "expiry_date": c["expiry_date"], "certificate_id": "", "certificate_html": "", "certificate_storage_link": "", "qr_data_uri": "", "created_on": now(), "updated_on": now()})
                    st.success("Request created.")
    auths = db_all("authorization_requests")
    table(auths)
    if auths.empty:
        return
    sel = st.selectbox("Select Request", auths["name"].astype(str)+" — "+auths["scope"].astype(str)+" — "+auths["authorization_id"].astype(str))
    aid = sel.split(" — ")[-1]
    req = auths[auths["authorization_id"] == aid].iloc[0]
    role = actor_get(actor, "role")
    current = req["status"]
    next_status = None; sig_field = None; signed_field = None; remarks_field = None
    if role == "Tutor/Mentor" and current == "Draft":
        next_status, sig_field, signed_field, remarks_field = "Tutor Recommended", "tutor_signature", "tutor_signed_on", "tutor_remarks"
    elif role == "Trainer" and current == "Tutor Recommended":
        next_status, remarks_field = "Technical Reviewed", "technical_remarks"
    elif role == "Quality Management Representative" and current == "Technical Reviewed":
        next_status, sig_field, signed_field, remarks_field = "QMS Reviewed", "qms_signature", "qms_signed_on", "qms_remarks"
    elif role == "Management" and current == "QMS Reviewed":
        next_status, sig_field, signed_field, remarks_field = "Management Approved", "management_signature", "management_signed_on", "management_remarks"
    elif role == "Admin":
        seq = ["Draft","Tutor Recommended","Technical Reviewed","QMS Reviewed","Management Approved"]
        if current in seq and current != "Management Approved":
            next_status = seq[seq.index(current)+1]
    remarks = st.text_area("Remarks")
    signature = st.text_input("Digital Signature", actor_get(actor, "name"))
    if st.button("Approve Next Step"):
        if not next_status:
            st.error("Role cannot approve current stage.")
        else:
            patch = {"status": next_status, "updated_on": now()}
            if remarks_field: patch[remarks_field] = remarks
            if sig_field: patch[sig_field] = signature
            if signed_field: patch[signed_field] = now()
            if next_status == "Management Approved":
                tmp = req.copy()
                for k, v in patch.items(): tmp[k] = v
                cert_id, html, qr = make_certificate(tmp)
                patch.update({"certificate_id": cert_id, "certificate_html": html, "certificate_storage_link": f"database://authorization_certificates/{cert_id}", "qr_data_uri": qr})
                db_insert("authorization_certificates", {"certificate_id": cert_id, "authorization_id": aid, "user_id": req["user_id"], "name": req["name"], "scope": req["scope"], "job_type": req["job_type"], "issue_date": today(), "expiry_date": req["expiry_date"], "certificate_html": html, "qr_data_uri": qr, "storage_link": f"database://authorization_certificates/{cert_id}", "verification_url": f"{PUBLIC_URL}/verify/{cert_id}", "status": "Valid", "created_on": now()})
                db_update("competency_matrix", "competency_id", req["competency_id"], {"status": "Competent", "updated_on": now()})
            db_update("authorization_requests", "authorization_id", aid, patch)
            st.success(f"Moved to {next_status}")
            st.rerun()
    req = db_all("authorization_requests")
    req = req[req["authorization_id"] == aid].iloc[0]
    if clean(req["certificate_html"]):
        components.html(req["certificate_html"], height=650, scrolling=True)
        st.download_button("Download Certificate HTML", req["certificate_html"], file_name=f"{req['certificate_id']}.html", mime="text/html")

def job_allocation_page(actor):
    st.header("Authorization-Based Job Allocation")
    with st.form("job"):
        title = st.text_input("Job Title")
        job_type = st.selectbox("Job Type", JOB_TYPES)
        scope = st.selectbox("Required Scope", SCOPE_LIBRARY)
        vessel = st.text_input("Vessel / Project")
        imo = st.text_input("IMO")
        location = st.text_input("Location")
        planned = st.date_input("Planned Date")
        priority = st.selectbox("Priority", ["Low", "Normal", "High", "Urgent"])
        submit = st.form_submit_button("Create Job")
    if submit and title:
        db_insert("job_requests", {"job_id": uid("JOB"), "job_title": title, "job_type": job_type, "required_scope": scope, "vessel_name": vessel, "imo_number": imo, "location": location, "planned_date": str(planned), "priority": priority, "status": "Open", "created_by": actor_get(actor, "name"), "assigned_user_id": "", "assigned_user_name": "", "assignment_reason": "", "created_on": now(), "updated_on": now()})
        st.success("Job created.")
    jobs = db_all("job_requests")
    table(jobs)
    open_jobs = jobs[jobs["status"].isin(["Open", "Reassign"])] if not jobs.empty else pd.DataFrame()
    if not open_jobs.empty:
        sel = st.selectbox("Select Job", open_jobs["job_title"].astype(str)+" — "+open_jobs["job_id"].astype(str))
        jid = sel.split(" — ")[-1]
        job = jobs[jobs["job_id"] == jid].iloc[0]
        candidates = authorized_users_for_job(job["job_type"], job["required_scope"])
        st.subheader("Eligible Authorized and Available Persons")
        table(candidates)
        if not candidates.empty:
            person = st.selectbox("Assign To", candidates["name"].astype(str)+" — "+candidates["user_id"].astype(str))
            pid = person.split(" — ")[-1]
            cand = candidates[candidates["user_id"] == pid].iloc[0]
            reason = f"Authorized for {job['job_type']} / {job['required_scope']}; certificate {cand['certificate_id']}; available at {cand['location']}"
            st.info(reason)
            if st.button("Assign Job"):
                db_update("job_requests", "job_id", jid, {"status": "Assigned", "assigned_user_id": pid, "assigned_user_name": cand["name"], "assignment_reason": reason, "updated_on": now()})
                db_update("users", "user_id", pid, {"availability": "Busy"})
                st.success("Assigned.")
        else:
            st.error("No available authorized person found.")

def rule_library_page(actor):
    st.header("Rule Library and Document Versions")
    if actor_get(actor, "role") in ["Admin", "Quality Management Representative", "Rule Development Rep"]:
        with st.form("rule"):
            title = st.text_input("Title")
            standard = st.selectbox("Standard", STANDARDS)
            revision = st.text_input("Revision")
            category = st.text_input("Category")
            link = st.text_input("Link")
            submit = st.form_submit_button("Add Rule")
        if submit and title:
            rid = uid("RULE")
            db_insert("rule_library", {"rule_id": rid, "title": title, "standard": standard, "revision": revision, "category": category, "link": link, "mandatory": "Yes", "current_version_id": "", "created_on": today(), "updated_on": today()})
            st.success("Added.")
    rules = db_all("rule_library")
    table(rules)
    if not rules.empty and actor_get(actor, "role") in ["Admin", "Quality Management Representative", "Rule Development Rep"]:
        st.subheader("Upload Rule Document Version")
        rule_sel = st.selectbox("Rule", rules["title"].astype(str)+" — "+rules["rule_id"].astype(str))
        rid = rule_sel.split(" — ")[-1]
        version_no = st.text_input("Version No")
        summary = st.text_area("Change Summary")
        file_upload_panel(actor, "rule_library", rid, "Rule Document")
        if st.button("Add Version Record"):
            vid = uid("VER")
            linked_files = db_all("files")
            latest = linked_files[linked_files["linked_id"] == rid].tail(1)
            file_link = latest.iloc[0]["public_url"] if not latest.empty else ""
            db_insert("document_versions", {"version_id": vid, "rule_id": rid, "version_no": version_no, "revision_date": today(), "change_summary": summary, "file_link": file_link, "uploaded_by": actor_get(actor, "name"), "approved_by": actor_get(actor, "name"), "status": "Approved", "created_on": now()})
            db_update("rule_library", "rule_id", rid, {"current_version_id": vid, "revision": version_no, "updated_on": today()})
            st.success("Version added.")
    table(db_all("document_versions"))

def qms_page(actor):
    st.header("QMS / CAPA / Audit")
    tabs = st.tabs(["CAPA", "Audit Trail", "Notifications", "Evidence Review"])
    with tabs[0]:
        users = db_all("users")
        with st.form("capa"):
            finding = st.text_input("Finding")
            severity = st.selectbox("Severity", ["Low", "Medium", "High"])
            owner = st.selectbox("Owner", users["name"].astype(str)+" — "+users["user_id"].astype(str))
            due = st.date_input("Due", date.today()+pd.Timedelta(days=30))
            action = st.text_area("Corrective Action")
            submit = st.form_submit_button("Create CAPA")
        if submit and finding:
            owner_name, owner_id = owner.split(" — ")
            db_insert("capa_register", {"capa_id": uid("CAPA"), "source": "Training/Competency/QMS", "finding": finding, "severity": severity, "owner_id": owner_id, "owner_name": owner_name, "due_date": str(due), "status": "Open", "corrective_action": action, "created_on": now(), "updated_on": now()})
            st.success("CAPA created.")
        table(db_all("capa_register"))
    with tabs[1]: table(db_all("audit_trail"))
    with tabs[2]: table(db_all("notifications"))
    with tabs[3]:
        files = db_all("files")
        pending = files[files["review_status"] == "Pending Review"] if not files.empty else pd.DataFrame()
        table(pending)
        if not pending.empty:
            sel = st.selectbox("File", pending["file_name"].astype(str)+" — "+pending["file_id"].astype(str))
            fid = sel.split(" — ")[-1]
            status = st.selectbox("Review Status", ["Accepted", "Rejected", "Need Clarification"])
            if st.button("Save Review"):
                db_update("files", "file_id", fid, {"review_status": status, "updated_on": now()})
                st.success("Reviewed.")

def ai_gap_page(actor):
    st.header("AI Competency Gap Analysis")
    users = db_all("users")
    if users.empty:
        return
    person = st.selectbox("Person", users["name"].astype(str)+" — "+users["user_id"].astype(str))
    uidv = person.split(" — ")[-1]
    comp = db_all("competency_matrix")
    records = db_all("training_records")
    gaps = []
    user_comp = comp[comp["user_id"] == uidv] if not comp.empty else pd.DataFrame()
    if user_comp.empty:
        gaps.append("No competency matrix defined.")
    for _, c in user_comp.iterrows():
        ok, msg = evidence_status(c)
        if not ok:
            gaps.append(f"{c['scope']}: evidence incomplete — {msg}")
        if days_until(c["expiry_date"]) <= 90:
            gaps.append(f"{c['scope']}: expiry/revalidation due on {c['expiry_date']}.")
    failed = records[(records["user_id"] == uidv) & (records["test_status"] == "Failed")] if not records.empty else pd.DataFrame()
    if not failed.empty:
        gaps.append(f"{len(failed)} failed assessment(s).")
    if not gaps:
        gaps.append("No major gap identified.")
    for g in gaps:
        st.write("- " + g)

def scorm_page(actor):
    st.header("SCORM/LMS Register")
    table(db_all("scorm_lms_records"))

def backup_page(actor):
    st.header("Audit Backup")
    tables = ["users","trainings","files","training_records","question_bank","assessment_history","scorm_lms_records","competency_matrix","authorization_requests","authorization_certificates","job_requests","supervised_logbook","witness_surveys","rule_library","document_versions","scope_library","notifications","capa_register","audit_trail"]
    export = {t: db_all(t).to_dict(orient="records") for t in tables}
    st.download_button("Download JSON Backup", json.dumps(export, indent=2, default=str), file_name=f"psb_backup_{today()}.json", mime="application/json")
    with io.BytesIO() as buf:
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            for t in tables:
                db_all(t).to_excel(writer, sheet_name=t[:31], index=False)
        st.download_button("Download Excel Backup", buf.getvalue(), file_name=f"psb_backup_{today()}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

def qr_verify_page(actor):
    st.header("Public QR Verification")
    cert_id = st.text_input("Certificate ID")
    if st.button("Verify") and cert_id:
        certs = db_all("authorization_certificates")
        c = certs[certs["certificate_id"] == cert_id] if not certs.empty else pd.DataFrame()
        if c.empty:
            st.error("Certificate not found.")
        else:
            row = c.iloc[0]
            st.success("Valid certificate." if row["status"] == "Valid" and days_until(row["expiry_date"]) >= 0 else "Invalid or expired.")
            st.write(row[["certificate_id", "name", "job_type", "scope", "issue_date", "expiry_date", "status", "verification_url"]])

def management_page(actor):
    dashboard_page(actor)
    st.subheader("Jobs")
    table(db_all("job_requests"))
    st.subheader("Authorizations")
    table(db_all("authorization_requests"))

def main():
    st.set_page_config(page_title=APP_TITLE, page_icon="⚓", layout="wide")
    init_db()
    apply_style()
    actor = require_login()
    header()
    page = sidebar(actor)
    if page == "Dashboard": dashboard_page(actor)
    elif page == "Admin": admin_page(actor)
    elif page == "Training": training_page(actor)
    elif page == "Files": files_page(actor)
    elif page == "Competency": competency_page(actor)
    elif page == "Authorization": authorization_page(actor)
    elif page == "Job Allocation": job_allocation_page(actor)
    elif page == "Logbook": logbook_page(actor)
    elif page == "Witness Mobile": witness_page(actor)
    elif page == "Rule Library": rule_library_page(actor)
    elif page == "QMS": qms_page(actor)
    elif page == "SCORM/LMS": scorm_page(actor)
    elif page == "AI Gap Analysis": ai_gap_page(actor)
    elif page == "Backup": backup_page(actor)
    elif page == "Public QR Verify": qr_verify_page(actor)
    elif page == "Management": management_page(actor)

if __name__ == "__main__":
    main()
