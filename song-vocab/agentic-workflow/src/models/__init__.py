from pydantic import BaseModel
from typing import List

class LyricsResponse(BaseModel):
    lyrics: str
    vocabulary: List[str]