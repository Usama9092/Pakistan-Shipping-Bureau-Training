from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class RolePresentation:
    label: str
    accent: str
    description: str

ROLE_PRESENTATIONS = {
    'GM': RolePresentation('Global Manager', '#071225', 'Executive governance, decisions, risk and accountability'),
    'Admin': RolePresentation('Administrator', '#0b3b76', 'System, access and governance controls'),
    'Trainer': RolePresentation('Trainer', '#0f766e', 'Training delivery and learner progress'),
    'Department Manager': RolePresentation('Department Manager', '#1e40af', 'Assigned department qualification governance'),
    'Surveyor': RolePresentation('Surveyor', '#2563eb', 'Authorized survey activity'),
    'Plan Appraiser': RolePresentation('Plan Appraiser', '#2563eb', 'Plan appraisal activity'),
    'QMS Auditor': RolePresentation('QMS Auditor', '#b45309', 'Quality audit and compliance'),
    'Industrial Surveyor': RolePresentation('Industrial Surveyor', '#2563eb', 'Industrial survey activity'),
    'Rule Development Rep': RolePresentation('Rule Development', '#7c2d12', 'Rules, interpretations and change control'),
    'QMR': RolePresentation('QMR', '#92400e', 'Quality management oversight'),
    'Management': RolePresentation('Management', '#111827', 'Management oversight and approvals'),
    'Trainee': RolePresentation('Trainee', '#475569', 'Assigned training and development'),
    'On Probation': RolePresentation('On Probation', '#475569', 'Probationary development'),
}

def role_presentation(role: str) -> RolePresentation:
    return ROLE_PRESENTATIONS.get(role, RolePresentation(role or 'User', '#0b3b76', 'PSB workforce platform'))

def page_kicker(page: str, role: str) -> str:
    p = role_presentation(role)
    return f"<div class='psb-page-kicker'><span class='psb-role-dot' style='background:{p.accent}'></span><span>{p.label}</span><span class='psb-kicker-sep'>•</span><span>{page}</span><span class='psb-role-description'>{p.description}</span></div>"
