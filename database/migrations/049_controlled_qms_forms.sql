create table if not exists controlled_qms_forms (
  form_code text primary key,
  title text not null,
  filename text not null,
  mime_type text not null default 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  procedure_ref text,
  path_key text not null default 'All',
  stages text not null,
  applies_to text,
  category text not null default 'Other',
  purpose text,
  template_base64 text not null,
  active text not null default 'Yes',
  created_on text,
  updated_on text
);
