"""
ParkSmart Pro — Authentication & Security Automated Tests
"""

import unittest
import tempfile
from pathlib import Path
from database.connection import init_database
from services.auth_service import AuthService
from database.connection import hash_password, verify_password
import config

class TestAuthService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_auth.db"
        config.DB_PATH = self.db_path
        init_database(custom_path=self.db_path, seed_defaults=True)
        self.auth = AuthService()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_salted_hash_verification(self):
        """Verify PBKDF2-HMAC-SHA256 salted hash correctly matches password."""
        h, salt = hash_password("SuperSecret123")
        self.assertTrue(verify_password("SuperSecret123", salt, h))
        self.assertFalse(verify_password("WrongPassword", salt, h))

    def test_successful_login_and_roles(self):
        """Verify default admin login and role extraction."""
        ok, user, msg = self.auth.authenticate("admin", "admin123")
        self.assertTrue(ok)
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "admin")
        self.assertEqual(user.role_name, "admin")
        self.assertTrue(user.is_admin())

    def test_invalid_credentials(self):
        """Verify wrong password returns failure and does not authenticate."""
        ok, user, msg = self.auth.authenticate("admin", "WrongPassword")
        self.assertFalse(ok)
        self.assertIsNone(user)
        self.assertIn("Invalid username or password", msg)

    def test_account_creation_and_deactivation(self):
        """Verify admin can create a user and toggle active status."""
        ok_create, msg = self.auth.create_user("new_operator", "pass1234", "New Operator", "operator")
        self.assertTrue(ok_create, msg)

        # Login with new user
        ok_login, u, _ = self.auth.authenticate("new_operator", "pass1234")
        self.assertTrue(ok_login)

        # Deactivate
        ok_toggle, _ = self.auth.toggle_user_active(u.id)
        self.assertTrue(ok_toggle)

        # Login should now fail
        ok_login2, _, msg2 = self.auth.authenticate("new_operator", "pass1234")
        self.assertFalse(ok_login2)
        self.assertIn("disabled", msg2.lower())

if __name__ == "__main__":
    unittest.main()
