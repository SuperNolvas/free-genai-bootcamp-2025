import logging
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt, ExpiredSignatureError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from ..database.config import get_db
from ..models.user import User
from ..core.config import get_settings
import secrets

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    logger.debug(f"Attempting to authenticate user: {email}")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        logger.debug(f"No user found with email: {email}")
        return None
    if not verify_password(password, user.hashed_password):
        logger.debug("Password verification failed")
        return None
    if not user.is_active:
        logger.debug(f"User {email} is not active")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is not active",
            headers={"WWW-Authenticate": "Bearer"},
        )
    logger.debug(f"Successfully authenticated user: {email}")
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def authenticate_websocket_user(token: str, db: Session) -> Optional[User]:
    """Authenticate a WebSocket connection using a JWT token"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
            
        user = db.query(User).filter(User.email == email).first()
        if user is None or not user.is_active:
            return None
            
        return user
    except (JWTError, ExpiredSignatureError):
        return None

def generate_verification_token() -> str:
    """Generate a secure verification token"""
    return secrets.token_urlsafe(32)

def create_verification_token() -> str:
    """Generate a verification token without database persistence"""
    return generate_verification_token()

def create_user_verification_token(user: User, db: Session) -> str:
    """Create and store email verification token"""
    logger.debug(f"Creating verification token for user: {user.email}")
    token = secrets.token_urlsafe(32)
    user.verification_token = token
    user.verification_token_expires = datetime.utcnow() + timedelta(hours=24)
    db.commit()
    logger.debug(f"Verification token created and stored for user: {user.email}")
    return token  # Return token after commit

def verify_email_token(token: str, db: Session) -> Optional[User]:
    """Verify email verification token and activate user if valid"""
    logger.debug(f"Verifying email token: {token[:10]}...")
    user = db.query(User).filter(
        User.verification_token == token,
        User.verification_token_expires > datetime.utcnow()
    ).first()
    
    if not user:
        logger.debug("No user found with provided verification token")
        return None

    logger.debug(f"Found user {user.email} for verification token")
    return user

def create_password_reset_token(user: User, db: Session) -> str:
    """Create and store password reset token"""
    token = generate_verification_token()
    user.password_reset_token = token
    user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
    db.commit()
    return token

def verify_password_reset_token(token: str, db: Session) -> Optional[User]:
    """Verify password reset token"""
    return db.query(User).filter(
        User.password_reset_token == token,
        User.password_reset_expires > datetime.utcnow()
    ).first()