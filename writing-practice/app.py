import streamlit as st
import requests
from typing import List, Dict
import json
from PIL import Image
import io
from manga_ocr import MangaOcr
import os
from streamlit_drawable_canvas import st_canvas
import numpy as np
import sys

# Configure Streamlit to handle PyTorch module watching
os.environ["WATCHDOG_FORCE_POLLING"] = "true"
st.set_page_config(page_title="Japanese Writing Practice", layout="wide")

# Disable PyTorch class watching in Streamlit
if 'torch.classes' in sys.modules:
    del sys.modules['torch.classes']

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
    """Get the list of practice words to use."""
    return DEFAULT_WORDS

def generate_sentence(word: Dict) -> tuple[str, str]:
    """Generate a single Kanji word"""
    return word['japanese'], word['english']

def process_canvas_data(image_data: np.ndarray) -> str:
    """Process canvas drawing and convert to text using MangaOCR"""
    if image_data is None:
        st.error("No image data provided.")
        return ""
    try:
        # Save the original image for debugging
        st.session_state['debug_original'] = Image.fromarray(image_data)
        st.session_state['debug_stage'] = 'Processing image'

        # For RGBA canvas data
        if len(image_data.shape) == 3 and image_data.shape[2] == 4:
            # Extract drawing data from alpha channel
            alpha = image_data[:, :, 3]
            st.write("Alpha channel extracted.")
            
            # Create binary image (black drawing on white background)
            binary = np.full(alpha.shape, 255, dtype=np.uint8)
            binary[alpha > 0] = 0  # Where we drew becomes black
            st.write("Binary image created.")
            
            # Add white padding
            pad = 100  # Larger padding
            padded = np.full((binary.shape[0] + 2*pad, binary.shape[1] + 2*pad), 255, dtype=np.uint8)
            padded[pad:-pad, pad:-pad] = binary
            st.write("Padding added.")
            
            # Convert to PIL Image
            img = Image.fromarray(padded)
            st.write("Converted to PIL Image.")
            
            # Save intermediate steps for debugging
            st.session_state['debug_alpha'] = Image.fromarray(alpha)
            st.session_state['debug_binary'] = Image.fromarray(binary)
            st.session_state['debug_padded'] = img
            
            # Resize to larger size (4x) for better OCR
            w, h = img.size
            img = img.resize((w*4, h*4), Image.Resampling.LANCZOS)
            st.session_state['debug_final'] = img
            st.write("Image resized for OCR.")
            
            # Count pixels to verify drawing
            black_pixels = np.count_nonzero(binary == 0)
            st.session_state['debug_black_pixels'] = black_pixels
            st.write(f"Black pixels counted: {black_pixels}")
            
            if black_pixels > 100:  # Only process if enough content
                try:
                    st.session_state['debug_stage'] = 'Running OCR'
                    st.write("Running OCR...")
                    # Save image to temporary file for OCR
                    img_path = "temp_kanji.png"
                    img.save(img_path)
                    # Use MangaOCR on the saved image
                    text = mocr(img_path)
                    # Clean up
                    os.remove(img_path)
                    st.session_state['debug_ocr_result'] = text
                    st.write(f"OCR result: {text}")
                    return text
                except Exception as ocr_error:
                    st.session_state['debug_ocr_error'] = str(ocr_error)
                    st.error(f"OCR Error: {ocr_error}")
                    return ""
            else:
                st.session_state['debug_stage'] = 'Not enough content'
                st.error("Not enough content to process.")
                return ""
    except Exception as e:
        st.error(f"Error processing drawing: {str(e)}")
        st.session_state['debug_error'] = str(e)
        import traceback
        st.session_state['debug_traceback'] = traceback.format_exc()
        st.error("Processing Error:")
        st.code(st.session_state['debug_traceback'])
        return ""

