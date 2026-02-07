"""
Windows-safe credential storage - NO chmod, NO encryption complexity
For personal use only (credentials stored as plaintext in user's home directory)
"""
import json
from pathlib import Path
from datetime import datetime, timezone

class CredentialManager:
    def __init__(self, app_name="jobtrack"):
        # Store in user's home directory (Windows-safe location)
        self.app_dir = Path.home() / f".{app_name}"
        self.app_dir.mkdir(exist_ok=True)
        self.creds_file = self.app_dir / "email_credentials.json"
        self._load()
    
    def _load(self):
        if self.creds_file.exists():
            try:
                with open(self.creds_file, "r") as f:
                    self.data = json.load(f)
            except:
                self.data = {}
        else:
            self.data = {}
    
    def _save(self):
        with open(self.creds_file, "w") as f:
            json.dump(self.data, f, indent=2)
    
    def save_credentials(self, email_address, app_password):
        """Save credentials (plaintext but in secure user directory)"""
        self.data[email_address] = {
            "password": app_password,
            "saved_at": datetime.now(timezone.utc).isoformat()
        }
        self._save()
        return True
    
    def load_credentials(self, email_address):
        """Load credentials - returns dict or None"""
        if email_address in self.data:
            return {
                "email": email_address,
                "password": self.data[email_address]["password"],
                "saved_at": self.data[email_address]["saved_at"]
            }
        return None
    
    def delete_credentials(self, email_address):
        """Delete stored credentials"""
        if email_address in self.data:
            del self.data[email_address]
            self._save()
            return True
        return False