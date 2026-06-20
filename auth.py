"""User accounts and sessions for QuestGen.

Pure standard-library implementation: SQLite for storage, PBKDF2-HMAC for
password hashing, and signed-random tokens for sessions. No external
dependencies and no JavaScript involved.
"""

from __future__ import annotations

import hashlib
import os
import re
import secrets
import sqlite3
import time
from typing import Any

DB_PATH = os.path.join(os.path.dirname(__file__), "questgen.db")

# Tunables for password hashing.
_PBKDF2_ROUNDS = 200_000
_SALT_BYTES = 16

# Session lifetime (7 days) and in-memory session store: token -> session dict.
SESSION_TTL_SECONDS = 7 * 24 * 60 * 60
_SESSIONS: dict[str, dict[str, Any]] = {}

USERNAME_RE = re.compile(r"^[A-Za-z0-9_.]{3,24}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AuthError(Exception):
    """Raised when signup/login validation fails; message is user-facing."""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                created_at REAL NOT NULL
            )
            """
        )


def hash_password(password: str) -> str:
    salt = os.urandom(_SALT_BYTES)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ROUNDS)
    return f"{salt.hex()}${derived.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, hash_hex = stored.split("$", 1)
        salt = bytes.fromhex(salt_hex)
    except (ValueError, TypeError):
        return False
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ROUNDS)
    return secrets.compare_digest(derived.hex(), hash_hex)


def create_user(username: str, email: str, password: str, confirm: str) -> dict[str, Any]:
    username = (username or "").strip()
    email = (email or "").strip().lower()

    if not USERNAME_RE.match(username):
        raise AuthError("Username must be 3-24 characters: letters, numbers, dot or underscore.")
    if not EMAIL_RE.match(email):
        raise AuthError("Please enter a valid email address.")
    if len(password) < 6:
        raise AuthError("Password must be at least 6 characters long.")
    if password != confirm:
        raise AuthError("Passwords do not match.")

    try:
        with _connect() as conn:
            cursor = conn.execute(
                "INSERT INTO users (username, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (username, email, hash_password(password), time.time()),
            )
            user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        # Figure out which field collided for a clearer message.
        with _connect() as conn:
            if conn.execute("SELECT 1 FROM users WHERE username = ? COLLATE NOCASE", (username,)).fetchone():
                raise AuthError("That username is already taken.")
        raise AuthError("An account with that email already exists.")

    return {"id": user_id, "username": username, "email": email}


def authenticate(identifier: str, password: str) -> dict[str, Any]:
    identifier = (identifier or "").strip()
    if not identifier or not password:
        raise AuthError("Please enter your credentials.")

    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ? COLLATE NOCASE OR email = ? COLLATE NOCASE",
            (identifier, identifier.lower()),
        ).fetchone()

    if row is None or not verify_password(password, row["password_hash"]):
        raise AuthError("Invalid username/email or password.")

    return {"id": row["id"], "username": row["username"], "email": row["email"]}


def create_session(user: dict[str, Any]) -> str:
    token = secrets.token_urlsafe(32)
    _SESSIONS[token] = {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "expires_at": time.time() + SESSION_TTL_SECONDS,
    }
    return token


def get_session(token: str | None) -> dict[str, Any] | None:
    if not token:
        return None
    session = _SESSIONS.get(token)
    if session is None:
        return None
    if session["expires_at"] < time.time():
        _SESSIONS.pop(token, None)
        return None
    return session


def destroy_session(token: str | None) -> None:
    if token:
        _SESSIONS.pop(token, None)
