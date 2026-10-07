import os
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt

# Secret key to sign the JWT token.
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "my-super-secret-key-change-this-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def get_password_hash(password: str) -> str:
    """
    Takes a plain text password and returns a scrambled (hashed) version.
    This ensures we don't save real passwords in the database.
    """
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_bytes.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Checks if a plain text password (typed during login) matches 
    the scrambled (hashed) password saved in the database.
    """
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Creates a new JWT digital ID card (token) for the user.
    It packs the user's data (like email) inside, adds an expiration date, 
    and locks it with our SECRET_KEY so it can't be tampered with.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict | None:
    """
    Reads a user's JWT digital ID card (token).
    It checks the signature with our SECRET_KEY and makes sure it hasn't expired.
    If valid, it returns the data inside (like the user's email). If invalid, it returns None.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
