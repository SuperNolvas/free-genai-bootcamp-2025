from typing import List, Dict, Optional
import os
import json
from sentence_transformers import SentenceTransformer
import chromadb
import boto3
from chromadb.utils import embedding_functions

class LLMInterface:
    """Interface for LLM interactions"""
    def __init__(self, model_id: str = "amazon.nova-micro-v1:0"):
        try:
            self.bedrock_client = boto3.client('bedrock-runtime', region_name="us-east-1")
            self.model_id = model_id
        except Exception as e:
            print(f"Error initializing Bedrock client: {str(e)}")
            self.bedrock_client = None

    def generate_response(self, prompt: str) -> str:
        """Generate response from LLM"""
        if not self.bedrock_client:
            return "LLM not available - Bedrock client not initialized"
        
        try:
            messages = [{
                "role": "user",
                "content": [{"text": prompt}]
            }]

            response = self.bedrock_client.converse(
                modelId=self.model_id,
                messages=messages,
                inferenceConfig={"temperature": 0.7}
            )
            return response['output']['message']['content'][0]['text']
        except Exception as e:
            print(f"Error details: {str(e)}")
            return f"Error generating response: {str(e)}"

class RAGSystem:
    def __init__(self, collection_name: str = "jlptn5-listening-comprehension"):
        """Initialize RAG system with ChromaDB and embedding model"""
        # Initialize embedding model - specifically good for Japanese
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="intfloat/multilingual-e5-large"
        )
        
        # Initialize ChromaDB
        self.client = chromadb.Client()
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function
        )
        
        # Initialize LLM interface
        self.llm = LLMInterface()

    def preprocess_japanese_text(self, text: str) -> List[str]:
        """Split Japanese text into meaningful chunks"""
        # Split on common Japanese sentence endings and question marks
        sentences = []
        current_sentence = ""
        
        for char in text:
            current_sentence += char
            if char in ["。", "？", "!", "．", "\n"] and current_sentence.strip():
                sentences.append(current_sentence.strip())
                current_sentence = ""
                
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
            
        # Group sentences into chunks of reasonable size
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) > 500:  # Reasonable chunk size
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
                
        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks

    def add_documents(self, documents: List[str], metadatas: Optional[List[Dict]] = None) -> None:
        """Add documents to the vector store with preprocessing"""
        all_chunks = []
        all_metadatas = []
        chunk_ids = []
        chunk_counter = 0
        
        for idx, doc in enumerate(documents):
            chunks = self.preprocess_japanese_text(doc)
            all_chunks.extend(chunks)
            
            # Create metadata for each chunk
            doc_metadata = metadatas[idx] if metadatas else {}
            for chunk in chunks:
                chunk_metadata = doc_metadata.copy()
                chunk_metadata["chunk_id"] = chunk_counter
                all_metadatas.append(chunk_metadata)
                chunk_ids.append(f"chunk_{chunk_counter}")
                chunk_counter += 1
        
        # Add chunks to collection
        if all_chunks:
            self.collection.add(
                documents=all_chunks,
                metadatas=all_metadatas,
                ids=chunk_ids
            )

    def query(self, query_text: str, n_results: int = 3) -> Dict:
        """Query the RAG system"""
        try:
            # Get relevant documents
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            
            # Construct prompt with retrieved context - simplified for Nova Micro
            contexts = results['documents'][0]
            
            prompt = f"""Analyze these Japanese language learning dialogues and answer the question.

Context:
{chr(10).join([f'• {ctx}' for ctx in contexts])}

Question: {query_text}

Give a clear and concise answer based only on the context provided."""

            # Generate response using LLM
            answer = self.llm.generate_response(prompt)
            
            return {
                "answer": answer,
                "contexts": contexts
            }
        except Exception as e:
            return {
                "answer": f"Error during query: {str(e)}",
                "contexts": []
            }

    def load_transcripts(self, transcript_dir: str) -> None:
        """Load transcripts from a directory"""
        documents = []
        metadatas = []
        
        try:
            for filename in os.listdir(transcript_dir):
                if filename.endswith(".txt"):
                    with open(os.path.join(transcript_dir, filename), 'r', encoding='utf-8') as f:
                        content = f.read()
                        documents.append(content)
                        metadatas.append({"source": filename})
            
            if documents:
                self.add_documents(documents, metadatas)
        except Exception as e:
            print(f"Error loading transcripts: {str(e)}")