create table if not exists schema_migrations (version text primary key, checksum text not null, applied_on text not null);
