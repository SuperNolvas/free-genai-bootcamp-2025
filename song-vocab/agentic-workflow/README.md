# Agentic Workflow

This project is designed to create an agentic workflow that retrieves song lyrics from the internet, processes them using Amazon Bedrock, extracts vocabulary, and stores it in a local database. The application utilizes FastAPI for the web framework and employs SQLite3 for database management.

## Project Structure

```
agentic-workflow
├── src
│   ├── main.py             # Entry point of the FastAPI application
│   ├── api
│   │   └── agent.py        # API endpoint for getting lyrics
│   ├── tools
│   │   ├── bedrock_client.py      # AWS Bedrock integration
│   │   ├── extract_vocabulary.py   # Functions to extract vocabulary from lyrics
│   │   ├── get_page_content.py     # Functions to retrieve webpage content
│   │   └── search_web.py          # Functions to perform web searches
│   └── models
│       └── __init__.py     # Data models or schemas for the application
├── requirements.txt         # Project dependencies
├── README.md               # Project documentation
└── config.py              # Configuration settings
```

## Prerequisites

- Python 3.8+
- AWS Account with Bedrock access
- AWS credentials configured
- uv package manager (`pip install uv`)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd agentic-workflow
```

2. Create and activate a virtual environment using uv:
```bash
uv venv
source .venv/bin/activate  # On Unix/Linux
# or
.venv\Scripts\activate     # On Windows
```

3. Install dependencies:
```bash
uv pip install -r requirements.txt
```

4. Configure AWS credentials by setting environment variables:
```bash
export AWS_ACCESS_KEY_ID=<your-access-key-id>
export AWS_SECRET_ACCESS_KEY=<your-secret-access-key>
export AWS_REGION=<your-region>
```

## Usage

1. Start the FastAPI application:

```bash
uvicorn src.main:app --reload
```

2. Send a POST request to `/api/agent` with song details:

```json
{
  "message_request": "Song Title by Artist Name"
}
```

The response will include:
- Original lyrics processed by Amazon Bedrock for improved formatting
- List of unique vocabulary words extracted from the lyrics

Example response:
```json
{
  "lyrics": "Processed and formatted lyrics...",
  "vocabulary": ["word1", "word2", "word3"]
}
```

## Features

- Web-based lyrics search using DuckDuckGo
- Lyrics processing and enhancement using Amazon Bedrock
- Vocabulary extraction and analysis
- RESTful API with FastAPI

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License.