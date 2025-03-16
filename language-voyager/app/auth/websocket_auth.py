from fastapi import WebSocket, HTTPException, status
from starlette.websockets import WebSocketState
from sqlalchemy.orm import Session
from jose import JWTError, jwt, ExpiredSignatureError
from ..models.user import User
from ..core.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

async def authenticate_websocket_user(websocket: WebSocket, db: Session) -> User:
    """Authenticate WebSocket connection and return user"""
    try:
        auth = websocket.headers.get("authorization", "")
        if not auth:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        
        # Handle both "Bearer token" and raw token formats
        token = auth
        if auth.lower().startswith("bearer"):
            token = auth.split(" ")[1]
        
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            email = payload.get("sub")
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials"
                )
        except ExpiredSignatureError:
            logger.warning("WebSocket connection error: Token has expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except JWTError as e:
            logger.error(f"JWT validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )

        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        return user

    except HTTPException:
        # Let the calling code handle HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected WebSocket authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during authentication"
        )