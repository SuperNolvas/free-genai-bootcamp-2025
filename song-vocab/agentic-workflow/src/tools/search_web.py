from duckduckgo_search import DDGS

def search_lyrics(song: str, artist: str):
    query = f"{song} lyrics {artist}"
    ddgs = DDGS()
    results = list(ddgs.text(query, max_results=5))
    links = [result['link'] for result in results if 'link' in result]
    return links