def grade_attempt(target_japanese: str, user_japanese: str) -> Dict:
    """Grade the writing attempt using Local LLM"""
    prompt = f"""Compare this Japanese writing attempt:
    Target Japanese: {target_japanese}
    User's Japanese: {user_japanese}
    
    Grade using S, A, B, C, D, F ranking system.
    Provide a brief explanation of the grade and any suggestions for improvement.
    Also include whether the characters match exactly.
    
    Return response in this JSON format:
    {{
        "grade": "letter grade",
        "explanation": "explanation and suggestions",
        "exact_match": true/false
    }}"""
    
    response = generate_completion(prompt)
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        return {
            "grade": "F",
            "explanation": "Error processing grade. Please try again.",
            "exact_match": False
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
    if "current_japanese" not in st.session_state:
        st.session_state.current_japanese = ""
    if "current_english" not in st.session_state:
        st.session_state.current_english = ""
    if "canvas_key" not in st.session_state:
        st.session_state.canvas_key = 0
    if "canvas_image_data" not in st.session_state:
        st.session_state.canvas_image_data = None
    
    if st.session_state.state == AppState.SETUP:
        if st.button("Generate Practice Text"):
            words = fetch_words("1")
            word = words[np.random.randint(len(words))]
            japanese, english = generate_sentence(word)
            st.session_state.current_japanese = japanese
            st.session_state.current_english = english
            st.session_state.state = AppState.PRACTICE
            st.rerun()
    
    elif st.session_state.state == AppState.PRACTICE:
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.subheader("Practice Text")
            st.markdown(f"<h2 style='font-size: 48px;'>Target Kanji: {st.session_state.current_japanese}</h2>", unsafe_allow_html=True)
            st.markdown(f"**Meaning:** {st.session_state.current_english}")
        
        with col2:
            st.subheader("Write Kanji Here")
            
            # Drawing canvas
            canvas_result = st_canvas(
                fill_color="rgba(255, 255, 255, 0)",
                stroke_width=5,
                stroke_color="#000000",
                background_color="#ffffff",
                width=400,
                height=200,
                drawing_mode="freedraw",
                key=f"canvas_{st.session_state.canvas_key}"
            )
            
            # Store canvas image data
            if canvas_result.image_data is not None:
                st.session_state.canvas_image_data = canvas_result.image_data
            
            # Control buttons in columns
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("Clear"):
                    st.session_state.canvas_key += 1
                    st.session_state.canvas_image_data = None
                    st.rerun()
            
            with col2:
                if st.button("Submit"):
                    if st.session_state.canvas_image_data is not None:
                        result_text = process_canvas_data(st.session_state.canvas_image_data)
                        
                        if result_text:
                            st.markdown("### Results")
                            st.markdown("**OCR Detected:**")
                            st.markdown(f"{result_text}")
                            
                            # Grade attempt
                            grade_result = grade_attempt(
                                st.session_state.current_japanese,
                                result_text
                            )
                            
                            st.markdown("### Evaluation")
                            st.markdown(f"**Grade:** {grade_result['grade']}")
                            st.markdown(f"**Feedback:** {grade_result['explanation']}")
                            
                            # Debug information
                            with st.expander("Debug Information"):
                                st.write("Processing Stage:", st.session_state.get('debug_stage', 'N/A'))
                                st.write("Black Pixels:", st.session_state.get('debug_black_pixels', 'N/A'))
                                if 'debug_ocr_error' in st.session_state:
                                    st.error(f"OCR Error: {st.session_state['debug_ocr_error']}")
                                
                                # Show processing stages in tabs instead of columns
                                tab1, tab2, tab3, tab4 = st.tabs(["Original", "Binary", "Padded", "Final"])
                                
                                with tab1:
                                    if 'debug_original' in st.session_state:
                                        st.image(st.session_state['debug_original'], caption="Original Drawing")
                                
                                with tab2:
                                    if 'debug_binary' in st.session_state:
                                        st.image(st.session_state['debug_binary'], caption="Binary Image")
                                
                                with tab3:
                                    if 'debug_padded' in st.session_state:
                                        st.image(st.session_state['debug_padded'], caption="Padded Image")
                                
                                with tab4:
                                    if 'debug_final' in st.session_state:
                                        st.image(st.session_state['debug_final'], caption="Final Image for OCR")
                                
                                if 'debug_error' in st.session_state:
                                    st.error("Processing Error:")
                                    st.code(st.session_state['debug_traceback'])
                        else:
                            st.error("Could not recognize any text. Try writing more clearly or with darker strokes.")
                    else:
                        st.error("Please draw something first")
            
            with col3:
                if st.button("Try Another"):
                    st.session_state.state = AppState.SETUP
                    st.session_state.canvas_key += 1
                    st.session_state.canvas_image_data = None
                    st.rerun()

if __name__ == "__main__":
    main()