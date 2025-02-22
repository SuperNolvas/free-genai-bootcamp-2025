import streamlit as st
from typing import Dict
import json
from collections import Counter
import re

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.chat import BedrockChat
from backend.get_transcript import YouTubeTranscriptDownloader  # Add this import


# Page config
st.set_page_config(
    page_title="Japanese Learning Assistant",
    page_icon="🎌",
    layout="wide"
)

# Initialize session state
if 'transcript' not in st.session_state:
    st.session_state.transcript = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'current_query' not in st.session_state:
    st.session_state.current_query = ''
if 'rag_feedback' not in st.session_state:
    st.session_state.rag_feedback = []

def render_header():
    """Render the header section"""
    st.title("🎌 Japanese Learning Assistant")
    st.markdown("""
    Transform YouTube transcripts into interactive Japanese learning experiences.
    
    This tool demonstrates:
    - Base LLM Capabilities
    - RAG (Retrieval Augmented Generation)
    - Amazon Bedrock Integration
    - Agent-based Learning Systems
    """)

def render_sidebar():
    """Render the sidebar with component selection"""
    with st.sidebar:
        st.header("Development Stages")
        
        # Main component selection
        selected_stage = st.radio(
            "Select Stage:",
            [
                "1. Chat with Nova",
                "2. Raw Transcript",
                "3. Structured Data",
                "4. RAG Implementation",
                "5. Interactive Learning"
            ]
        )
        
        # Stage descriptions
        stage_info = {
            "1. Chat with Nova": """
            **Current Focus:**
            - Basic Japanese learning
            - Understanding LLM capabilities
            - Identifying limitations
            """,
            
            "2. Raw Transcript": """
            **Current Focus:**
            - YouTube transcript download
            - Raw text visualization
            - Initial data examination
            """,
            
            "3. Structured Data": """
            **Current Focus:**
            - Text cleaning
            - Dialogue extraction
            - Data structuring
            """,
            
            "4. RAG Implementation": """
            **Current Focus:**
            - Bedrock embeddings
            - Vector storage
            - Context retrieval
            """,
            
            "5. Interactive Learning": """
            **Current Focus:**
            - Scenario generation
            - Audio synthesis
            - Interactive practice
            """
        }
        
        st.markdown("---")
        st.markdown(stage_info[selected_stage])
        
        return selected_stage

def render_chat_stage():
    """Render an improved chat interface"""
    st.header("Chat with Nova")

    # Initialize BedrockChat instance if not in session state
    if 'bedrock_chat' not in st.session_state:
        st.session_state.bedrock_chat = BedrockChat()

    # Introduction text
    st.markdown("""
    Start by exploring Nova's base Japanese language capabilities. Try asking questions about Japanese grammar, 
    vocabulary, or cultural aspects.
    """)

    # Initialize chat history if not exists
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar="🧑‍💻" if message["role"] == "user" else "🤖"):
            st.markdown(message["content"])

    # Chat input area
    if prompt := st.chat_input("Ask about Japanese language..."):
        # Process the user input
        process_message(prompt)

    # Example questions in sidebar
    with st.sidebar:
        st.markdown("### Try These Examples")
        example_questions = [
            "How do I say 'Where is the train station?' in Japanese?",
            "Explain the difference between は and が",
            "What's the polite form of 食べる?",
            "How do I count objects in Japanese?",
            "What's the difference between こんにちは and こんばんは?",
            "How do I ask for directions politely?"
        ]
        
        for q in example_questions:
            if st.button(q, use_container_width=True, type="secondary"):
                # Process the example question
                process_message(q)
                st.rerun()

    # Add a clear chat button
    if st.session_state.messages:
        if st.button("Clear Chat", type="primary"):
            st.session_state.messages = []
            st.rerun()

def process_message(message: str):
    """Process a message and generate a response"""
    # Add user message to state and display
    st.session_state.messages.append({"role": "user", "content": message})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(message)

    # Generate and display assistant's response
    with st.chat_message("assistant", avatar="🤖"):
        response = st.session_state.bedrock_chat.generate_response(message)
        if response:
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})



