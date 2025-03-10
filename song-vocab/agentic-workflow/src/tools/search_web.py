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
    retry_delay = 2  # Reduced from 5 to speed up searches
    timeout = 10  # Add timeout for faster failures
    
    print(f"\nSearching for lyrics: '{song}' by '{artist}'")
    
    # Try direct approach first with stricter validation
    lyrics, url = get_lyrics_with_fallback(song, artist)
    if lyrics and url:
        print(f"Found lyrics directly at: {url}")
        return [url]
    
    # Fix common misspellings before searching
    artist = artist.lower().replace('roling', 'rolling')
    
    # If direct approach fails, try search with variants
    variants = get_alternate_titles(song, artist)
    artist_variants = clean_artist_name(artist)
    
    # Try well-known lyrics sites first
    known_sites = [
        'azlyrics.com',
        'genius.com',
        'metrolyrics.com',
        'lyrics.com'
    ]
    
    for site in known_sites:
        try:
            print(f"Trying site: {site}")
            query = f'site:{site} "{song}" "{artist}" lyrics'
            ddgs = DDGS()
            results = list(ddgs.text(query, max_results=3))
            
            if results:
                valid_urls = []
                for result in results:
                    if 'link' not in result:
                        continue
                    url = result['link']
                    print(f"Checking URL: {url}")
                    content = get_page_content(url)
                    if content and is_correct_song_page(content, song, artist):
                        lyrics = extract_lyrics_from_html(content)
                        if lyrics and validate_lyrics_content(lyrics, song, artist, content):
                            print(f"Found valid lyrics at: {url}")
                            return [url]
                            
        except Exception as e:
            print(f"Error searching {site}: {e}")
            continue
    
    # General search as fallback
    for artist_name in artist_variants:
        for song_variant in variants:
            query = f'"{song_variant}" "{artist_name}" lyrics'
            print(f"Trying general search: {query}")
            
            try:
                ddgs = DDGS()
                results = list(ddgs.text(query, max_results=5))
                
                if results:
                    valid_urls = []
                    for result in results:
                        if 'link' not in result:
                            continue
                        url = result['link']
                        print(f"Checking URL: {url}")
                        content = get_page_content(url)
                        if content and is_correct_song_page(content, song, artist):
                            lyrics = extract_lyrics_from_html(content)
                            if lyrics and validate_lyrics_content(lyrics, song, artist, content):
                                print(f"Found valid lyrics at: {url}")
                                return [url]
                
            except Exception as e:
                print(f"Error in general search: {e}")
                continue
    
    print("No valid lyrics found in search")
    return []  # Return empty list instead of raising an exception