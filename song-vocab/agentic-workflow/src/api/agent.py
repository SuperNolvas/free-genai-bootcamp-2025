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
    print(f"\nReceived request for song: '{song}' by '{artist}'")
    try:
        # First try direct URL approach
        print("Trying direct URL approach...")
        lyrics, url = get_lyrics_with_fallback(song, artist)
        
        # If direct approach fails, try search
        if not lyrics:
            print("Direct URL approach failed, trying search...")
            search_results = search_lyrics(song, artist)
            if search_results:
                print(f"Found {len(search_results)} search results")
                for result in search_results:
                    print(f"Trying URL: {result}")
                    page_content = get_page_content(result)
                    if page_content:
                        lyrics = extract_lyrics_from_html(page_content)
                        if lyrics:
                            print("Successfully extracted lyrics from search result")
                            break
        
        if not lyrics:
            print("No lyrics found through any method")
            return {
                "error": "404",
                "message": f"Could not find verified lyrics for '{song}' by {artist}. Please check the song name or try again later.",
                "status": 404
            }
            
        print("Found lyrics, processing with Bedrock...")
        # Process lyrics with Bedrock and handle potential failures
        try:
            processed_lyrics = process_with_bedrock(lyrics)
            if not processed_lyrics or len(processed_lyrics.strip()) < 10:  # Basic validation
                print("Bedrock processing failed or returned invalid result, using original lyrics")
                processed_lyrics = lyrics  # Fallback to original if processing failed
        except Exception as e:
            print(f"Bedrock processing error: {e}")
            processed_lyrics = lyrics  # Use original lyrics if processing fails
            
        # Clean up lyrics by removing empty lines and normalizing whitespace
        cleaned_lyrics = "\n".join(
            line.strip() for line in processed_lyrics.split("\n") 
            if line.strip()
        )
        
        # Extract vocabulary from cleaned lyrics
        vocabulary = extract_vocabulary(cleaned_lyrics)
        print("Successfully processed lyrics and extracted vocabulary")
        
        return {
            "lyrics": cleaned_lyrics,
            "vocabulary": vocabulary,
            "note": "Original lyrics shown" if processed_lyrics == lyrics else None,
            "status": 200
        }
    except Exception as e:
        print(f"Error processing request: {e}")
        return {
            "error": "500",
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