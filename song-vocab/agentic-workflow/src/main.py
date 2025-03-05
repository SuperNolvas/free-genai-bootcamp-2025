from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.agent import router as agent_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Lyrics Vocabulary API"}