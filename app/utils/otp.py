import secrets

def generate_otp(length: int = 6) -> str:
    """Cryptographically secure numeric OTP (6 digits by default)."""
    
    return "".join(secrets.choice("0123456789") for _ in range(length))
