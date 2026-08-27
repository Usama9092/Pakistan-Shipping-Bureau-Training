-- Additional audit requirements introduced by role-experience workspaces.
insert into audit_event_requirements(requirement_id,module_name,action_name,notes) values
('AUD-PROBATION','Probation Review','Save','Formal probation review creation/decision must emit audit event'),
('AUD-AUTH-LINK','Authorization','Evidence Link','Exact authorization-case evidence linkage must emit audit event'),
('AUD-CERT-REVOKE','Certificate Center','Revoke','Certificate suspension/revocation must emit audit event'),
('AUD-MGMT-REVIEW','Management Review','Save','Management review governance record changes must emit audit event')
on conflict (module_name, action_name) do nothing;
