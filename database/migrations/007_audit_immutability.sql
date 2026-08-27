create or replace function psb_block_audit_mutation() returns trigger language plpgsql as $$ begin raise exception 'Audit trail is immutable'; end; $$;
drop trigger if exists trg_audit_trail_immutable on audit_trail;
create trigger trg_audit_trail_immutable before update or delete on audit_trail for each row execute function psb_block_audit_mutation();
