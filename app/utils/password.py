import re
import bcrypt


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)

    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def validate_password(password: str) -> list[str]:
    """Return a list of rule violations. Empty list = valid."""

    errors = []
    if len(password) < 8:
        errors.append("at least 8 characters")

    if not re.search(r"[A-Z]", password):
        errors.append("one uppercase letter")

    if not re.search(r"[a-z]", password):
        errors.append("one lowercase letter")

    if not re.search(r"\d", password):
        errors.append("one digit")

    if not re.search(r"[^A-Za-z0-9]", password):
        errors.append("one special character")
        
    return errors