def count_characters(text):
    """Count Japanese and total characters in text"""
    if not text:
        return 0, 0
        
    def is_japanese(char):
        return any([
            '\u4e00' <= char <= '\u9fff',  # Kanji
            '\u3040' <= char <= '\u309f',  # Hiragana
            '\u30a0' <= char <= '\u30ff',  # Katakana
        ])
    
    jp_chars = sum(1 for char in text if is_japanese(char))
    return jp_chars, len(text)

def render_transcript_stage():
    """Render the raw transcript stage"""
    st.header("Raw Transcript Processing")
    
    # URL input
    url = st.text_input(
        "YouTube URL",
        placeholder="Enter a Japanese lesson YouTube URL"
    )
    
    # Download button and processing
    if url:
        if st.button("Download Transcript"):
            try:
                downloader = YouTubeTranscriptDownloader()
                transcript = downloader.get_transcript(url)
                if transcript:
                    # Store the raw transcript text in session state
                    transcript_text = "\n".join([entry['text'] for entry in transcript])
                    st.session_state.transcript = transcript_text
                    
                    # Save the transcript to file
                    video_id = downloader.extract_video_id(url)
                    if downloader.save_transcript(transcript, video_id):
                        st.success("Transcript downloaded and saved successfully!")
                    else:
                        st.warning("Transcript downloaded but failed to save to file.")
                else:
                    st.error("No transcript found for this video.")
            except Exception as e:
                st.error(f"Error downloading transcript: {str(e)}")

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Raw Transcript")
        if st.session_state.transcript:
            st.text_area(
                label="Raw text",
                value=st.session_state.transcript,
                height=400,
                disabled=True
            )
    
        else:
            st.info("No transcript loaded yet")
    
    with col2:
        st.subheader("Transcript Stats")
        if st.session_state.transcript:
            # Calculate stats
            jp_chars, total_chars = count_characters(st.session_state.transcript)
            total_lines = len(st.session_state.transcript.split('\n'))
            
            # Display stats
            st.metric("Total Characters", total_chars)
            st.metric("Japanese Characters", jp_chars)
            st.metric("Total Lines", total_lines)
        else:
            st.info("Load a transcript to see statistics")

def render_structured_stage():
    """Render the structured data stage"""
    st.header("Structured Data Processing")
    
    from backend.structured_data import JLPTStructuredDataExtractor

    # Only process if we have a transcript
    if not st.session_state.transcript:
        st.warning("Please load a transcript first in the 'Raw Transcript' stage")
        return

    # Initialize the extractor
    extractor = JLPTStructuredDataExtractor()
    
    # Process button
    if st.button("Process Transcript"):
        with st.spinner("Extracting questions..."):
            questions = extractor.extract_questions(st.session_state.transcript)
            st.session_state.structured_questions = questions
    
    # Display results in two columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Raw Transcript")
        if st.session_state.transcript:
            st.text_area(
                "Source Text",
                st.session_state.transcript,
                height=400,
                disabled=True
            )
    
    with col2:
        st.subheader("Extracted Questions")
        if 'structured_questions' in st.session_state and st.session_state.structured_questions:
            for i, question in enumerate(st.session_state.structured_questions, 1):
                with st.expander(f"Question {i}"):
                    st.markdown("**Introduction:**")
                    st.write(question.introduction)
                    
                    st.markdown("**Conversation:**")
                    st.write(question.conversation)
                    
                    st.markdown("**Question:**")
                    st.write(question.question)
        else:
            st.info("Click 'Process Transcript' to extract structured data")

