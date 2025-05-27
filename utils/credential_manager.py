# utils/credential_manager.py

import os
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import keyring


class CredentialManager:
    """Securely manage and store ThinkOrSwim credentials."""

    def __init__(self, app_name="DeltaMon"):
        """
        Initialize credential manager.

        Args:
            app_name: Name of the application for keyring
        """
        self.app_name = app_name
        self.key_file = os.path.join(os.path.expanduser('~'), '.deltamonkey')
        self._ensure_key_exists()

    def _ensure_key_exists(self):
        """Ensure encryption key exists, creating if needed."""
        if not os.path.exists(self.key_file):
            # Generate a new key
            salt = os.urandom(16)
            # Use machine-specific info as password
            machine_id = self._get_machine_id()
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(machine_id.encode()))

            # Save key with salt
            with open(self.key_file, 'wb') as f:
                f.write(salt + key)

            # Set permissions to user-only
            os.chmod(self.key_file, 0o600)

    def _get_machine_id(self):
        """Get a unique machine identifier for key derivation."""
        try:
            if os.name == 'nt':  # Windows
                import subprocess
                result = subprocess.check_output('wmic csproduct get uuid').decode()
                return result.split('\n')[1].strip()
            else:  # Linux/Mac
                with open('/etc/machine-id', 'r') as f:
                    return f.read().strip()
        except:
            # Fallback to a fixed string + hostname
            import socket
            return f"DeltaMon-{socket.gethostname()}"

    def _get_encryption_key(self):
        """Get the encryption key from file."""
        with open(self.key_file, 'rb') as f:
            data = f.read()
            salt = data[:16]
            stored_key = data[16:]

        return stored_key

    def save_credentials(self, username, password):
        """
        Save ThinkOrSwim credentials securely.

        Args:
            username: ThinkOrSwim username
            password: ThinkOrSwim password
        """
        try:
            # Use keyring as primary storage
            keyring.set_password(self.app_name, "tos_username", username)
            keyring.set_password(self.app_name, "tos_password", password)

            # Backup storage using file encryption
            key = self._get_encryption_key()
            cipher = Fernet(key)

            creds = {
                "username": username,
                "password": password
            }

            encrypted = cipher.encrypt(json.dumps(creds).encode())

            # Save to backup file
            backup_path = os.path.join(os.path.expanduser('~'), '.deltamonbackup')
            with open(backup_path, 'wb') as f:
                f.write(encrypted)

            # Set permissions
            os.chmod(backup_path, 0o600)

            return True
        except Exception as e:
            print(f"Error saving credentials: {e}")
            return False

    def get_credentials(self):
        """
        Get stored ThinkOrSwim credentials.

        Returns:
            Tuple of (username, password) or (None, None) if not found
        """
        try:
            # Try keyring first
            username = keyring.get_password(self.app_name, "tos_username")
            password = keyring.get_password(self.app_name, "tos_password")

            if username and password:
                return username, password

            # Fall back to backup file
            backup_path = os.path.join(os.path.expanduser('~'), '.deltamonbackup')
            if not os.path.exists(backup_path):
                return None, None

            # Decrypt backup
            key = self._get_encryption_key()
            cipher = Fernet(key)

            with open(backup_path, 'rb') as f:
                encrypted = f.read()

            decrypted = cipher.decrypt(encrypted)
            creds = json.loads(decrypted.decode())

            return creds.get("username"), creds.get("password")

        except Exception as e:
            print(f"Error retrieving credentials: {e}")
            return None, None

    def has_saved_credentials(self):
        """Check if credentials are saved."""
        username, password = self.get_credentials()
        return bool(username and password)

    def clear_credentials(self):
        """Clear all saved credentials."""
        try:
            keyring.delete_password(self.app_name, "tos_username")
            keyring.delete_password(self.app_name, "tos_password")

            # Remove backup file
            backup_path = os.path.join(os.path.expanduser('~'), '.deltamonbackup')
            if os.path.exists(backup_path):
                os.remove(backup_path)

            return True
        except Exception as e:
            print(f"Error clearing credentials: {e}")
            return False