def extract_vocabulary(lyrics: str) -> list:
    """
    Extracts unique vocabulary words from the provided lyrics.

    Args:
        lyrics (str): The lyrics of the song.

    Returns:
        list: A list of unique vocabulary words found in the lyrics.
    """
    # Normalize the lyrics by converting to lowercase and removing punctuation
    normalized_lyrics = ''.join(char.lower() if char.isalnum() or char.isspace() else ' ' for char in lyrics)
    
    # Split the lyrics into words and create a set to get unique words
    vocabulary_set = set(normalized_lyrics.split())
    
    # Convert the set back to a list and sort it
    vocabulary_list = sorted(list(vocabulary_set))
    
    return vocabulary_list