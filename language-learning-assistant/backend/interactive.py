from typing import Dict, List, Optional
import random
from dataclasses import dataclass
from datetime import datetime
from .rag import RAGSystem
from .audio_generation import AudioGenerator

@dataclass
class PracticeItem:
    question: str
    context: str
    options: List[str]
    correct_answer: str
    audio_url: Optional[str] = None
    explanation: Optional[str] = None
    type: str = "dialogue"  # dialogue, vocabulary, or listening

class InteractiveLearning:
    def __init__(self):
        """Initialize interactive learning system with RAG integration"""
        self.rag_system = RAGSystem()
        self.audio_generator = AudioGenerator()  # Add audio generator
        self.current_session = {
            "score": 0,
            "total_questions": 0,
            "practice_history": []
        }
        
        # Cache available voices
        self.available_voices = self.audio_generator.get_available_voices()
        if not self.available_voices:
            print("Warning: No Japanese voices available")
            self.available_voices = [{"id": "Mizuki", "name": "Mizuki", "gender": "Female"}]

    def generate_practice_item(self, practice_type: str) -> PracticeItem:
        """Generate a practice item based on the selected type"""
        # Get relevant contexts from RAG system
        contexts = []
        query_map = {
            "dialogue": "Find a conversation about daily activities or greetings",
            "vocabulary": "Find sentences with common Japanese vocabulary",
            "listening": "Find a short dialogue with question and answer"
        }
        
        try:
            result = self.rag_system.query(query_map[practice_type])
            contexts = result.get('contexts', [])
            if not contexts:
                raise ValueError("No contexts found for practice generation")
            
            # Select a random context
            context = random.choice(contexts)
            
            # Generate practice item based on type
            if practice_type == "dialogue":
                return self._generate_dialogue_practice(context)
            elif practice_type == "vocabulary":
                return self._generate_vocabulary_quiz(context)
            else:  # listening
                return self._generate_listening_exercise(context)
                
        except Exception as e:
            raise Exception(f"Error generating practice item: {str(e)}")

    def _generate_dialogue_practice(self, context: str) -> PracticeItem:
        """Generate a dialogue practice item"""
        # Use RAG to generate a dialogue question
        prompt = f"""Based on this dialogue, create a practice question:
        {context}
        
        Generate a JSON response with:
        1. formatted_dialogue: The dialogue with clear speaker labels (e.g. "A:", "B:", "Student:", "Teacher:")
        2. question: A question about the dialogue content or meaning
        3. options: Four possible responses (one correct)
        4. correct_answer: The correct answer
        5. explanation: A brief explanation of why this answer is correct
        
        Example format:
        {{
            "formatted_dialogue": "Student: すみません、図書館はどこですか？\nStaff: 2階です。\nStudent: ありがとうございます。",
            "question": "What is the student asking about?",
            "options": ["The library location", "The time", "The restroom", "The exit"],
            "correct_answer": "The library location",
            "explanation": "The student asks 'すみません、図書館はどこですか？' which means 'Excuse me, where is the library?'"
        }}"""
        
        result = self.rag_system.llm.generate_response(prompt)
        try:
            response = eval(result)
            return PracticeItem(
                question=response['question'],
                context=response['formatted_dialogue'],  # Use formatted dialogue with speaker labels
                options=response['options'],
                correct_answer=response['correct_answer'],
                explanation=response['explanation'],
                type="dialogue"
            )
        except Exception:
            # Improved fallback with formatted dialogue
            return PracticeItem(
                question="What is this conversation about?",
                context="A: こんにちは。\nB: こんにちは、元気ですか。\nA: はい、元気です。",
                options=["A greeting", "Asking directions", "Ordering food", "Making plans"],
                correct_answer="A greeting",
                explanation="This is a basic greeting dialogue where two people exchange こんにちは (hello) and ask about wellbeing.",
                type="dialogue"
            )

    def _generate_vocabulary_quiz(self, context: str) -> PracticeItem:
        """Generate a vocabulary quiz item"""
        prompt = f"""From this text, select a Japanese word and create a vocabulary quiz:
        {context}
        
        Generate a JSON response with:
        1. target_word: A Japanese word from the text
        2. reading: The furigana reading in hiragana
        3. display_sentence: The sentence containing the word (target word should be wrapped in ** for highlighting)
        4. question: Ask about the meaning of the target word
        5. options: Four possible meanings (one correct)
        6. correct_answer: The correct meaning
        7. explanation: Brief explanation including the word's reading and usage
        
        Example format:
        {{
            "target_word": "食べる",
            "reading": "たべる",
            "display_sentence": "私は寿司を**食べる**のが好きです。",
            "question": "What does '食べる (たべる)' mean in this sentence?",
            "options": ["to eat", "to drink", "to cook", "to buy"],
            "correct_answer": "to eat",
            "explanation": "'食べる' (taberu) is a verb meaning 'to eat'. Reading: たべる (taberu)"
        }}"""
        
        result = self.rag_system.llm.generate_response(prompt)
        try:
            response = eval(result)
            # Include reading in question and explanation if available
            question = response['question']
            if 'reading' in response:
                explanation = f"{response['explanation']}\nWord: {response['target_word']} ({response['reading']})\nExample: {response['display_sentence']}"
            else:
                explanation = f"{response['explanation']}\nWord: {response['target_word']}\nExample: {response['display_sentence']}"
                
            return PracticeItem(
                question=question,
                context=response['display_sentence'],
                options=response['options'],
                correct_answer=response['correct_answer'],
                explanation=explanation,
                type="vocabulary"
            )
        except Exception:
            # Fallback with reading included
            return PracticeItem(
                question="What does '食べる (たべる)' mean in this sentence?",
                context="私は寿司を**食べる**のが好きです。",
                options=["to eat", "to drink", "to cook", "to buy"],
                correct_answer="to eat",
                explanation="Basic vocabulary: '食べる' (たべる) means 'to eat'",
                type="vocabulary"
            )

    def _generate_listening_exercise(self, context: str) -> PracticeItem:
        """Generate a listening comprehension exercise"""
        prompt = f"""Create a listening comprehension question with clear speaker roles:
        {context}
        
        Generate a JSON response with:
        1. formatted_dialogue: A clear dialogue with speaker labels and natural pauses
        2. question: A listening comprehension question
        3. options: Four possible answers (one correct)
        4. correct_answer: The correct answer choice
        5. explanation: Explanation focusing on what was heard
        6. speakers: List of speaker names in the dialogue
        7. segments: Array of text segments with speaker IDs
        
        Example format:
        {{
            "formatted_dialogue": "Guide: いらっしゃいませ。\\nVisitor: すみません、トイレはどこですか。\\nGuide: あ、2階です。エレベーターの隣です。\\nVisitor: ありがとうございます。",
            "question": "Where did the guide say the restroom was located?",
            "options": ["On the second floor", "Near the entrance", "On the first floor", "In the basement"],
            "correct_answer": "On the second floor",
            "explanation": "The guide says '2階です' (ni-kai desu) meaning 'it's on the second floor' and adds that it's next to the elevator.",
            "speakers": ["Guide", "Visitor"],
            "segments": [
                {{"speaker": "Guide", "text": "いらっしゃいませ"}},
                {{"speaker": "Visitor", "text": "すみません、トイレはどこですか"}},
                {{"speaker": "Guide", "text": "あ、2階です。エレベーターの隣です"}},
                {{"speaker": "Visitor", "text": "ありがとうございます"}}
            ]
        }}"""
        
        result = self.rag_system.llm.generate_response(prompt)
        try:
            response = eval(result)
            
            # Generate audio for each dialogue segment
            audio_files = []
            available_voices = {
                speaker: voice['id'] 
                for speaker, voice in zip(response['speakers'], self.available_voices)
            }
            
            # Generate audio for each segment with consistent voice per speaker
            segments = response.get('segments', [])
            for segment in segments:
                speaker = segment['speaker']
                text = segment['text']
                voice_id = available_voices.get(speaker, "Mizuki")
                
                # Try to generate audio
                audio_file = self.audio_generator.generate_audio(text, voice_id)
                if audio_file:
                    audio_files.append({
                        'file': audio_file,
                        'speaker': speaker,
                        'text': text
                    })
            
            # Get cache stats after generation
            cache_stats = self.audio_generator.get_cache_stats()
            print(f"[AUDIO] Cache status: {cache_stats['cache_size_mb']}MB used of {cache_stats['max_size_mb']}MB")
            
            return PracticeItem(
                question=response['question'],
                context=response['formatted_dialogue'],
                options=response['options'],
                correct_answer=response['correct_answer'],
                explanation=response['explanation'],
                type="listening",
                audio_url=audio_files[0]['file'] if audio_files else None  # For now, use first audio file
            )
        except Exception as e:
            print(f"[AUDIO] Error in listening exercise generation: {str(e)}")
            # Fallback with basic dialogue
            fallback_text = "いらっしゃいませ。"
            audio_file = self.audio_generator.generate_audio(fallback_text, "Mizuki")
            return PracticeItem(
                question="What did you hear in the greeting?",
                context="Staff: いらっしゃいませ。",
                options=["Welcome", "Goodbye", "Thank you", "Excuse me"],
                correct_answer="Welcome",
                explanation="You heard 'いらっしゃいませ' (irasshaimase) which means 'welcome'",
                type="listening",
                audio_url=audio_file
            )

    def check_answer(self, practice_item: PracticeItem, user_answer: str) -> Dict:
        """Check user's answer and provide feedback"""
        is_correct = user_answer == practice_item.correct_answer
        
        # Update session statistics
        self.current_session["total_questions"] += 1
        if is_correct:
            self.current_session["score"] += 1
            
        # Record practice history
        self.current_session["practice_history"].append({
            "timestamp": datetime.now().isoformat(),
            "practice_type": practice_item.type,
            "question": practice_item.question,
            "user_answer": user_answer,
            "correct_answer": practice_item.correct_answer,
            "is_correct": is_correct
        })
        
        return {
            "is_correct": is_correct,
            "explanation": practice_item.explanation,
            "correct_answer": practice_item.correct_answer,
            "context": practice_item.context,
            "score": f"{self.current_session['score']}/{self.current_session['total_questions']}"
        }

    def get_session_stats(self) -> Dict:
        """Get current session statistics"""
        return {
            "score": self.current_session["score"],
            "total_questions": self.current_session["total_questions"],
            "accuracy": (self.current_session["score"] / self.current_session["total_questions"] * 100 
                        if self.current_session["total_questions"] > 0 else 0),
            "practice_history": self.current_session["practice_history"][-5:]  # Last 5 practices
        }

    def reset_session(self) -> None:
        """Reset the current practice session"""
        self.current_session = {
            "score": 0,
            "total_questions": 0,
            "practice_history": []
        }