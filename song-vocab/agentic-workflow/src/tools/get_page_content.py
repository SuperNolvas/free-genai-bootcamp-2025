import requests
from bs4 import BeautifulSoup

def get_page_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching page content: {e}")
        return None

def extract_lyrics_from_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    lyrics_div = soup.find('div', class_='lyrics')  # Adjust the selector based on the actual HTML structure
    if lyrics_div:
        return lyrics_div.get_text(strip=True)
    return None