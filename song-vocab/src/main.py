from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles  # Import StaticFiles
from fastapi.responses import HTMLResponse # Import HTMLResponse
from .api.agent import router as agent_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent_router)

# Remove static file mount
# app.mount("/static", StaticFiles(directory="/home/phil/free-genai-bootcamp-2025/song-vocab/agentic-workflow"), name="static") # Mount static files

INDEX_HTML_CONTENT = """<!DOCTYPE html>
<html>
<head>
    <title>Song Lyrics Finder</title>
</head>
<body>
    <h1>Song Lyrics Finder</h1>
    <label for="song">Song:</label><br>
    <input type="text" id="song" name="song"><br><br>
    <label for="artist">Artist:</label><br>
    <input type="text" id="artist" name="artist"><br><br>
    <button onclick="getLyrics()">Get Lyrics</button>
    <div id="lyrics-display"></div>

    <script>
        function getLyrics() {
            const song = document.getElementById('song').value;
            const artist = document.getElementById('artist').value;
            const lyricsDisplay = document.getElementById('lyrics-display');

            fetch(`/api/agent/${encodeURIComponent(song)}/${encodeURIComponent(artist)}`)
                .then(response => response.json())
                .then(data => {
                    lyricsDisplay.innerHTML = `<pre>${data.lyrics}</pre>`; // Use <pre> for formatting
                })
                .catch(error => {
                    lyricsDisplay.innerHTML = `<p>Error: ${error.message}</p>`;
                });
           }
       </script>
   </body>
   </html>"""

@app.get("/api") # Changed root path for API to /api to avoid conflict with static files
def read_root():
    return {"message": "Welcome to the Lyrics Vocabulary API"}

@app.get("/", response_class=HTMLResponse)
async def read_index():
    return HTMLResponse(content=INDEX_HTML_CONTENT)
