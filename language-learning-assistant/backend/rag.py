from typing import List, Dict, Optional
import os
import json
import traceback
from datetime import datetime
from sentence_transformers import SentenceTransformer
import chromadb
import boto3
from chromadb.utils import embedding_functions

class LLMInterface:
    """Interface for LLM interactions"""
    def __init__(self, model_id: str = "amazon.nova-micro-v1:0"):
        try:
            print("[LLM] Initializing Bedrock client...")
            self.bedrock_client = boto3.client('bedrock-runtime', region_name="us-east-1")
            self.model_id = model_id
            print(f"[LLM] Using Nova Micro model: {model_id}")
            
        except Exception as e:
            print(f"[LLM ERROR] Error initializing Bedrock client: {str(e)}")
            print(f"[LLM ERROR] {traceback.format_exc()}")
            self.bedrock_client = None

    def generate_response(self, prompt: str) -> str:
        """Generate response from LLM"""
        if not self.bedrock_client:
            return "LLM not available - Bedrock client not initialized"
        
        try:
            print("[LLM] Preparing request for Nova Micro...")
            # Format specifically for Nova Micro API requirements
            body = {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": 512,
                    "temperature": 0.7,
                    "stopSequences": []
                }
            }
            
            print("[LLM] Sending request to Nova Micro...")
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body)
            )
            
            print("[LLM] Processing Nova Micro response...")
            response_body = json.loads(response.get('body').read())
            return response_body.get('outputText', "No response generated")
            
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            print(f"[LLM ERROR] {error_msg}")
            print(f"[LLM ERROR] {traceback.format_exc()}")
            return error_msg

