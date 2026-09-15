from __future__ import annotations

import html
import streamlit.components.v1 as components

from psb_app.common import (
    actor_get,
    can_action,
    clean,
    days_until,
    db_all_unscoped,
    db_where_unscoped,
    pd,
    st,
    table_exists,
)
from psb_app.services.certificate_service import build_certificate, build_training_attestation


def _enterprise_access(actor: dict) -> bool:
    role = clean(actor_get(actor, 'role')).strip()
    return (
        role in {'Admin', 'GM', 'Management'}
        or can_action(actor, 'Authorization', 'Manage', 'Organization-wide')
        or can_action(actor, 'Administration', 'Manage', 'Organization-wide')
    )


def _esc(value) -> str:
    return html.escape(clean(value) or '—', quote=True)


def _inject_style() -> None:
    st.markdown(
        """
        <style>
        .psb-cert-hero{border:1px solid #d7e0e7;border-radius:18px;padding:22px 24px;margin:8px 0 18px;background:linear-gradient(135deg,#fff 0%,#f7faf9 62%,#eef7f2 100%);box-shadow:0 8px 26px rgba(15,45,64,.07)}
        .psb-cert-kicker{color:#0b6b42;font-size:.76rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase;margin-bottom:6px}
        .psb-cert-name{color:#102a3a;font-size:1.55rem;font-weight:800;line-height:1.2;margin-bottom:4px}
        .psb-cert-subtitle{color:#607381;font-size:.95rem;margin-bottom:18px}
        .psb-cert-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}
        .psb-cert-field{background:#fff;border:1px solid #e4eaee;border-radius:12px;padding:12px 13px;min-height:72px}
        .psb-cert-label{color:#7a8b97;font-size:.69rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;margin-bottom:5px}
        .psb-cert-value{color:#173446;font-size:.91rem;font-weight:700;overflow-wrap:anywhere}
        .psb-cert-valid{display:inline-block;color:#0b6b42;background:#eaf7f0;border:1px solid #c8ead7;padding:5px 10px;border-radius:999px;font-weight:800;font-size:.78rem}
        .psb-cert-invalid{display:inline-block;color:#9d2727;background:#fff0f0;border:1px solid #f2cccc;padding:5px 10px;border-radius:999px;font-weight:800;font-size:.78rem}
        .psb-module-box{border-left:4px solid #0b6b42;background:#f8fbf9;border-radius:10px;padding:12px 15px;margin:8px 0 14px}
        .psb-module-box div{margin:3px 0;color:#334e5d}
        @media(max-width:900px){.psb-cert-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
        @media(max-width:560px){.psb-cert-grid{grid-template-columns:1fr}}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _certificate_card(kind: str, row: dict, fields: list[tuple[str, str]]) -> None:
    status = clean(row.get('status')) or 'Unknown'
    valid = status.casefold() == 'valid'
    badge = (
        f"<span class='psb-cert-valid'>{_esc(status)}</span>"
        if valid else f"<span class='psb-cert-invalid'>{_esc(status)}</span>"
    )
    title = clean(row.get('name')) or 'Certificate Holder'
    subtitle = clean(row.get('scope')) if kind.startswith('Authorization') else clean(row.get('training_title'))
    cells = ''.join(
        f"<div class='psb-cert-field'><div class='psb-cert-label'>{_esc(label)}</div><div class='psb-cert-value'>{_esc(value)}</div></div>"
        for label, value in fields
    )
    st.markdown(
        f"""
        <div class='psb-cert-hero'>
          <div class='psb-cert-kicker'>{_esc(kind)}</div>
          <div class='psb-cert-name'>{_esc(title)}</div>
          <div class='psb-cert-subtitle'>{_esc(subtitle)}</div>
          <div style='margin-bottom:14px'>{badge}</div>
          <div class='psb-cert-grid'>{cells}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _authorization_center(certs: pd.DataFrame) -> None:
    if certs.empty:
        st.warning('No authorization certificate is currently linked to this account.')
        return
    certs = certs.copy()
    if 'issue_date' in certs.columns:
        certs = certs.sort_values(['issue_date', 'name'] if 'name' in certs.columns else ['issue_date'], ascending=False)

    search = st.text_input(
        'Find authorization certificate',
        placeholder='Search by holder, qualification/scope or certificate ID',
        key='professional_auth_certificate_search_fixed',
    )
    shown = certs
    if search.strip():
        needle = search.strip().casefold()
        mask = shown.astype(str).apply(lambda col: col.str.casefold().str.contains(needle, regex=False, na=False)).any(axis=1)
        shown = shown[mask]
    if shown.empty:
        st.info('No authorization certificate matches the current search.')
        return

    labels, label_to_id = [], {}
    for _, r in shown.iterrows():
        label = f"{clean(r.get('name'))} · {clean(r.get('scope'))} · {clean(r.get('certificate_id'))}"
        labels.append(label)
        label_to_id[label] = clean(r.get('certificate_id'))

    selected = st.selectbox('Authorization certificate', labels, key='professional_auth_certificate_select_fixed')
    certificate_id = label_to_id[selected]
    row = shown[shown['certificate_id'].astype(str).eq(certificate_id)].iloc[-1].to_dict()

    _certificate_card(
        'Authorization Certificate · PSB-PTQ20-F02',
        row,
        [
            ('Certificate ID', certificate_id),
            ('Qualification / Scope', clean(row.get('scope'))),
            ('Job Type', clean(row.get('job_type'))),
            ('Status', clean(row.get('status'))),
            ('Issue Date', clean(row.get('issue_date'))),
            ('Valid Until', clean(row.get('expiry_date'))),
            ('Trainer', clean(row.get('trainer_name'))),
            ('Document / Revision', f"{clean(row.get('document_code')) or 'PSB-PTQ20-F02'} · Rev {clean(row.get('revision_no')) or '01'}"),
        ],
    )

    modules = [x.strip(' •-\t') for x in clean(row.get('completed_modules')).replace(';', '\n').splitlines() if x.strip()]
    if modules:
        st.markdown('#### Completed Qualification Modules')
        st.markdown(
            "<div class='psb-module-box'>" + ''.join(f"<div>✓ {_esc(item)}</div>" for item in modules) + '</div>',
            unsafe_allow_html=True,
        )

    st.markdown('### Generated Authorization Certificate')
    st.caption('The official PSB-PTQ20-F02 digital authorization certificate is attached below. It includes the CEO signature on the left, the recorded Trainer signature on the right, the PSB document control details and QR verification.')
    _, certificate_html, _ = build_certificate(pd.Series(row))
    components.html(certificate_html, height=1180, scrolling=True)

    b1, b2 = st.columns(2)
    b1.download_button(
        'Download Authorization Certificate',
        data=certificate_html,
        file_name=f'{certificate_id}.html',
        mime='text/html',
        use_container_width=True,
        key=f'professional_auth_download_fixed_{certificate_id}',
    )
    verification_url = clean(row.get('verification_url'))
    if verification_url:
        b2.link_button('Verify Authorization Certificate', verification_url, use_container_width=True)

    if table_exists('authorization_certificate_history'):
        history = db_where_unscoped('authorization_certificate_history', 'certificate_id = :cid', (('cid', certificate_id),))
        if not history.empty:
            with st.expander('Certificate history & audit trail', expanded=False):
                if 'event_on' in history.columns:
                    history = history.sort_values('event_on', ascending=False)
                for _, event in history.iterrows():
                    st.markdown(
                        f"**{clean(event.get('event_type')) or 'Certificate Event'}**  \n"
                        f"{clean(event.get('event_on')) or '—'} · {clean(event.get('actor_name')) or 'System'}  \n"
                        f"{clean(event.get('from_status')) or '—'} → {clean(event.get('to_status')) or '—'}"
                    )
                    if clean(event.get('reason')):
                        st.caption(clean(event.get('reason')))
                    st.divider()


def _attestation_center(certs: pd.DataFrame) -> None:
    if certs.empty:
        st.info('No training attestation certificates are currently linked to this account.')
        return
    certs = certs.copy()
    if 'issue_date' in certs.columns:
        certs = certs.sort_values('issue_date', ascending=False)

    search = st.text_input(
        'Find training attestation',
        placeholder='Search by holder, training, module or certificate ID',
        key='professional_attestation_search_fixed',
    )
    shown = certs
    if search.strip():
        needle = search.strip().casefold()
        mask = shown.astype(str).apply(lambda col: col.str.casefold().str.contains(needle, regex=False, na=False)).any(axis=1)
        shown = shown[mask]
    if shown.empty:
        st.info('No training attestation matches the current search.')
        return

    labels, label_to_id = [], {}
    for _, r in shown.iterrows():
        module = clean(r.get('module_code')) or clean(r.get('training_title'))
        label = f"{clean(r.get('name'))} · {module} · {clean(r.get('certificate_id'))}"
        labels.append(label)
        label_to_id[label] = clean(r.get('certificate_id'))

    selected = st.selectbox('Training attestation certificate', labels, key='professional_attestation_select_fixed')
    certificate_id = label_to_id[selected]
    row = shown[shown['certificate_id'].astype(str).eq(certificate_id)].iloc[-1].to_dict()

    _certificate_card(
        'Training Course Attestation · PSB-PTQ20-F03',
        row,
        [
            ('Certificate ID', certificate_id),
            ('Training', clean(row.get('training_title'))),
            ('Module', ' · '.join(x for x in [clean(row.get('module_code')), clean(row.get('module_name'))] if x)),
            ('Status', clean(row.get('status'))),
            ('Training Completed', clean(row.get('conducted_on'))),
            ('Issued On', clean(row.get('issue_date'))),
            ('Trainer', clean(row.get('trainer_name'))),
            ('Document / Revision', f"{clean(row.get('document_code')) or 'PSB-PTQ20-F03'} · Rev {clean(row.get('revision_no')) or '01'}"),
        ],
    )

    basis = clean(row.get('completion_basis'))
    if basis:
        st.markdown('#### Completion Basis')
        st.info(basis)

    st.markdown('### Generated Training Attestation')
    certificate_html, _ = build_training_attestation(pd.Series(row))
    components.html(certificate_html, height=1180, scrolling=True)
    b1, b2 = st.columns(2)
    b1.download_button(
        'Download Training Attestation',
        data=certificate_html,
        file_name=f'{certificate_id}.html',
        mime='text/html',
        use_container_width=True,
        key=f'professional_attestation_download_fixed_{certificate_id}',
    )
    verification_url = clean(row.get('verification_url'))
    if verification_url:
        b2.link_button('Verify Training Attestation', verification_url, use_container_width=True)


def professional_certificate_center(actor: dict) -> None:
    _inject_style()
    enterprise = _enterprise_access(actor)
    actor_id = clean(actor_get(actor, 'user_id'))

    # Deliberately use the unscoped repository read here and apply the certificate
    # scope below. The shared db_all() helper caches scoped frames by table name,
    # which can make a certificate set from one session appear in another session.
    # Certificate access is simple and explicit: enterprise roles see the register;
    # every other person sees only certificates whose user_id is their own.
    auth_certs = db_all_unscoped('authorization_certificates') if table_exists('authorization_certificates') else pd.DataFrame()
    attestations = db_all_unscoped('training_attestation_certificates') if table_exists('training_attestation_certificates') else pd.DataFrame()

    if not enterprise:
        if not auth_certs.empty:
            auth_certs = auth_certs[auth_certs.get('user_id', pd.Series('', index=auth_certs.index)).astype(str).eq(actor_id)]
        if not attestations.empty:
            attestations = attestations[attestations.get('user_id', pd.Series('', index=attestations.index)).astype(str).eq(actor_id)]

    active_auth = 0
    expiring_auth = 0
    if not auth_certs.empty:
        status = auth_certs.get('status', pd.Series('', index=auth_certs.index)).astype(str).str.casefold()
        expiry_days = auth_certs.get('expiry_date', pd.Series('', index=auth_certs.index)).astype(str).map(days_until)
        active_mask = status.eq('valid') & (expiry_days >= 0)
        active_auth = int(active_mask.sum())
        expiring_auth = int((active_mask & (expiry_days <= 90)).sum())

    valid_attestations = 0
    if not attestations.empty:
        valid_attestations = int(attestations.get('status', pd.Series('', index=attestations.index)).astype(str).str.casefold().eq('valid').sum())

    st.header('Certificate Center' if enterprise else 'My Certificates')
    if enterprise:
        st.caption('Organization-wide controlled PSB certificate center. Select an employee certificate to preview, download or verify it.')
    else:
        st.caption('Your controlled PSB certificates. Only certificates issued to your own account are shown here.')

    m1, m2, m3, m4 = st.columns(4)
    m1.metric('Authorization Certificates', len(auth_certs))
    m2.metric('Active Authorizations', active_auth)
    m3.metric('Training Attestations', valid_attestations)
    m4.metric('Expiring ≤90 Days', expiring_auth)

    if not auth_certs.empty:
        st.success(f'{len(auth_certs)} authorization certificate(s) available in your current view.')

    tab_auth, tab_att = st.tabs([
        f'Authorization Certificates ({len(auth_certs)})',
        f'Training Attestations ({len(attestations)})',
    ])
    with tab_auth:
        _authorization_center(auth_certs)
    with tab_att:
        _attestation_center(attestations)
