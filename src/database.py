
import sqlite3
import os
import hashlib
import hmac
from pathlib import Path


# ---------------- PROJECT PATHS ----------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_PATH = DATA_DIR / "facevault.db"


# ---------------- DATABASE CONNECTION ----------------

def get_connection():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


# ---------------- DATABASE INITIALIZATION ----------------

def initialize_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_salt BLOB NOT NULL,
                password_hash BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS vault_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                original_name TEXT NOT NULL,
                encrypted_path TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        columns = connection.execute(
            "PRAGMA table_info(users)"
        ).fetchall()

        if "face_embedding" not in {
            column["name"] for column in columns
        }:
            connection.execute("""
                ALTER TABLE users ADD COLUMN face_embedding BLOB
            """)


# ---------------- PASSWORD SECURITY ----------------

def hash_password(password, salt):
    return hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=2**14,
        r=8,
        p=1,
        dklen=32,
    )


def verify_user_password(user_id, password):
    with get_connection() as connection:
        user = connection.execute(
            """
            SELECT password_salt, password_hash
            FROM users WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

    if user is None:
        return False

    candidate = hash_password(password, user["password_salt"])
    return hmac.compare_digest(candidate, user["password_hash"])


def change_user_password(user_id, new_password):
    if len(new_password) < 8:
        return False, "Password must contain at least 8 characters."

    salt = os.urandom(16)
    password_hash = hash_password(new_password, salt)

    with get_connection() as connection:
        result = connection.execute(
            """
            UPDATE users
            SET password_salt = ?, password_hash = ?
            WHERE id = ?
            """,
            (salt, password_hash, user_id),
        )

        if result.rowcount == 0:
            return False, "User account was not found."

    return True, "Password changed successfully."


# ---------------- USER REGISTRATION / LOGIN ----------------

def register_user(username, password):
    username = username.strip()

    if not username or len(username) > 50:
        return False, "Username must be 1–50 characters."

    if len(password) < 8:
        return False, "Password must contain at least 8 characters."

    salt = os.urandom(16)
    password_hash = hash_password(password, salt)

    try:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO users
                    (username, password_salt, password_hash)
                VALUES (?, ?, ?)
                """,
                (username, salt, password_hash),
            )
        return True, "Account created successfully."

    except sqlite3.IntegrityError:
        return False, "That username already exists."


def login_user(username, password):
    with get_connection() as connection:
        user = connection.execute(
            """
            SELECT id, username, password_salt, password_hash
            FROM users WHERE username = ?
            """,
            (username.strip(),),
        ).fetchone()

    if user is None:
        return None

    candidate = hash_password(password, user["password_salt"])

    if hmac.compare_digest(candidate, user["password_hash"]):
        return {"id": user["id"], "username": user["username"]}

    return None


def get_all_users():
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, username, created_at
            FROM users ORDER BY username COLLATE NOCASE
            """
        ).fetchall()

    return [dict(row) for row in rows]


# ---------------- FACE FEATURE STORAGE ----------------

def save_face_embedding(user_id, embedding):
    if embedding is None:
        return False, "No face features were provided."

    embedding_bytes = bytes(embedding)
    if not embedding_bytes:
        return False, "Face features cannot be empty."

    with get_connection() as connection:
        result = connection.execute(
            """
            UPDATE users SET face_embedding = ?
            WHERE id = ?
            """,
            (sqlite3.Binary(embedding_bytes), user_id),
        )

        if result.rowcount == 0:
            return False, "User account was not found."

    return True, "Face features saved successfully."


def get_face_embedding(user_id):
    with get_connection() as connection:
        user = connection.execute(
            "SELECT face_embedding FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

    if user is None or user["face_embedding"] is None:
        return None

    return bytes(user["face_embedding"])


def get_users_with_faces():
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, username, face_embedding
            FROM users WHERE face_embedding IS NOT NULL
            """
        ).fetchall()

    return [
        {
            "id": row["id"],
            "username": row["username"],
            "face_embedding": bytes(row["face_embedding"]),
        }
        for row in rows
    ]


def delete_face_embedding(user_id):
    with get_connection() as connection:
        result = connection.execute(
            "UPDATE users SET face_embedding = NULL WHERE id = ?",
            (user_id,),
        )

        if result.rowcount == 0:
            return False, "User account was not found."

    return True, "Registered face data removed."


# ---------------- ENCRYPTED FILE RECORDS ----------------

def save_vault_file(user_id, original_name, encrypted_path):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO vault_files
                (user_id, original_name, encrypted_path)
            VALUES (?, ?, ?)
            """,
            (user_id, original_name, encrypted_path),
        )


def get_user_files(user_id):
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT id, original_name, encrypted_path, created_at
            FROM vault_files
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,),
        ).fetchall()


# ---------------- ACCOUNT DELETION ----------------

def delete_user_account(user_id):
    """Delete database records only; never remove encrypted files on disk."""
    with get_connection() as connection:
        exists = connection.execute(
            "SELECT id FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

        if exists is None:
            return False, "User account was not found."

        connection.execute(
            "DELETE FROM vault_files WHERE user_id = ?",
            (user_id,),
        )
        connection.execute(
            "DELETE FROM users WHERE id = ?",
            (user_id,),
        )

    return True, "Account deleted. Encrypted files on disk were kept."


if __name__ == "__main__":
    initialize_database()
    print(f"FaceVault database ready: {DATABASE_PATH}")