def render_rag_stage():
    """Render the RAG implementation stage"""
    from backend.rag import RAGSystem
    import os
    from datetime import datetime
    
    st.header("RAG System")
    
    # Add system status in sidebar
    with st.sidebar:
        st.subheader("System Status")
        if 'rag_system' in st.session_state and st.session_state.rag_system:
            try:
                doc_count = st.session_state.rag_system.collection.count()
                if doc_count > 0:
                    st.success(f"✅ System Active - {doc_count} documents loaded")
                else:
                    st.warning("⚠️ No documents loaded")
            except Exception as e:
                st.error("❌ System Error")
                st.error(str(e))

        # Reset button with confirmation
        if st.button("🔄 Reset System", key="reset_system_btn"):
            if 'rag_system' in st.session_state:
                with st.spinner("Resetting system..."):
                    try:
                        st.session_state.rag_system.reset_collection()
                        st.success("System reset successful!")
                    except:
                        pass
                st.session_state.rag_system = None
                st.rerun()

    # Initialize RAG system
    if 'rag_system' not in st.session_state:
        try:
            with st.spinner("🚀 Initializing RAG system..."):
                st.session_state.rag_system = RAGSystem()
                transcript_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend', 'transcripts')
                
                if os.path.exists(transcript_dir):
                    with st.status("Loading transcripts...", expanded=True) as status:
                        st.write("Processing documents...")
                        st.session_state.rag_system.load_transcripts(transcript_dir)
                        doc_count = st.session_state.rag_system.collection.count()
                        status.update(label=f"✅ Loaded {doc_count} documents!", state="complete")
                else:
                    st.warning("⚠️ No transcripts directory found")
                    st.info("Please ensure transcript files are present in backend/transcripts")
                    
        except Exception as e:
            st.error("❌ System Initialization Failed")
            st.error(str(e))
            return

    # Main interface
    if st.session_state.rag_system:
        tab1, tab2, tab3 = st.tabs(["Query Interface", "System Stats", "Debug"])
        
        with tab1:
            # Example queries
            with st.expander("📚 Example Queries"):
                example_queries = [
                    "What are common greeting patterns used in the dialogues?",
                    "How do people typically ask for directions?",
                    "What kinds of locations are mentioned in the conversations?",
                    "What are some polite expressions used in these dialogues?",
                    "How do people typically respond to questions in these conversations?"
                ]
                
                col1, col2 = st.columns(2)
                for i, query in enumerate(example_queries):
                    with col1 if i % 2 == 0 else col2:
                        if st.button(query, key=f"example_query_{i}", use_container_width=True):
                            st.session_state.current_query = query
                            st.rerun()
            
            # Query input
            query = st.text_input(
                "🔍 Ask about Japanese language patterns",
                value=st.session_state.get('current_query', ''),
                placeholder="Enter your question about Japanese expressions, grammar, or dialogue patterns...",
                key="query_input"
            )
            
            if query:
                try:
                    with st.spinner("🤔 Processing query..."):
                        result = st.session_state.rag_system.query(query)
                    
                    # Display results in columns
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("📑 Retrieved Contexts")
                        if result.get('contexts'):
                            for i, (context, metadata) in enumerate(zip(
                                result['contexts'], 
                                result['metadata'].get('context_sources', [''] * len(result['contexts']))
                            ), 1):
                                with st.expander(f"Context {i}"):
                                    st.caption(f"Source: {metadata}")
                                    if 'metadata' in result and 'relevance_scores' in result['metadata']:
                                        score = result['metadata']['relevance_scores'][i-1]
                                        st.progress(score, f"Relevance: {score:.2f}")
                                    st.markdown(context)
                        else:
                            st.info("No relevant contexts found")
                    
                    with col2:
                        st.subheader("💡 Answer")
                        if result.get('answer'):
                            st.markdown(result['answer'])
                            
                            # Show metadata
                            with st.expander("Query Details"):
                                st.json({
                                    "timestamp": result['metadata']['timestamp'],
                                    "num_contexts": result['metadata']['num_contexts'],
                                    "status": result['metadata']['status']
                                })
                            
                            # Feedback system with connection to RAG system
                            st.divider()
                            st.caption("Was this response helpful?")
                            fb_col1, fb_col2 = st.columns(2)
                            with fb_col1:
                                if st.button("👍", key=f"fb_yes_{hash(query)}"):
                                    st.session_state.rag_system.add_feedback(
                                        query=query,
                                        feedback="positive",
                                        contexts=result.get('contexts', [])
                                    )
                                    st.success("Thanks for your feedback!")
                            with fb_col2:
                                if st.button("👎", key=f"fb_no_{hash(query)}"):
                                    st.session_state.rag_system.add_feedback(
                                        query=query,
                                        feedback="negative",
                                        contexts=result.get('contexts', [])
                                    )
                                    st.error("Thanks for your feedback!")
                        else:
                            st.error("No response generated")
                
                except Exception as e:
                    st.error("Error processing query")
                    st.error(str(e))
                    if hasattr(st.session_state.rag_system, 'get_logs'):
                        with st.expander("System Logs"):
                            logs = st.session_state.rag_system.get_logs()
                            for log in logs[-5:]:
                                if "!" in log:
                                    st.error(log)
                                elif "✓" in log:
                                    st.success(log)
                                else:
                                    st.info(log)
        
        with tab2:
            st.subheader("📊 System Statistics")
            try:
                stats_col1, stats_col2 = st.columns(2)
                with stats_col1:
                    doc_count = st.session_state.rag_system.collection.count()
                    st.metric("Documents Loaded", doc_count)
                    
                    # Use RAG system's feedback stats
                    feedback_stats = st.session_state.rag_system.get_feedback_stats()
                    if feedback_stats['total_feedback'] > 0:
                        st.metric("User Satisfaction", f"{feedback_stats['positive_rate']:.1f}%")
                        st.metric("Total Feedback", feedback_stats['total_feedback'])
                
                with stats_col2:
                    if hasattr(st.session_state.rag_system, 'get_cache_stats'):
                        cache_stats = st.session_state.rag_system.get_cache_stats()
                        st.metric("Cached Queries", cache_stats['cache_size'])
                        
                    # Show recent feedback
                    if feedback_stats.get('recent_feedback'):
                        st.subheader("Recent Feedback")
                        for fb in feedback_stats['recent_feedback']:
                            icon = "👍" if fb['feedback'] == "positive" else "👎"
                            st.text(f"{icon} {fb['query'][:50]}...")
            except Exception as e:
                st.error(f"Error loading statistics: {str(e)}")
        
        with tab3:
            st.subheader("🛠️ Debug Information")
            
            # System logs
            with st.expander("System Logs"):
                if hasattr(st.session_state.rag_system, 'get_logs'):
                    logs = st.session_state.rag_system.get_logs()
                    for log in logs:
                        if "!" in log:
                            st.error(log)
                        elif "✓" in log:
                            st.success(log)
                        else:
                            st.info(log)
            
            # Collection stats
            with st.expander("Collection Details"):
                try:
                    stats = {
                        "document_count": st.session_state.rag_system.collection.count(),
                        "collection_name": st.session_state.rag_system.collection.name,
                        "embedding_model": st.session_state.rag_system.embedding_function.model_name
                    }
                    st.json(stats)
                except Exception as e:
                    st.error(f"Error getting collection details: {str(e)}")
            
            # Cache info
            if hasattr(st.session_state.rag_system, 'get_cache_stats'):
                with st.expander("Cache Information"):
                    cache_stats = st.session_state.rag_system.get_cache_stats()
                    st.json(cache_stats)
                    if st.button("Clear Cache", key="clear_cache_debug"):
                        st.session_state.rag_system.clear_cache()
                        st.success("Cache cleared!")
                        st.rerun()

            # Add feedback management
            with st.expander("Feedback Management"):
                feedback_stats = st.session_state.rag_system.get_feedback_stats()
                st.json(feedback_stats)
                if st.button("Clear Feedback History", key="clear_feedback"):
                    st.session_state.rag_system.clear_feedback()
                    st.success("Feedback history cleared!")
                    st.rerun()

