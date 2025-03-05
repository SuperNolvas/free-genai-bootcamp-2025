from duckduckgo_search import ddg

def search_lyrics(song: str, artist: str):
    query = f"{song} lyrics {artist}"
    results = ddg(query, max_results=5)
    links = [result['href'] for result in results if 'href' in result]
    return links