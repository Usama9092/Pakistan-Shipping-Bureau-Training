-- Phase: authoritative role/scope alignment for direct Supabase reads.
-- The application remains the primary server-side enforcement layer.
create or replace function public.psb_current_user_id() returns text language sql stable security definer set search_path=public as $$
  select user_id from public.users where auth_user_id=auth.uid() limit 1
$$;
create or replace function public.psb_current_role() returns text language sql stable security definer set search_path=public as $$
  select role from public.users where auth_user_id=auth.uid() limit 1
$$;
create or replace function public.psb_can_access_user(target text) returns boolean language plpgsql stable security definer set search_path=public as $$
declare me text := public.psb_current_user_id(); role_name text := coalesce(public.psb_current_role(),'');
begin
  if me is null or me='' or target is null or target='' then return false; end if;
  if role_name in ('Admin','Management','Technical Manager','QMR','Job Coordinator') then return true; end if;
  if role_name in ('Surveyor','Plan Appraiser','Industrial Surveyor','Trainee','On Probation') then return target=me; end if;
  if role_name = 'Trainer' then return target=me or exists(select 1 from public.users u where u.user_id=target and (u.tutor_id=me or u.mentor_id=me or u.trainer_id=me or u.assigner_id=me)); end if;
  if role_name in ('QMS Auditor','Lead Auditor','Principal Surveyor','Chief Plan Appraiser') then return target=me or exists(select 1 from public.user_departments ut join public.user_departments um on um.department=ut.department and um.status='Active' where ut.user_id=target and ut.status='Active' and um.user_id=me); end if;
  return target=me;
end; $$;
comment on function public.psb_can_access_user(text) is 'Phase 6: role-aware user scope. Do not widen without matching application access_policy rules.';
