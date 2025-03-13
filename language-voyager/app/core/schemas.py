from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel

T = TypeVar('T')

class ErrorModel(BaseModel):
    code: str
    message: str
    details: Optional[str] = None

class ResponseModel(BaseModel, Generic[T]):
    success: bool
    message: str
    data: Optional[T] = None
    errors: Optional[List[ErrorModel]] = None