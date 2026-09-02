"""Offline encryption check. A real DB drill is scripts/encrypted_postgres_restore_drill.py."""
from cryptography.fernet import Fernet

def run():
    key=Fernet.generate_key(); cipher=Fernet(key)
    source=b'PSB staging backup verification payload'
    encrypted=cipher.encrypt(source)
    assert source not in encrypted and cipher.decrypt(encrypted)==source
    print('ENCRYPTED BACKUP ROUND-TRIP: PASS')
if __name__=='__main__': run()

