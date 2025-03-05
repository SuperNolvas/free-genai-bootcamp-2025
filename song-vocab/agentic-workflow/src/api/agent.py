from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..tools.extract_vocabulary import extract_vocabulary
from ..tools.get_page_content import get_page_content, extract_lyrics_from_html
from ..tools.search_web import search_lyrics
from ..tools.bedrock_client import process_with_bedrock

router = APIRouter()

class MessageRequest(BaseModel):
    message_request: str

@router.post("/api/agent")
async def get_lyrics(request: MessageRequest):
    try:
        # Split song and artist from request
        parts = request.message_request.split(" by ")
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="Please format request as 'Song Title by Artist Name'")
        
        song, artist = parts[0].strip(), parts[1].strip()
        
        # Search for lyrics
        search_results = search_lyrics(song, artist)
        if not search_results:
            raise HTTPException(status_code=404, detail="No lyrics found.")

        # Get page content and extract lyrics
        page_content = get_page_content(search_results[0])
        if not page_content:
            raise HTTPException(status_code=404, detail="Could not fetch lyrics content.")
            
        lyrics = extract_lyrics_from_html(page_content)
        if not lyrics:
            raise HTTPException(status_code=404, detail="Could not extract lyrics from page.")

        # Process lyrics with Bedrock
        processed_lyrics = process_with_bedrock(lyrics)
        
        # Extract vocabulary from processed lyrics
        vocabulary = extract_vocabulary(processed_lyrics)

        return {"lyrics": processed_lyrics, "vocabulary": vocabulary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/agent/{song}/{artist}")
async def get_lyrics_by_url(song: str, artist: str):
    try:
        message = f"{song} by {artist}"
        
        # Search for lyrics
        search_results = search_lyrics(song, artist)
        if not search_results:
            raise HTTPException(status_code=404, detail="No lyrics found.")

        # Get page content and extract lyrics
        page_content = get_page_content(search_results[0])
        if not page_content:
            raise HTTPException(status_code=404, detail="Could not fetch lyrics content.")
            
        lyrics = extract_lyrics_from_html(page_content)
        if not lyrics:
            raise HTTPException(status_code=404, detail="Could not extract lyrics from page.")

        # Process lyrics with Bedrock
        processed_lyrics = process_with_bedrock(lyrics)
        
        # Extract vocabulary from processed lyrics
        vocabulary = extract_vocabulary(processed_lyrics)

        return {"lyrics": processed_lyrics, "vocabulary": vocabulary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))