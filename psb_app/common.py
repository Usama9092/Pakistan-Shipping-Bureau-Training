"""Compatibility facade for PSB runtime services.

New code should import the narrowest core/service module available. This facade
exists only to preserve the existing page API while keeping the runtime modular.
"""
from pathlib import Path
from psb_app import legacy_runtime as _runtime
ROOT = Path(__file__).resolve().parents[1]

def __getattr__(name):
    return getattr(_runtime, name)

def __dir__():
    return sorted(set(globals()) | set(dir(_runtime)))

from psb_app.services.database_service import (
    ensure_accreditation_schema, ensure_client_feedback_schema, ensure_interpretation_schema,
    init_db, seed_demo, ensure_indexes,
)


def table(df, max_rows: int = 300) -> None:
    """Shared bounded dataframe renderer used by page modules.

    Defined in the compatibility facade rather than auth_ui so technical pages do
    not depend on the authentication/page-shell module (which also prevents an
    import-cycle between UI pages).
    """
    if df is None or getattr(df, 'empty', True):
        _runtime.st.markdown("<div class='psb-empty'>No records found for the current filters.</div>", unsafe_allow_html=True)
        return
    shown = df.fillna('')
    if len(shown) > max_rows:
        _runtime.st.caption(f'Showing latest {max_rows} of {len(shown)} records for faster loading. Use Backup/Export for full data.')
        shown = shown.tail(max_rows)
    _runtime.st.dataframe(shown, width='stretch', hide_index=True)
