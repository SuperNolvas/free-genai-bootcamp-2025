from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from tools.extract_vocabulary import extract_vocabulary
from tools.get_page_content import get_page_content
from tools.search_web import search_lyrics

router = APIRouter()

class MessageRequest(BaseModel):
    message_request: str

@router.post("/api/agent")
async def get_lyrics(request: MessageRequest):
    try:
        search_results = search_lyrics(request.message_request)
        if not search_results:
            raise HTTPException(status_code=404, detail="No lyrics found.")

        lyrics = get_page_content(search_results[0])  # Assuming the first result is the best
        vocabulary = extract_vocabulary(lyrics)

        return {"lyrics": lyrics, "vocabulary": vocabulary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))