from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.tools.extract_vocabulary import extract_vocabulary
from src.tools.get_page_content import get_page_content, extract_lyrics_from_html, get_lyrics_with_fallback
from src.tools.search_web import search_lyrics
from src.tools.bedrock_client import process_with_bedrock

router = APIRouter()

class MessageRequest(BaseModel):
    message_request: str

@router.post("/api/agent")
async def get_lyrics(request: MessageRequest):
    try:
        parts = request.message_request.split(" by ")
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="Please format request as 'Song Title by Artist Name'")
        
        return await process_song_request(parts[0].strip(), parts[1].strip())
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/agent/{song}/{artist}")
async def get_lyrics_by_url(song: str, artist: str):
    try:
        # First try direct URL approach
        lyrics, url = get_lyrics_with_fallback(song, artist)
        
        # If direct approach fails, try search
        if not lyrics:
            search_results = search_lyrics(song, artist)
            if search_results:
                page_content = get_page_content(search_results[0])
                if page_content:
                    lyrics = extract_lyrics_from_html(page_content)
        
        if not lyrics:
            return {
                "error": "Lyrics not found",
                "message": f"Could not find lyrics for '{song}' by {artist}. Please check the song title and artist name.",
                "status": 404
            }
            
        # Process lyrics with Bedrock and handle potential failures
        processed_lyrics = process_with_bedrock(lyrics)
        if not processed_lyrics or len(processed_lyrics.strip()) < 10:  # Basic validation
            processed_lyrics = lyrics  # Fallback to original if processing failed
            
        # Clean up lyrics by removing empty lines and normalizing whitespace
        cleaned_lyrics = "\n".join(
            line.strip() for line in processed_lyrics.split("\n") 
            if line.strip()
        )
        
        # Extract vocabulary from cleaned lyrics
        vocabulary = extract_vocabulary(cleaned_lyrics)
        return {
            "lyrics": cleaned_lyrics,
            "vocabulary": vocabulary,
            "note": "Original lyrics shown" if processed_lyrics == lyrics else None
        }
    except Exception as e:
        return {
            "error": "Internal server error",
            "message": str(e),
            "status": 500
        }

async def process_song_request(song: str, artist: str):
    """Common processing logic for both POST and GET endpoints"""
    try:
        # First try direct URL approach
        lyrics, url = get_lyrics_with_fallback(song, artist)
        
        # If direct approach fails, try search
        if not lyrics:
            search_results = search_lyrics(song, artist)
            page_content = get_page_content(search_results[0])
            if page_content:
                lyrics = extract_lyrics_from_html(page_content)
        
        if not lyrics:
            raise HTTPException(status_code=404, detail=f"Could not find lyrics for {song} by {artist}")

        # Process lyrics with Bedrock and handle potential failures
        processed_lyrics = process_with_bedrock(lyrics)
        if not processed_lyrics or len(processed_lyrics.strip()) < 10:  # Basic validation
            processed_lyrics = lyrics  # Fallback to original if processing failed
            
        # Clean up lyrics by removing empty lines and normalizing whitespace
        cleaned_lyrics = "\n".join(
            line.strip() for line in processed_lyrics.split("\n") 
            if line.strip()
        )
        
        # Extract vocabulary from cleaned lyrics
        vocabulary = extract_vocabulary(cleaned_lyrics)

        return {
            "lyrics": cleaned_lyrics,
            "vocabulary": vocabulary,
            "note": "Original lyrics shown" if processed_lyrics == lyrics else None
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")