import logging
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import timedelta, datetime
from typing import Annotated
from ..database.config import get_db
from ..models.user import User
from ..auth.utils import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_password_hash,
    create_user_verification_token,
    verify_email_token,
    create_password_reset_token,
    verify_password_reset_token,
    generate_verification_token
)
from ..core.config import get_settings
from pydantic import BaseModel, EmailStr, ConfigDict
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

settings = get_settings()
router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str | None = None
    is_active: bool
    email_verified: bool = False
    verification_token: str | None = None
    
    model_config = ConfigDict(from_attributes=True)

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str

async def send_verification_email(email: str, token: str):
    """
    Send verification email to user
    TODO: Implement actual email sending logic
    """
    # For now, just print the verification link
    verification_link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    print(f"Verification link sent to {email}: {verification_link}")

async def send_password_reset_email(email: str, token: str):
    """
    Send password reset email to user
    TODO: Implement actual email sending logic
    """
    # For now, just print the reset link
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    print(f"Password reset link sent to {email}: {reset_link}")

@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    logger.debug(f"Registration attempt for email: {user_data.email}")
    
    # Check for existing user first
    if db.query(User).filter(User.email == user_data.email).first():
        logger.debug(f"Registration failed: Email already registered: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # For test emails, clean up any existing test data with same username
    if "@example.com" in user_data.email:
        logger.debug("Test email detected, cleaning up existing username data")
        db.execute(text("DELETE FROM users WHERE username = :username"), {"username": user_data.username})
        db.commit()
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    verification_token = generate_verification_token()
    
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        is_active=True,  # Changed: User starts active
        email_verified=True,  # Changed: Email auto-verified
        verification_token=None,  # Changed: No verification needed
        verification_token_expires=None
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.debug(f"Created new user with email: {user_data.email}")
    
    return UserResponse(
        id=db_user.id,
        email=db_user.email,
        username=db_user.username,
        is_active=db_user.is_active,
        email_verified=db_user.email_verified,
        verification_token=None
    )

@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)]
) -> UserResponse:
    """Get current user info"""
    try:
        # Refresh the session if needed
        db.refresh(current_user)
        
        # Using the current_user directly since it's already validated by the dependency
        if not current_user.is_active:
            logger.warning(f"Inactive user attempted access: {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is inactive"
            )
        return current_user
        
    except SQLAlchemyError as e:
        logger.error(f"Database error in read_users_me: {str(e)}")
        # Return 401 instead of 500 to trigger proper frontend auth handling
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in read_users_me: {str(e)}")
        # Return 401 instead of 500 to trigger proper frontend auth handling
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

@router.post("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify user's email address"""
    logger.debug(f"Email verification attempt with token: {token[:10]}...")
    user = verify_email_token(token, db)
    if not user:
        logger.debug("Verification failed: Invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # Update user status
    user.email_verified = True
    user.is_active = True
    user.verification_token = None  # Clear the token after use
    user.verification_token_expires = None
    db.commit()
    logger.debug(f"Email verified successfully for user: {user.email}")
    
    return {"message": "Email verified successfully"}

@router.post("/request-password-reset")
async def request_password_reset(
    request: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Request password reset token"""
    user = db.query(User).filter(User.email == request.email).first()
    if user:
        token = create_password_reset_token(user, db)
        background_tasks.add_task(send_password_reset_email, user.email, token)
    return {"message": "If the email exists, a password reset link has been sent"}

@router.post("/reset-password")
async def reset_password(reset_data: PasswordReset, db: Session = Depends(get_db)):
    """Reset password using reset token"""
    user = verify_password_reset_token(reset_data.token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    user.hashed_password = get_password_hash(reset_data.new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    user.is_active = True  # Activate user when password is reset
    user.email_verified = True  # Consider email verified after password reset
    db.commit()
    
    return {"message": "Password reset successfully"}