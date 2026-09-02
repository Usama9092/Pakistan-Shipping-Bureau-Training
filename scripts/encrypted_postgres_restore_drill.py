"""Encrypted PostgreSQL backup/restore drill for an isolated staging target only."""
from __future__ import annotations
import hashlib, json, os, subprocess, tempfile
from pathlib import Path
from urllib.parse import urlparse
from cryptography.fernet import Fernet

def required(name):
    value=os.getenv(name,'')
    if not value: raise SystemExit(f'Missing required environment variable: {name}')
    return value

def db_name(url): return urlparse(url).path.lstrip('/')

def main():
    source=required('PSB_BACKUP_SOURCE_DATABASE_URL')
    target=required('PSB_RESTORE_TARGET_DATABASE_URL')
    key=required('PSB_BACKUP_ENCRYPTION_KEY').encode()
    if required('PSB_RESTORE_TARGET_CONFIRM') != 'staging':
        raise SystemExit('Refusing restore: PSB_RESTORE_TARGET_CONFIRM must equal staging')
    if source == target: raise SystemExit('Refusing restore: source and target are identical')
    if required('PSB_RESTORE_ALLOW_TARGET') != db_name(target):
        raise SystemExit('Refusing restore: allowlisted target database name does not match')
    with tempfile.TemporaryDirectory() as td:
        root=Path(td); dump=root/'source.dump'; encrypted=root/'source.dump.enc'; restored=root/'restore.dump'
        subprocess.run(['pg_dump','--format=custom','--no-owner','--file',str(dump),source],check=True)
        encrypted.write_bytes(Fernet(key).encrypt(dump.read_bytes()))
        restored.write_bytes(Fernet(key).decrypt(encrypted.read_bytes()))
        subprocess.run(['pg_restore','--clean','--if-exists','--no-owner','--dbname',target,str(restored)],check=True)
        evidence={'target_database':db_name(target),'encrypted_sha256':hashlib.sha256(encrypted.read_bytes()).hexdigest(),'restore_completed':True}
        Path(os.getenv('PSB_RESTORE_EVIDENCE_FILE','restore-drill-evidence.json')).write_text(json.dumps(evidence,indent=2))
        print(json.dumps(evidence))

if __name__=='__main__': main()

