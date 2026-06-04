import hashlib

from fastapi import Request


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


def is_logged_in(request: Request) -> bool:
    return bool(request.session.get("user"))
