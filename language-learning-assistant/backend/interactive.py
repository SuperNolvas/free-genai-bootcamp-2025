from typing import Dict, List, Optional
import random
from dataclasses import dataclass
from datetime import datetime
from .rag import RAGSystem

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
        self.current_session = {
            "score": 0,
            "total_questions": 0,
            "practice_history": []
        }
    
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
        
        Example format:
        {{
            "formatted_dialogue": "Guide: いらっしゃいませ。\nVisitor: すみません、トイレはどこですか。\nGuide: あ、2階です。エレベーターの隣です。\nVisitor: ありがとうございます。",
            "question": "Where did the guide say the restroom was located?",
            "options": ["On the second floor", "Near the entrance", "On the first floor", "In the basement"],
            "correct_answer": "On the second floor",
            "explanation": "The guide says '2階です' (ni-kai desu) meaning 'it's on the second floor' and adds that it's next to the elevator."
        }}"""
        
        result = self.rag_system.llm.generate_response(prompt)
        try:
            response = eval(result)
            return PracticeItem(
                question=response['question'],
                context=response['formatted_dialogue'],
                options=response['options'],
                correct_answer=response['correct_answer'],
                explanation=response['explanation'],
                type="listening",
                audio_url=None  # Future: Add audio URL
            )
        except Exception:
            # Improved fallback with clear dialogue structure
            return PracticeItem(
                question="What did the visitor ask about?",
                context="Staff: いらっしゃいませ。\nVisitor: すみません、駅はどこですか。\nStaff: まっすぐ行って、右です。\nVisitor: ありがとうございます。",
                options=["The station location", "The time", "The restroom", "The entrance"],
                correct_answer="The station location",
                explanation="The visitor asks 'すみません、駅はどこですか。' meaning 'Excuse me, where is the station?'",
                type="listening"
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