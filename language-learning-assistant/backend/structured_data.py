from typing import List, Dict, Optional
import boto3
from dataclasses import dataclass

@dataclass
class JLPTQuestion:
    introduction: str
    conversation: str
    question: str

class JLPTStructuredDataExtractor:
    def __init__(self, model_id: str = "amazon.nova-micro-v1:0"):
        """Initialize with Bedrock client"""
        self.bedrock_client = boto3.client('bedrock-runtime', region_name="us-east-1")
        self.model_id = model_id

    def _generate_structured_data(self, text: str) -> Optional[Dict]:
        """Use Bedrock to extract structured data from text"""
        prompt = f"""Extract the following components from this JLPT listening question text:
- Introduction (setup of the scenario)
- Conversation (the actual dialogue)
- Question (what is being asked)

Text to analyze:
{text}

Format your response as:
Introduction:
[the introduction text]
Conversation:
[the conversation text]
Question:
[the question text]

Only include these three sections, with no additional text or commentary."""

        try:
            messages = [{
                "role": "user",
                "content": [{"text": prompt}]
            }]
            
            response = self.bedrock_client.converse(
                modelId=self.model_id,
                messages=messages,
                inferenceConfig={"temperature": 0.1}  # Low temperature for more deterministic extraction
            )
            
            response_text = response['output']['message']['content'][0]['text']
            
            # Parse the response into our structure
            parts = response_text.split('\n')
            current_section = None
            sections = {'introduction': '', 'conversation': '', 'question': ''}
            
            for line in parts:
                line = line.strip()
                if line.lower().startswith('introduction:'):
                    current_section = 'introduction'
                elif line.lower().startswith('conversation:'):
                    current_section = 'conversation'
                elif line.lower().startswith('question:'):
                    current_section = 'question'
                elif current_section and line:
                    sections[current_section] += line + '\n'
            
            # Clean up the extracted sections
            sections = {k: v.strip() for k, v in sections.items()}
            
            return sections
            
        except Exception as e:
            print(f"Error in Bedrock processing: {str(e)}")
            return None

    def extract_questions(self, transcript: str) -> List[JLPTQuestion]:
        """
        Extract JLPT questions from a transcript
        
        Args:
            transcript (str): Full transcript text
            
        Returns:
            List[JLPTQuestion]: List of extracted questions with their components
        """
        # First, split the transcript into individual questions
        # This uses common JLPT patterns to identify question boundaries
        questions_raw = self._split_into_questions(transcript)
        
        # Process each question
        structured_questions = []
        for q_text in questions_raw:
            result = self._generate_structured_data(q_text)
            if result:
                question = JLPTQuestion(
                    introduction=result['introduction'],
                    conversation=result['conversation'],
                    question=result['question']
                )
                structured_questions.append(question)
        
        return structured_questions

    def _split_into_questions(self, transcript: str) -> List[str]:
        """Split full transcript into individual questions"""
        # Common JLPT question markers
        markers = ['Question', '問題', 'もんだい']
        
        # Use Bedrock to help identify question boundaries
        prompt = f"""Split this JLPT listening transcript into individual questions.
Each question typically starts with markers like 'Question', '問題', or 'もんだい'.

Transcript:
{transcript}

Format your response as:
---QUESTION START---
[question content]
---QUESTION END---
[repeat for each question]"""

        try:
            messages = [{
                "role": "user",
                "content": [{"text": prompt}]
            }]
            
            response = self.bedrock_client.converse(
                modelId=self.model_id,
                messages=messages,
                inferenceConfig={"temperature": 0.1}
            )
            
            response_text = response['output']['message']['content'][0]['text']
            
            # Split the response into questions
            questions = []
            current_question = []
            
            for line in response_text.split('\n'):
                if '---QUESTION START---' in line:
                    current_question = []
                elif '---QUESTION END---' in line and current_question:
                    questions.append('\n'.join(current_question).strip())
                elif current_question is not None:
                    current_question.append(line)
            
            return questions
            
        except Exception as e:
            print(f"Error splitting questions: {str(e)}")
            # Fallback: simple splitting by question markers
            questions = []
            current_question = []
            
            for line in transcript.split('\n'):
                if any(marker in line for marker in markers) and current_question:
                    questions.append('\n'.join(current_question))
                    current_question = []
                current_question.append(line)
                
            if current_question:
                questions.append('\n'.join(current_question))
                
            return questions

if __name__ == "__main__":
    # Example usage
    extractor = JLPTStructuredDataExtractor()
    sample_transcript = """
    Question 1
    You will hear a conversation at a restaurant.
    A: Welcome! Table for two?
    B: Yes, please. By the window if possible.
    A: Of course. Please follow me.
    What does the customer want?
    
    Question 2
    You will hear an announcement at a train station.
    [Train announcement in Japanese]
    When will the train arrive?
    """
    
    questions = extractor.extract_questions(sample_transcript)
    for i, q in enumerate(questions, 1):
        print(f"\nQuestion {i}:")
        print(f"Introduction: {q.introduction}")
        print(f"Conversation: {q.conversation}")
        print(f"Question: {q.question}")