import streamlit as st
import requests
from typing import List, Dict
import json
from PIL import Image
import io
from manga_ocr import MangaOcr
import os

# Set environment variable to avoid PyTorch warning with Streamlit's file watcher
os.environ["WATCHDOG_FORCE_POLLING"] = "true"

# Initialize MangaOCR
mocr = MangaOcr()

OLLAMA_BASE_URL = "http://localhost:11434/api"

# Default words to use when API is unavailable
DEFAULT_WORDS = [
    {"japanese": "本", "english": "book"},
    {"japanese": "食べる", "english": "to eat"},
    {"japanese": "飲む", "english": "to drink"},
    {"japanese": "車", "english": "car"},
    {"japanese": "今日", "english": "today"},
    {"japanese": "明日", "english": "tomorrow"},
    {"japanese": "昨日", "english": "yesterday"},
    {"japanese": "学校", "english": "school"},
    {"japanese": "行く", "english": "to go"},
    {"japanese": "見る", "english": "to see/watch"}
]

class AppState:
    SETUP = "setup"
    PRACTICE = "practice"
    REVIEW = "review"

def generate_completion(prompt: str, model: str = "mistral") -> str:
    """Generate completion using Ollama"""
    try:
        with st.spinner("Generating response..."):
            response = requests.post(
                f"{OLLAMA_BASE_URL}/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            if response.status_code == 200:
                return response.json()["response"].strip()
            else:
                st.error(f"Error generating completion: {response.status_code}")
                return ""
    except Exception as e:
        st.error(f"Error connecting to Ollama: {str(e)}")
        return ""

def fetch_words(group_id: str) -> List[Dict]:
    """Fetch words from the API or use default words if API is unavailable"""
    try:
        response = requests.get(f"http://localhost:5000/api/groups/{group_id}/raw")
        if response.status_code == 200:
            return response.json()
        else:
            st.info("Using built-in word list for practice. API connection not required.")
            return DEFAULT_WORDS
    except Exception as e:
        st.info("Using built-in word list for practice. API connection not required.")
        return DEFAULT_WORDS

def generate_sentence(word: Dict) -> str:
    """Generate a practice sentence using Local LLM"""
    with st.status(f"Generating practice sentence using: {word['japanese']} ({word['english']})...") as status:
        status.update(label="Preparing prompt...", state="running", expanded=True)
        
        prompt = f"""Generate a simple sentence using the following word: {word['japanese']}
        The grammar should be scoped to JLPTN5 grammar.
        You can use the following vocabulary to construct a simple sentence:
        - simple objects eg. book, car, ramen, sushi
        - simple verbs, to drink, to eat, to meet
        - simple times eg. tomorrow, today, yesterday
        
        Return only the English sentence."""
        
        status.update(label="Sending request to language model...", state="running")
        response = generate_completion(prompt)
        
        if response:
            status.update(label="Sentence generated successfully!", state="complete", expanded=False)
        else:
            status.update(label="Failed to generate sentence", state="error", expanded=True)
            
        return response

def transcribe_image(image) -> str:
    """Transcribe Japanese text from image using MangaOCR"""
    if image is None:
        return ""
    try:
        # Convert uploaded file to PIL Image
        img = Image.open(image)
        # Use MangaOCR to get text
        text = mocr(img)
        return text
    except Exception as e:
        st.error(f"Error transcribing image: {str(e)}")
        return ""

def translate_text(text: str) -> str:
    """Translate Japanese text to English using Local LLM"""
    prompt = f"""Translate the following Japanese text to English:
    {text}
    
    Return only the English translation."""
    
    return generate_completion(prompt)

def grade_attempt(english_prompt: str, japanese_attempt: str, translation: str) -> Dict:
    """Grade the writing attempt using Local LLM"""
    prompt = f"""Grade this Japanese writing attempt:
    
    Original English: {english_prompt}
    Student's Japanese: {japanese_attempt}
    Literal Translation: {translation}
    
    Grade using S, A, B, C, D, F ranking system.
    Provide a brief explanation of the grade and any suggestions for improvement.
    
    Return response in this JSON format:
    {{
        "grade": "letter grade",
        "explanation": "explanation and suggestions"
    }}"""
    
    response = generate_completion(prompt)
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        # Fallback in case the LLM doesn't return valid JSON
        return {
            "grade": "F",
            "explanation": "Error processing grade. Please try again."
        }

def main():
    st.title("Japanese Writing Practice")
    
    # Check if Ollama is running
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/tags")
        if response.status_code != 200:
            st.error("Cannot connect to Ollama. Please make sure Ollama is running on http://localhost:11434")
            return
    except:
        st.error("Cannot connect to Ollama. Please make sure Ollama is running on http://localhost:11434")
        return
        
    # Initialize session state
    if "state" not in st.session_state:
        st.session_state.state = AppState.SETUP
    if "words" not in st.session_state:
        st.session_state.words = []
    if "current_sentence" not in st.session_state:
        st.session_state.current_sentence = ""
    if "current_word" not in st.session_state:
        st.session_state.current_word = None
    
    # Initial word fetch
    if not st.session_state.words:
        with st.spinner("Loading word list..."):
            group_id = "1"  # TODO: Make this configurable
            words = fetch_words(group_id)
            if words:
                st.session_state.words = words
                st.success("Word list loaded successfully!")
    
    # State machine
    if st.session_state.state == AppState.SETUP:
        if st.button("Generate Sentence"):
            if st.session_state.words:
                # Randomly select a word
                import random
                word = random.choice(st.session_state.words)
                st.session_state.current_word = word
                st.session_state.current_sentence = generate_sentence(word)
                if st.session_state.current_sentence:
                    st.session_state.state = AppState.PRACTICE
            else:
                st.error("No words available. Please check API connection.")
    
    elif st.session_state.state == AppState.PRACTICE:
        st.write("English Sentence:")
        st.write(st.session_state.current_sentence)
        
        uploaded_file = st.file_uploader("Upload your handwritten Japanese", type=["jpg", "jpeg", "png"])
        
        if st.button("Submit for Review"):
            if uploaded_file is not None:
                # Process the image
                transcription = transcribe_image(uploaded_file)
                translation = translate_text(transcription)
                grade_result = grade_attempt(
                    st.session_state.current_sentence,
                    transcription,
                    translation
                )
                
                # Store results in session state
                st.session_state.review_results = {
                    "transcription": transcription,
                    "translation": translation,
                    "grade": grade_result
                }
                st.session_state.state = AppState.REVIEW
            else:
                st.error("Please upload an image first")
    
    elif st.session_state.state == AppState.REVIEW:
        # Display original sentence
        st.write("Original English Sentence:")
        st.write(st.session_state.current_sentence)
        
        # Display review results
        results = st.session_state.review_results
        
        st.write("Transcription:")
        st.write(results["transcription"])
        
        st.write("Translation:")
        st.write(results["translation"])
        
        st.write("Grade:")
        st.write(f"Grade: {results['grade']['grade']}")
        st.write(f"Feedback: {results['grade']['explanation']}")
        
        if st.button("Next Question"):
            # Reset for next question
            st.session_state.state = AppState.SETUP
            st.session_state.current_sentence = ""
            st.session_state.current_word = None
            st.session_state.review_results = None

if __name__ == "__main__":
    main()