def render_interactive_stage():
    """Render the interactive learning stage"""
    from backend.interactive import InteractiveLearning
    
    st.header("Interactive Learning")
    
    # Initialize interactive learning system
    if 'interactive_system' not in st.session_state:
        st.session_state.interactive_system = InteractiveLearning()
        
    if 'current_practice_item' not in st.session_state:
        st.session_state.current_practice_item = None
    
    # Practice type selection
    practice_type = st.selectbox(
        "Select Practice Type",
        ["dialogue", "vocabulary", "listening"],
        format_func=lambda x: x.title() + " Practice"
    )
    
    # Generate new practice item button
    if st.button("Generate New Practice Item", key="generate_practice"):
        try:
            with st.spinner("Generating practice..."):
                st.session_state.current_practice_item = st.session_state.interactive_system.generate_practice_item(practice_type)
        except Exception as e:
            st.error(f"Error generating practice: {str(e)}")
    
    # Display practice content
    if st.session_state.current_practice_item:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Practice Scenario")
            
            if practice_type == "vocabulary":
                # Create styled containers for vocabulary practice
                st.markdown("""
                    <style>
                    .vocab-card {
                        padding: 20px;
                        border-radius: 10px;
                        background-color: #f0f2f6;
                        margin-bottom: 20px;
                        border-left: 5px solid #ff4b4b;
                        overflow: hidden;
                    }
                    .question-section {
                        margin-top: 25px;
                        padding: 15px;
                        border-radius: 5px;
                        background-color: white;
                    }
                    .word-container {
                        display: flex;
                        flex-wrap: wrap;
                        align-items: center;
                        justify-content: center;
                        gap: 8px;
                        margin: 10px 0;
                        text-align: center;
                        width: 100%;
                    }
                    .target-word {
                        font-size: 1.5em;
                        color: #ff4b4b;
                        padding: 4px 12px;
                        white-space: nowrap;
                        background-color: rgba(255,75,75,0.1);
                        border-radius: 4px;
                        margin: 4px 0;
                        transition: all 0.3s ease;
                        display: inline-block;
                        position: relative;
                    }
                    .target-word:hover {
                        transform: scale(1.1);
                        background-color: rgba(255,75,75,0.15);
                        box-shadow: 0 2px 8px rgba(255,75,75,0.2);
                    }
                    .context-text {
                        flex: 1;
                        min-width: 120px;
                        display: inline-block;
                        line-height: 1.5;
                        padding: 4px;
                    }
                    @media (max-width: 640px) {
                        .word-container {
                            padding: 8px;
                        }
                        .context-text {
                            width: 100%;
                            text-align: center;
                        }
                    }
                    @media (max-width: 400px) {
                        .word-container {
                            flex-direction: column;
                        }
                        .target-word {
                            width: auto;
                            max-width: 90%;
                        }
                    }
                    </style>
                """, unsafe_allow_html=True)
                
                # Vocabulary word section
                st.markdown('<div class="vocab-card">', unsafe_allow_html=True)
                st.subheader("Vocabulary Word")
                context = st.session_state.current_practice_item.context
                if "**" in context:
                    parts = context.split("**")
                    if len(parts) >= 3:
                        st.markdown('<div class="word-container">', unsafe_allow_html=True)
                        if parts[0].strip():
                            st.markdown(f'<div class="context-text">{parts[0]}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="target-word">{parts[1]}</div>', unsafe_allow_html=True)
                        if parts[2].strip():
                            st.markdown(f'<div class="context-text">{parts[2]}</div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.write(context)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Question section
                st.markdown('<div class="question-section">', unsafe_allow_html=True)
                st.markdown("### Test Your Understanding")
                st.markdown(f"**Question:**\n{st.session_state.current_practice_item.question}")
                st.markdown('</div>', unsafe_allow_html=True)
            elif practice_type == "dialogue":
                # Create styled containers for dialogue practice
                st.markdown("""
                    <style>
                    .dialogue-card {
                        padding: 20px;
                        border-radius: 10px;
                        background-color: #f0f2f6;
                        margin-bottom: 20px;
                        border-left: 5px solid #4b96ff;
                    }
                    </style>
                """, unsafe_allow_html=True)
                
                # Dialogue section
                st.markdown('<div class="dialogue-card">', unsafe_allow_html=True)
                st.subheader("Dialogue Context")
                # Split dialogue into speaker turns for better readability
                dialogue_lines = st.session_state.current_practice_item.context.split('\n')
                for line in dialogue_lines:
                    if line.strip():
                        if ':' in line:
                            speaker, text = line.split(':', 1)
                            st.markdown(f"**{speaker}:** {text}")
                        else:
                            st.markdown(line)
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown("### Comprehension Question")
                st.markdown(f"**{st.session_state.current_practice_item.question}**")
            
            elif practice_type == "listening":
                # Create styled containers for listening practice
                st.markdown("""
                    <style>
                    .listening-card {
                        padding: 20px;
                        border-radius: 10px;
                        background-color: #f0f2f6;
                        margin-bottom: 20px;
                        border-left: 5px solid #4bff4b;
                    }
                    .listening-controls {
                        padding: 10px;
                        background-color: white;
                        border-radius: 5px;
                        margin: 10px 0;
                    }
                    </style>
                """, unsafe_allow_html=True)
                
                st.markdown('<div class="listening-card">', unsafe_allow_html=True)
                st.subheader("Listening Exercise")
                
                # Show listening controls
                st.markdown('<div class="listening-controls">', unsafe_allow_html=True)
                if 'listening_revealed' not in st.session_state:
                    st.session_state.listening_revealed = False
                    
                col1, col2 = st.columns([1, 3])
                with col1:
                    if st.button("🔊 Play", key="play_listening"):
                        st.session_state.listening_revealed = True
                with col2:
                    if st.button("🔄 Reset", key="reset_listening"):
                        st.session_state.listening_revealed = False
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Show dialogue content
                if st.session_state.listening_revealed:
                    dialogue_lines = st.session_state.current_practice_item.context.split('\n')
                    for line in dialogue_lines:
                        if line.strip():
                            if ':' in line:
                                speaker, text = line.split(':', 1)
                                st.markdown(f"**{speaker}:** {text}")
                            else:
                                st.markdown(line)
                else:
                    st.info("👂 Click 'Play' to listen to the conversation")
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown("### Listen and Answer")
                if st.session_state.listening_revealed:
                    st.markdown(f"**{st.session_state.current_practice_item.question}**")
                else:
                    st.markdown("*Question will appear after playing the conversation...*")
            
            else:
                st.markdown(f"**Context:**\n{st.session_state.current_practice_item.context}")
                st.markdown(f"**Question:**\n{st.session_state.current_practice_item.question}")
            
            # Multiple choice options
            selected = st.radio(
                "Choose your answer:",
                st.session_state.current_practice_item.options,
                key="practice_options"
            )
            
            # Check answer button
            if st.button("Submit Answer", key="check_answer"):
                result = st.session_state.interactive_system.check_answer(
                    st.session_state.current_practice_item,
                    selected
                )
                
                if result['is_correct']:
                    st.success("✅ Correct!")
                else:
                    st.error(f"❌ Incorrect. The correct answer was: {result['correct_answer']}")
                
                st.info(f"Explanation: {result['explanation']}")
                st.metric("Current Score", result['score'])
        
        with col2:
            if practice_type == "listening":
                st.subheader("Audio")
                if st.session_state.current_practice_item.audio_url:
                    st.audio(st.session_state.current_practice_item.audio_url)
                else:
                    st.info("Audio not available for this practice item")
            
            # Show session statistics
            st.subheader("Session Stats")
            stats = st.session_state.interactive_system.get_session_stats()
            st.metric("Accuracy", f"{stats['accuracy']:.1f}%")
            st.metric("Questions Completed", stats['total_questions'])
            
            # Reset session button
            if st.button("Reset Session", key="reset_session"):
                st.session_state.interactive_system.reset_session()
                st.session_state.current_practice_item = None
                st.rerun()
            
            # Show practice history
            with st.expander("Practice History"):
                for practice in stats['practice_history']:
                    icon = "✅" if practice['is_correct'] else "❌"
                    st.text(f"{icon} {practice['practice_type'].title()}: {practice['question'][:50]}...")

def main():
    render_header()
    selected_stage = render_sidebar()
    
    # Render appropriate stage
    if selected_stage == "1. Chat with Nova":
        render_chat_stage()
    elif selected_stage == "2. Raw Transcript":
        render_transcript_stage()
    elif selected_stage == "3. Structured Data":
        render_structured_stage()
    elif selected_stage == "4. RAG Implementation":
        render_rag_stage()
    elif selected_stage == "5. Interactive Learning":
        render_interactive_stage()
    
    # Debug section at the bottom
    with st.expander("Debug Information"):
        st.json({
            "selected_stage": selected_stage,
            "transcript_loaded": st.session_state.transcript is not None,
            "chat_messages": len(st.session_state.messages)
        })

if __name__ == "__main__":
    main()