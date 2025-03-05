# Agentic Workflow

This project is designed to create an agentic workflow that retrieves song lyrics from the internet, extracts vocabulary, and stores it in a local database. The application utilizes FastAPI for the web framework, integrates with the Ollama Python SDK for language model processing, and employs SQLite3 for database management.

## Project Structure

```
agentic-workflow
├── src
│   ├── main.py             # Entry point of the FastAPI application
│   ├── api
│   │   └── agent.py        # API endpoint for getting lyrics
│   ├── tools
│   │   ├── extract_vocabulary.py  # Functions to extract vocabulary from lyrics
│   │   ├── get_page_content.py    # Functions to retrieve webpage content
│   │   └── search_web.py           # Functions to perform web searches
│   └── models
│       └── __init__.py     # Data models or schemas for the application
├── requirements.txt         # Project dependencies
├── README.md                # Project documentation
└── config.py                # Configuration settings
```

## Installation

To set up the project, clone the repository and install the required dependencies:

```bash
git clone <repository-url>
cd agentic-workflow
pip install -r requirements.txt
```

## Usage

1. Start the FastAPI application:

```bash
uvicorn src.main:app --reload
```

2. Use the `/api/agent` endpoint to retrieve lyrics and vocabulary. Send a POST request with the following JSON body:

```json
{
  "message_request": "Song Title by Artist"
}
```

3. The response will include the lyrics and a list of vocabulary words extracted from the lyrics:

```json
{
  "lyrics": "Full lyrics of the song...",
  "vocabulary": ["word1", "word2", "word3"]
}
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.