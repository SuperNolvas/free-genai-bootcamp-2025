"""Backend initialization"""

# Import core components
from .rag import RAGSystem
from .chat import BedrockChat
from .get_transcript import YouTubeTranscriptDownloader
from .interactive import InteractiveLearning
from .audio_generation import AudioGenerator

# Export key classes
__all__ = [
    'RAGSystem',
    'BedrockChat',
    'YouTubeTranscriptDownloader',
    'InteractiveLearning',
    'AudioGenerator'
]