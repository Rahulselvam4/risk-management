# backend/auth.py
import os
import jwt
import datetime
import bcrypt
import logging
from dotenv import load_dotenv

# Initialize logging
logger = logging.getLogger("AuthService")

# Load environment variables from .env file
load_dotenv()

# --- ENTERPRISE SECURITY CONFIGURATION ---
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    # Fail-fast: Never allow the app to start without a cryptographic key
    raise ValueError("CRITICAL: JWT_SECRET_KEY environment variable is not set. Cannot start server securely.")

ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# Safely parse the expiration time, defaulting to 30 minutes if malformed
try:
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
except ValueError:
    logger.warning("Invalid ACCESS_TOKEN_EXPIRE_MINUTES in .env. Defaulting to 30 minutes.")
    ACCESS_TOKEN_EXPIRE_MINUTES = 30


def get_password_hash(password: str) -> str:
    """Scrambles a plain text password into a secure bcrypt hash."""
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Checks if the typed password matches the scrambled hash in the database."""
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_password_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_password_bytes)
    except Exception as e:
        logger.error("Error during password verification.")
        return False


def create_access_token(data: dict) -> str:
    """Mints a secure, time-limited JSON Web Token (JWT)."""
    to_encode = data.copy()
    
    # Use timezone-aware UTC datetime (modern Python standard)
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt  