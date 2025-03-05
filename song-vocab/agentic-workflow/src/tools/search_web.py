from duckduckgo_search import DDGS
import time
from fastapi import HTTPException
from .get_page_content import (
    get_lyrics_with_fallback, 
    get_alternate_titles,
    get_page_content,
    extract_lyrics_from_html,
    validate_lyrics_content,
    clean_artist_name,
    is_correct_song_page
)

def search_lyrics(song: str, artist: str):
    max_retries = 2
    retry_delay = 5
    
    # Try direct approach first with stricter validation
    lyrics, url = get_lyrics_with_fallback(song, artist)
    if lyrics and url:
        return [url]
    
    # If direct approach fails, try search with variants
    variants = get_alternate_titles(song, artist)
    artist_variants = clean_artist_name(artist)
    
    for artist_name in artist_variants:
        for song_variant in variants:
            # Try exact match search first
            query = f'"{song_variant}" "{artist_name}" lyrics'
            
            for attempt in range(max_retries):
                try:
                    ddgs = DDGS()
                    results = list(ddgs.text(query, max_results=5))
                    
                    if results:
                        # Try each result with strict validation
                        for result in results:
                            if 'link' not in result:
                                continue
                                
                            url = result['link']
                            content = get_page_content(url)
                            
                            # First check if it's the right song page
                            if not content or not is_correct_song_page(content, song, artist):
                                continue
                                
                            lyrics = extract_lyrics_from_html(content)
                            if lyrics and validate_lyrics_content(lyrics, song, artist, content):
                                return [url]
                    
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                        
                except Exception as e:
                    if "Ratelimit" in str(e):
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay * (attempt + 1))
                            continue
                    else:
                        print(f"Search error: {e}")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            continue
    
    # If all attempts fail, try one last time with a site-specific search
    lyrics_sites = ['genius.com', 'azlyrics.com', 'lyrics.com']
    for site in lyrics_sites:
        try:
            query = f'site:{site} "{song}" "{artist}" lyrics'
            ddgs = DDGS()
            results = list(ddgs.text(query, max_results=3))
            
            for result in results:
                if 'link' not in result:
                    continue
                    
                url = result['link']
                content = get_page_content(url)
                if not content or not is_correct_song_page(content, song, artist):
                    continue
                    
                lyrics = extract_lyrics_from_html(content)
                if lyrics and validate_lyrics_content(lyrics, song, artist, content):
                    return [url]
                    
        except Exception:
            continue
    
    raise HTTPException(
        status_code=404,
        detail=f"Could not find verified lyrics for '{song}' by {artist}. Please check the song name or try again later."
    )