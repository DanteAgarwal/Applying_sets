"""
Windows-safe credential storage - NO chmod, NO encryption complexity
For personal use only (credentials stored as plaintext in user's home directory)
"""
import json
from pathlib import Path
import base64
from datetime import datetime, timezone

class SimpleCredentialStore:
    """Windows-safe credential storage without chmod issues"""
    def __init__(self, app_name="jobtrack"):
        self.app_dir = Path.home() / f".{app_name}"
        self.app_dir.mkdir(exist_ok=True)
        self.creds_file = self.app_dir / "email_creds.json"
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
            json.dump(self.data, f)

    def save(self, email, password):
        """Save credentials (plaintext but in user's hidden dir - sufficient for personal use)"""
        self.data[email] = {
            "password": password,
            "saved_at": datetime.now(timezone.utc).isoformat()
        }
        self._save()
        return True

    def load(self, email):
        """Load credentials"""
        if email in self.data:
            return {
                "email": email,
                "password": self.data[email]["password"],
                "saved_at": self.data[email]["saved_at"]
            }
        return None

    def delete(self, email):
        """Delete credentials"""
        if email in self.data:
            del self.data[email]
            self._save()
            return True
        return False

    def save_profile(self, your_name: str):
        """Save a small profile entry (your display name)"""
        if "__profile__" not in self.data:
            self.data["__profile__"] = {}
        self.data["__profile__"]["your_name"] = your_name
        self._save()

    def save_default_resume(self, filename: str, content: bytes, mimetype: str = "application/octet-stream"):
        """Save a default resume (base64) in the store"""
        if "__profile__" not in self.data:
            self.data["__profile__"] = {}
        self.data["__profile__"]["default_resume"] = {
            "filename": filename,
            "mimetype": mimetype,
            "content_b64": base64.b64encode(content).decode("ascii")
        }
        self._save()

    def load_default_resume(self):
        """Return (filename, bytes, mimetype) or None"""
        p = self.data.get("__profile__")
        if not p:
            return None
        r = p.get("default_resume")
        if not r:
            return None
        try:
            return r["filename"], base64.b64decode(r["content_b64"]), r.get("mimetype", "application/octet-stream")
        except Exception:
            return None

    def load_profile(self):
        """Load profile (returns your_name or None)"""
        p = self.data.get("__profile__")
        if p:
            return p.get("your_name")
        return None
