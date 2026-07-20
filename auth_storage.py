"""
SATRIA SE2026 — Auth storage: user accounts (register/login/profile)
Badan Pusat Statistik Kabupaten Bangkalan
"""

from werkzeug.security import generate_password_hash, check_password_hash
from db_config import get_connection, execute_query


class AuthStorage:
    def __init__(self):
        self._ensure_schema()
        print("[✓] AuthStorage initialized (users table ready)")

    def _ensure_schema(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(150) NOT NULL,
                email VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                instansi VARCHAR(255) NULL,
                profile_photo TEXT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login_at DATETIME NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        # Add profile_photo column if it doesn't exist (for existing databases)
        try:
            cursor.execute("""
                ALTER TABLE users ADD COLUMN profile_photo MEDIUMTEXT NULL
            """)
            conn.commit()
        except Exception:
            # Column already exists — make sure it's wide enough for a
            # base64 photo (TEXT tops out at ~64KB, which a raw upload can
            # exceed even after client-side resizing on a bad day).
            try:
                cursor.execute("""
                    ALTER TABLE users MODIFY COLUMN profile_photo MEDIUMTEXT NULL
                """)
                conn.commit()
            except Exception:
                pass
        conn.commit()
        cursor.close()
        conn.close()

    def get_by_email(self, email):
        rows = execute_query(
            "SELECT * FROM users WHERE email = %s", (email.strip().lower(),), fetch=True
        )
        return rows[0] if rows else None

    def get_by_id(self, user_id):
        rows = execute_query("SELECT * FROM users WHERE id = %s", (user_id,), fetch=True)
        return rows[0] if rows else None

    def create_user(self, name, email, password, instansi=None):
        email = email.strip().lower()
        password_hash = generate_password_hash(password)
        query = """
            INSERT INTO users (name, email, password_hash, instansi)
            VALUES (%s, %s, %s, %s)
        """
        user_id = execute_query(
            query, (name.strip(), email, password_hash, (instansi or '').strip() or None)
        )
        return self.get_by_id(user_id)

    def verify_password(self, user, password):
        return check_password_hash(user['password_hash'], password)

    def touch_last_login(self, user_id):
        execute_query("UPDATE users SET last_login_at = NOW() WHERE id = %s", (user_id,))

    def update_profile(self, user_id, name, instansi):
        execute_query(
            "UPDATE users SET name = %s, instansi = %s WHERE id = %s",
            (name.strip(), (instansi or '').strip() or None, user_id),
        )

    def update_password(self, user_id, new_password):
        execute_query(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (generate_password_hash(new_password), user_id),
        )

    def update_profile_photo(self, user_id, photo_base64):
        """Update user profile photo (base64 encoded)"""
        execute_query(
            "UPDATE users SET profile_photo = %s WHERE id = %s",
            (photo_base64, user_id),
        )