class RAGSystem:
    def __init__(self, collection_name: str = "jlptn5-listening-comprehension"):
        """Initialize RAG system with ChromaDB and embedding model"""
        self.debug_logs = []
        self.query_cache = {}
        self.log("Initializing RAG System...")
        
        try:
            # Initialize embedding model
            try:
                self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name="intfloat/multilingual-e5-large",
                    device="cpu"
                )
                self.log("✓ Embedding model initialized")
            except Exception as embed_error:
                self.log(f"! Error initializing primary model: {str(embed_error)}")
                self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name="all-MiniLM-L6-v2",
                    device="cpu"
                )
                self.log("✓ Fallback embedding model initialized")
            
            # Set up ChromaDB with proper persistence
            persist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
            os.makedirs(persist_dir, exist_ok=True)
            
            # Initialize ChromaDB with proper settings
            try:
                self.client = chromadb.PersistentClient(
                    path=persist_dir,
                    settings=chromadb.Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
                self.log("✓ ChromaDB client initialized")
                
                # Try to get existing collection
                try:
                    self.collection = self.client.get_collection(
                        name=collection_name,
                        embedding_function=self.embedding_function
                    )
                    doc_count = self.collection.count()
                    self.log(f"✓ Retrieved existing collection with {doc_count} documents")
                except Exception:
                    # Create new collection if it doesn't exist
                    self.collection = self.client.create_collection(
                        name=collection_name,
                        embedding_function=self.embedding_function,
                        metadata={"description": "Japanese language learning dialogues"}
                    )
                    self.log("✓ Created new collection")
            except Exception as db_error:
                self.log(f"! Error with ChromaDB: {str(db_error)}")
                raise
            
            # Initialize LLM interface
            self.llm = LLMInterface()
            self.log("✓ LLM interface initialized")
            
            self.feedback_history = []
            self.log("✓ Feedback system initialized")
            
        except Exception as e:
            error_msg = f"Critical error initializing RAG system: {str(e)}"
            self.log(f"! {error_msg}")
            raise

    def log(self, message: str) -> None:
        """Add a log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.debug_logs.append(f"[{timestamp}] {message}")
        print(f"[RAG] {message}")  # Also print to console for debugging
    
    def get_logs(self) -> List[str]:
        """Return all debug logs"""
        return self.debug_logs

    def reset_collection(self) -> None:
        """Reset the collection by deleting and recreating it"""
        try:
            collection_name = self.collection.name
            self.log(f"Resetting collection: {collection_name}")
            
            # Delete existing collection
            self.client.delete_collection(collection_name)
            self.log("✓ Deleted existing collection")
            
            # Create new collection
            self.collection = self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function,
                metadata={"description": "Japanese language learning dialogues"}
            )
            self.log("✓ Created new collection")
            
            # Clear query cache
            self.query_cache = {}
            self.log("✓ Query cache cleared")
            
        except Exception as e:
            error_msg = f"Error resetting collection: {str(e)}"
            self.log(f"! {error_msg}")
            raise

    def preprocess_japanese_text(self, text: str) -> List[str]:
        """Split Japanese text into meaningful chunks with improved handling"""
        # Split on common Japanese sentence endings and question marks
        sentences = []
        current_sentence = ""
        
        # Handle both full-width and half-width characters
        end_markers = ["。", "？", "!", "．", "\n", "?", ".", "!", "…"]
        
        for char in text:
            current_sentence += char
            if char in end_markers and current_sentence.strip():
                # Clean up the sentence
                cleaned = current_sentence.strip().replace('\n', ' ').replace('  ', ' ')
                if cleaned:
                    sentences.append(cleaned)
                current_sentence = ""
                
        if current_sentence.strip():
            cleaned = current_sentence.strip().replace('\n', ' ').replace('  ', ' ')
            if cleaned:
                sentences.append(cleaned)
            
        # Group sentences into chunks of reasonable size
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # Check both character count and byte length for better Japanese text handling
            if (len(current_chunk) + len(sentence) > 500 or 
                len(current_chunk.encode('utf-8')) + len(sentence.encode('utf-8')) > 1500):
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
        try:
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
                    chunk_metadata.update({
                        "chunk_id": chunk_counter,
                        "timestamp": datetime.now().isoformat()
                    })
                    all_metadatas.append(chunk_metadata)
                    chunk_ids.append(f"chunk_{chunk_counter}")
                    chunk_counter += 1
            
            # Add chunks to collection with error handling
            if all_chunks:
                try:
                    self.collection.add(
                        documents=all_chunks,
                        metadatas=all_metadatas,
                        ids=chunk_ids
                    )
                    print(f"Successfully added {len(all_chunks)} chunks to collection")
                except Exception as add_error:
                    print(f"Error adding documents: {str(add_error)}")
                    # Try to persist changes even if there's an error
                    self.client.persist()
                    raise
        except Exception as e:
            print(f"Error in add_documents: {str(e)}")
            raise

    def query(self, query_text: str, n_results: int = 3) -> Dict:
        """Query the RAG system"""
        self.log(f"Processing query: {query_text}")
        
        # Check cache first
        cache_key = f"{query_text}_{n_results}"
        if cache_key in self.query_cache:
            self.log("✓ Retrieved result from cache")
            return self.query_cache[cache_key]
        
        try:
            # Verify collection state
            doc_count = self.collection.count()
            self.log(f"Collection contains {doc_count} documents")
            
            if doc_count == 0:
                self.log("! No documents in collection")
                return {
                    "answer": "No documents found in collection. Please load some transcripts first.",
                    "contexts": [],
                    "metadata": {
                        "timestamp": datetime.now().isoformat(),
                        "status": "empty_collection"
                    },
                    "logs": self.debug_logs
                }
            
            # Get relevant documents
            self.log(f"Retrieving {n_results} most relevant contexts...")
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                include=['documents', 'distances', 'metadatas']
            )
            
            contexts = results['documents'][0]
            distances = results.get('distances', [[]])[0]
            metadatas = results.get('metadatas', [[]])[0]
            
            self.log(f"✓ Retrieved {len(contexts)} relevant contexts")
            
            # Prepare prompt for LLM
            prompt = self._construct_prompt(query_text, contexts)
            
            # Generate LLM response
            self.log("Generating response from LLM...")
            answer = self.llm.generate_response(prompt)
            self.log("✓ Generated response")
            
            # Prepare result
            result = {
                "answer": answer,
                "contexts": contexts,
                "metadata": {
                    "num_contexts": len(contexts),
                    "query": query_text,
                    "timestamp": datetime.now().isoformat(),
                    "relevance_scores": [1 - d for d in distances] if distances else [],
                    "context_sources": [m.get('source', 'unknown') for m in metadatas] if metadatas else [],
                    "status": "success"
                },
                "logs": self.debug_logs
            }
            
            # Cache the result
            self.query_cache[cache_key] = result
            
            # Limit cache size
            if len(self.query_cache) > 100:
                oldest_key = next(iter(self.query_cache))
                del self.query_cache[oldest_key]
            
            return result
            
        except Exception as e:
            error_msg = f"Error during query: {str(e)}"
            self.log(f"! {error_msg}")
            
            try:
                # Attempt collection reset on error
                self.reset_collection()
                self.log("✓ Collection reset after error")
                return {
                    "answer": "An error occurred. The system has been reset. Please try again.",
                    "contexts": [],
                    "metadata": {
                        "error": str(e),
                        "timestamp": datetime.now().isoformat(),
                        "status": "error_reset"
                    },
                    "logs": self.debug_logs
                }
            except Exception as reset_error:
                reset_msg = f"Error during reset: {str(reset_error)}"
                self.log(f"! {reset_msg}")
                return {
                    "answer": f"Critical error occurred: {str(e)}",
                    "contexts": [],
                    "metadata": {
                        "error": str(e),
                        "reset_error": str(reset_error),
                        "timestamp": datetime.now().isoformat(),
                        "status": "critical_error"
                    },
                    "logs": self.debug_logs
                }

    def _construct_prompt(self, query_text: str, contexts: List[str]) -> str:
        """Construct the prompt for the LLM"""
        # Format prompt for Nova Micro
        context_text = "\n\n".join([
            f"Context {i+1}:\n{ctx.strip()}" 
            for i, ctx in enumerate(contexts)
        ])
        
        # Keep prompt concise for Nova Micro's context window
        return f"""Based on these Japanese dialogues, answer the following question:

{context_text}

Question: {query_text}

Instructions:
1. Use examples from the dialogues
2. Explain Japanese patterns found
3. Show both Japanese and English
4. Be concise and clear

Answer:"""

    def load_transcripts(self, transcript_dir: str) -> None:
        """Load transcripts from a directory"""
        try:
            documents = []
            metadatas = []
            
            # Reset collection before loading new transcripts
            self.reset_collection()
            self.log("✓ Collection reset before loading transcripts")
            
            for filename in os.listdir(transcript_dir):
                if filename.endswith(".txt"):
                    file_path = os.path.join(transcript_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            documents.append(content)
                            metadatas.append({
                                "source": filename,
                                "type": "transcript",
                                "timestamp": datetime.now().isoformat()
                            })
                            self.log(f"✓ Loaded transcript: {filename}")
                    except Exception as file_error:
                        self.log(f"! Error reading file {filename}: {str(file_error)}")
                        continue
            
            if documents:
                self.add_documents(documents, metadatas)
                self.log(f"✓ Added {len(documents)} documents to collection")
            else:
                self.log("! No valid documents found to load")
                
        except Exception as e:
            error_msg = f"Error loading transcripts: {str(e)}"
            self.log(f"! {error_msg}")
            raise

    def clear_cache(self) -> None:
        """Clear the query cache"""
        self.query_cache = {}
        self.log("Query cache cleared")
    
    def get_cache_stats(self) -> Dict:
        """Get statistics about the query cache"""
        try:
            # Get cache info
            cache_queries = list(self.query_cache.keys())
            cache_size = len(cache_queries)
            
            # Get query texts without n_results suffix
            recent_queries = [q.split('_')[0] for q in cache_queries[-5:]]
            
            return {
                "cache_size": cache_size,
                "cached_queries": recent_queries,
                "total_cached": cache_size,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.log(f"! Error getting cache stats: {str(e)}")
            return {
                "cache_size": 0,
                "cached_queries": [],
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def add_feedback(self, query: str, feedback: str, contexts: List[str]) -> None:
        """Add user feedback for a query"""
        try:
            feedback_entry = {
                "query": query,
                "feedback": feedback,
                "contexts": contexts,
                "timestamp": datetime.now().isoformat()
            }
            self.feedback_history.append(feedback_entry)
            self.log(f"✓ Added {feedback} feedback for query")
        except Exception as e:
            self.log(f"! Error adding feedback: {str(e)}")
            
    def get_feedback_stats(self) -> Dict:
        """Get statistics about user feedback"""
        try:
            total = len(self.feedback_history)
            if total == 0:
                return {
                    "total_feedback": 0,
                    "positive_rate": 0,
                    "recent_feedback": []
                }
                
            positive = sum(1 for f in self.feedback_history if f['feedback'] == 'positive')
            positive_rate = (positive / total) * 100
            
            recent = self.feedback_history[-5:]  # Last 5 feedback entries
            
            return {
                "total_feedback": total,
                "positive_feedback": positive,
                "positive_rate": positive_rate,
                "recent_feedback": recent
            }
        except Exception as e:
            self.log(f"! Error getting feedback stats: {str(e)}")
            return {
                "error": str(e),
                "total_feedback": 0,
                "recent_feedback": []
            }
            
    def clear_feedback(self) -> None:
        """Clear all feedback history"""
        try:
            self.feedback_history = []
            self.log("✓ Feedback history cleared")
        except Exception as e:
            self.log(f"! Error clearing feedback: {str(e)}")
            raise