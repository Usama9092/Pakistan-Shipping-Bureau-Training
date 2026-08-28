"""Extracted service boundary from the legacy runtime.
The module consumes the established runtime context for compatibility.
"""
from __future__ import annotations
from psb_app.legacy_runtime import (
    actor_get,
    audit,
    can_action,
    datetime,
    db_all,
    db_update,
    io,
    json,
    now,
    pd,
    st,
    table_exists,
)

def _admin_only(actor: dict) -> bool:
    # The canonical administrator role must never depend on an optional
    # permission-matrix row to enter the Administration workspace.  The
    # matrix remains authoritative for delegated/non-admin access.
    role = str(actor_get(actor, 'role', '') or '').strip().lower()
    if role not in {'admin', 'administrator'} and not can_action(actor, 'Administration', 'Manage', 'Organization-wide'):
        st.error('Administrator access is required for this page.')
        return False
    return True

def _setting_value(settings_df: pd.DataFrame, key: str, default: str='') -> str:
    if settings_df is None or settings_df.empty or 'setting_key' not in settings_df.columns:
        return default
    rows = settings_df[settings_df['setting_key'] == key]
    if rows.empty:
        return default
    value = rows.iloc[0].get('setting_value', default)
    return default if pd.isna(value) else str(value)

def _setting_bool(settings_df: pd.DataFrame, key: str, default: bool=False) -> bool:
    return _setting_value(settings_df, key, 'Yes' if default else 'No').strip().lower() in {'yes', 'true', '1', 'on', 'enabled'}

def _save_setting(actor: dict, key: str, value: str, reason: str='Configuration change') -> None:
    db_update('system_settings', 'setting_key', key, {'setting_value': str(value), 'updated_by': actor_get(actor, 'user_id'), 'updated_on': now()})
    audit('System Setting Changed', f'{key} updated', actor=actor, entity_type='System Setting', entity_id=key, reason=reason, after_value=str(value))

def _backup_export_tables() -> list[str]:
    """Return business tables suitable for an application-level backup export."""
    tables = ['users', 'user_departments', 'user_assignments', 'roles', 'permissions', 'role_permissions', 'user_permission_overrides', 'departments', 'system_settings', 'training_modules', 'trainings', 'files', 'training_records', 'question_bank', 'assessment_history', 'competency_matrix', 'authorization_matrix', 'development_plans', 'field_exposure_matrix', 'witness_surveys', 'supervised_activities', 'authorization_requests', 'authorization_certificates', 'crb_reviews', 'annual_reviews', 'revalidation_requests', 'job_requests', 'kpi_records', 'cpd_records', 'knowledge_library', 'knowledge_acknowledgements', 'rule_library', 'document_versions', 'capa_register', 'notifications', 'audit_trail', 'technical_authorities', 'technical_reviews', 'competency_ncrs', 'authorization_restrictions', 'client_feedback', 'succession_plans', 'workforce_forecasts', 'accreditation_evidence', 'technical_interpretations']
    return [t for t in tables if table_exists(t)]

def _sanitize_backup_frame(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    """Remove credentials/secrets from application-level exports."""
    if df is None or df.empty:
        return df
    out = df.copy()
    sensitive_names = {'password', 'temp_password', 'password_hash', 'reset_token', 'access_token', 'refresh_token', 'service_key', 'smtp_password', 'api_key', 'secret'}
    drop_cols = [c for c in out.columns if str(c).strip().lower() in sensitive_names or any((x in str(c).strip().lower() for x in ['password_hash', 'reset_token', 'access_token', 'refresh_token', 'service_key', 'smtp_password', 'api_key']))]
    if table_name == 'users' and 'password' in out.columns:
        drop_cols.append('password')
    if drop_cols:
        out = out.drop(columns=list(dict.fromkeys([c for c in drop_cols if c in out.columns])), errors='ignore')
    if table_name == 'system_settings' and (not out.empty):
        key_col = 'setting_key' if 'setting_key' in out.columns else None
        if key_col:
            mask = out[key_col].astype(str).str.lower().str.contains('password|secret|token|key|credential', regex=True, na=False)
            out = out.loc[~mask].copy()
    return out

def _build_backup_payload(backup_type: str, tables: list[str]):
    generated_on = now()
    if backup_type == 'Application Data Export (JSON)':
        export = {'metadata': {'format': 'PSB Application Data Export', 'version': '1.0', 'generated_on': generated_on, 'table_count': len(tables), 'credential_fields_excluded': True, 'note': 'Application-level export; not a substitute for a managed PostgreSQL/Supabase backup.'}, 'tables': {t: _sanitize_backup_frame(db_all(t), t).to_dict(orient='records') for t in tables}}
        return (json.dumps(export, indent=2, default=str).encode(), 'application/json', f"psb_application_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with io.BytesIO() as buf:
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            meta = pd.DataFrame([{'Format': 'PSB Application Data Export', 'Version': '1.0', 'Generated On': generated_on, 'Tables': len(tables), 'Credential Fields Excluded': True, 'Note': 'Application-level export; not a substitute for a managed PostgreSQL/Supabase backup.'}])
            meta.to_excel(writer, sheet_name='_metadata', index=False)
            for t in tables:
                _sanitize_backup_frame(db_all(t), t).to_excel(writer, sheet_name=t[:31], index=False)
        return (buf.getvalue(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', f"psb_application_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
