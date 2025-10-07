from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
import hashlib
import secrets
from app.core.config import settings

def verify_password(plain_password: str, stored_password: str, is_admin: bool = False) -> bool:
    """Verify a password against stored password (hashed for admin, plaintext for others)."""
    if is_admin:
        # For admin users, verify against SHA-256 hash with salt
        return verify_admin_password(plain_password, stored_password)
    else:
        # For non-admin users, simple plaintext comparison
        return plain_password == stored_password

def get_password_hash(password: str, is_admin: bool = False) -> str:
    """Generate password hash for admin or return plaintext for others."""
    if is_admin:
        # For admin users, use SHA-256 with salt (simpler than bcrypt)
        return hash_admin_password(password)
    else:
        # For non-admin users, store as plaintext
        return password

def hash_admin_password(password: str) -> str:
    """Hash admin password using SHA-256 with random salt."""
    # Generate a random salt
    salt = secrets.token_hex(16)
    # Create hash with salt
    pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    # Store as salt:hash format
    return f"{salt}:{pwd_hash}"

def verify_admin_password(password: str, stored_hash: str) -> bool:
    """Verify admin password against stored hash."""
    try:
        # Split stored hash into salt and hash
        salt, stored_pwd_hash = stored_hash.split(':', 1)
        # Hash the provided password with the same salt
        pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        # Compare hashes
        return pwd_hash == stored_pwd_hash
    except ValueError:
        # If stored_hash doesn't contain ':', it might be an old format
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """Verify and decode token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None