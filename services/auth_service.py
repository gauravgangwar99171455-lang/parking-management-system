"""
ParkSmart Pro — Authentication & Authorization Service
TQM Quality Attribute: Security & Accountability (ISO/IEC 25010)
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple, List
from database.connection import get_db_connection, verify_password, hash_password
from models.user import User, Role
from utils.logger import get_logger
from config import MAX_LOGIN_ATTEMPTS, LOCKOUT_TIME_SECONDS

logger = get_logger("auth_service")

class AuthService:
    def __init__(self):
        self._current_user: Optional[User] = None

    @property
    def current_user(self) -> Optional[User]:
        return self._current_user

    def set_current_user(self, user: Optional[User]) -> None:
        self._current_user = user

    def authenticate(self, username: str, password: str) -> Tuple[bool, Optional[User], str]:
        """
        Authenticate user with username and password.
        Implements lockout protection against brute-force attacks.
        """
        if not username or not password:
            return False, None, "Username and password are required."

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT u.id, u.username, u.password_hash, u.salt, u.full_name,
                       u.role_id, r.name as role_name, u.is_active,
                       u.failed_attempts, u.locked_until, u.last_login, u.created_at
                FROM users u
                JOIN roles r ON u.role_id = r.id
                WHERE u.username = ?
            """, (username.strip(),))
            row = cur.fetchone()

            if not row:
                logger.warning(f"Failed login attempt for non-existent user '{username}'")
                return False, None, "Invalid username or password."

            if not row["is_active"]:
                logger.warning(f"Login rejected: Account '{username}' is disabled")
                return False, None, "Account is disabled. Please contact an administrator."

            # Check Lockout status
            locked_until_str = row["locked_until"]
            if locked_until_str:
                try:
                    locked_until = datetime.strptime(locked_until_str, "%Y-%m-%d %H:%M:%S")
                    if datetime.now() < locked_until:
                        remaining = int((locked_until - datetime.now()).total_seconds())
                        return False, None, f"Account locked due to multiple failed attempts. Try again in {remaining}s."
                except ValueError:
                    pass

            # Verify password
            is_valid = verify_password(password, row["salt"], row["password_hash"])
            if not is_valid:
                new_attempts = row["failed_attempts"] + 1
                locked_until_val = None
                msg = "Invalid username or password."
                if new_attempts >= MAX_LOGIN_ATTEMPTS:
                    lock_time = datetime.now() + timedelta(seconds=LOCKOUT_TIME_SECONDS)
                    locked_until_val = lock_time.strftime("%Y-%m-%d %H:%M:%S")
                    msg = f"Account locked for {LOCKOUT_TIME_SECONDS // 60} minutes due to {new_attempts} failed attempts."
                    logger.warning(f"User '{username}' locked out until {locked_until_val}")

                cur.execute("""
                    UPDATE users
                    SET failed_attempts = ?, locked_until = ?, updated_at = DATETIME('now', 'localtime')
                    WHERE id = ?
                """, (new_attempts, locked_until_val, row["id"]))
                conn.commit()
                return False, None, msg

            # Successful login: reset failed attempts, update last_login
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur.execute("""
                UPDATE users
                SET failed_attempts = 0, locked_until = NULL, last_login = ?, updated_at = DATETIME('now', 'localtime')
                WHERE id = ?
            """, (now_str, row["id"]))
            conn.commit()

            user = User.from_row(row)
            self._current_user = user
            logger.info(f"User '{username}' ({user.role_name}) logged in successfully.")
            return True, user, "Login successful."
        finally:
            conn.close()

    def logout(self) -> None:
        if self._current_user:
            logger.info(f"User '{self._current_user.username}' logged out.")
        self._current_user = None

    def get_all_users(self) -> List[User]:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT u.id, u.username, u.full_name, u.role_id, r.name as role_name,
                       u.is_active, u.last_login, u.created_at
                FROM users u
                JOIN roles r ON u.role_id = r.id
                ORDER BY u.id ASC
            """)
            return [User.from_row(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def create_user(self, username: str, password: str, full_name: str, role_name: str) -> Tuple[bool, str]:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id FROM roles WHERE name = ?", (role_name,))
            role_row = cur.fetchone()
            if not role_row:
                return False, f"Invalid role: '{role_name}'."

            pwd_hash, salt = hash_password(password)
            cur.execute("""
                INSERT INTO users (username, password_hash, salt, full_name, role_id)
                VALUES (?, ?, ?, ?, ?)
            """, (username.strip(), pwd_hash, salt, full_name.strip(), role_row["id"]))
            conn.commit()
            return True, f"User '{username}' created successfully."
        except Exception as e:
            conn.rollback()
            if "UNIQUE constraint failed" in str(e):
                return False, f"Username '{username}' already exists."
            return False, f"Failed to create user: {str(e)}"
        finally:
            conn.close()

    def toggle_user_active(self, user_id: int) -> Tuple[bool, str]:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT is_active, username FROM users WHERE id = ?", (user_id,))
            row = cur.fetchone()
            if not row:
                return False, "User not found."
            new_status = 0 if row["is_active"] else 1
            cur.execute("UPDATE users SET is_active = ?, updated_at = DATETIME('now', 'localtime') WHERE id = ?", (new_status, user_id))
            conn.commit()
            state = "activated" if new_status else "deactivated"
            return True, f"User '{row['username']}' {state}."
        finally:
            conn.close()

auth_service = AuthService()
