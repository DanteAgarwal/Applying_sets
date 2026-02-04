"""
Minimal security module for credential encryption
"""
from datetime import datetime ,timezone
import os
import json
from pathlib import Path
from cryptography.fernet import Fernet

class CredentialManager:
    def __init__(self):
        self.creds_file = Path("credentials.enc")
        self.key_file = Path("secret.key")
        
        # Generate/load key
        if not self.key_file.exists():
            key = Fernet.generate_key()
            with open(self.key_file, "wb") as f:
                f.write(key)
            os.chmod(self.key_file, 0o600)
        else:
            with open(self.key_file, "rb") as f:
                key = f.read()
        
        self.fernet = Fernet(key)
    
    def save_credentials(self, email_address, app_password):
        creds = {
            "email": email_address,
            "password": app_password,
            "saved_at": str(datetime.now(timezone.utc))
        }
        encrypted = self.fernet.encrypt(json.dumps(creds).encode())
        
        with open(self.creds_file, "wb") as f:
            f.write(encrypted)
        os.chmod(self.creds_file, 0o600)
        return True
    
    def load_credentials(self, email_address):
        if not self.creds_file.exists():
            return None
        
        try:
            with open(self.creds_file, "rb") as f:
                encrypted = f.read()
            decrypted = self.fernet.decrypt(encrypted)
            creds = json.loads(decrypted.decode())
            
            if creds.get("email") == email_address:
                return creds
            return None
        except Exception:
            return None