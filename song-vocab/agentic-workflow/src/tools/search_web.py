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
    
    # For Beatles songs, add specific site searches first
    if any('beatles' in variant.lower() for variant in artist_variants):
        specific_urls = [
            'www.beatleslyrics.com',
            'www.thebeatles.com'
        ]
        for site in specific_urls:
            try:
                query = f'site:{site} "{song}"'
                ddgs = DDGS()
                results = list(ddgs.text(query, max_results=3))
                
                if results and any('link' in r for r in results):
                    return [r['link'] for r in results if 'link' in r]
            except Exception:
                continue
    
    # Try with each artist and song variant
    for artist_name in artist_variants:
        for song_variant in variants:
            # Try both with and without quotes
            queries = [
                f'"{song_variant}" "{artist_name}" lyrics',
                f'{song_variant} {artist_name} lyrics official'
            ]
            
            for query in queries:
                for attempt in range(max_retries):
                    try:
                        ddgs = DDGS()
                        results = list(ddgs.text(query, max_results=5))
                        
                        if results:
                            valid_urls = []
                            for result in results:
                                if 'link' not in result:
                                    continue
                                    
                                url = result['link']
                                content = get_page_content(url)
                                
                                if not content or not is_correct_song_page(content, song, artist):
                                    continue
                                    
                                lyrics = extract_lyrics_from_html(content)
                                if lyrics and validate_lyrics_content(lyrics, song, artist, content):
                                    valid_urls.append(url)
                            
                            if valid_urls:
                                return valid_urls
                        
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                    
                    except Exception as e:
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay * (attempt + 1))
                        continue
    
    # Try site-specific searches as last resort
    lyrics_sites = ['genius.com', 'azlyrics.com', 'lyrics.com', 'metrolyrics.com']
    for site in lyrics_sites:
        try:
            query = f'site:{site} "{song}" "{artist}" lyrics'
            ddgs = DDGS()
            results = list(ddgs.text(query, max_results=3))
            
            valid_urls = []
            for result in results:
                if 'link' not in result:
                    continue
                    
                url = result['link']
                content = get_page_content(url)
                if not content or not is_correct_song_page(content, song, artist):
                    continue
                    
                lyrics = extract_lyrics_from_html(content)
                if lyrics and validate_lyrics_content(lyrics, song, artist, content):
                    valid_urls.append(url)
            
            if valid_urls:
                return valid_urls
                    
        except Exception:
            continue
    
    # Return empty list instead of raising an exception
    return []