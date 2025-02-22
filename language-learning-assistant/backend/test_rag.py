import os
from rag import RAGSystem
import traceback
import sys

def test_rag():
    rag = None
    try:
        # Initialize RAG system
        print("[TEST] Initializing RAG system...")
        rag = RAGSystem()
        print("[TEST] RAG system initialized successfully")
        
        # Load transcripts from directory
        transcript_dir = os.path.join(os.path.dirname(__file__), 'transcripts')
        if not os.path.exists(transcript_dir):
            print(f"[TEST ERROR] Transcript directory not found at {transcript_dir}")
            return
            
        print(f"[TEST] Loading transcripts from {transcript_dir}...")
        rag.load_transcripts(transcript_dir)
        print("[TEST] Transcripts loaded successfully")
        
        # Test queries
        test_queries = [
            "What are common greeting patterns in the dialogues?",
            "How are questions typically structured in JLPT N5 listening comprehension?",
            "What types of locations and situations appear in these conversations?",
            "How do people typically ask for directions in these dialogues?"
        ]
        
        for query in test_queries:
            print("\n" + "="*50)
            print(f"[TEST] Processing query: {query}")
            try:
                print("[TEST] Calling RAG query method...")
                result = rag.query(query)
                print("[TEST] Query processed successfully")
                
                print("\nRetrieved Contexts:")
                if result.get('contexts'):
                    for i, ctx in enumerate(result['contexts'], 1):
                        print(f"\n{i}. {ctx}")
                else:
                    print("[TEST] No contexts retrieved")
                    
                print("\nGenerated Answer:")
                print(result.get('answer', "No answer generated"))
                
                if 'metadata' in result:
                    print("\nMetadata:")
                    print(result['metadata'])
                
                # Print debug logs if available
                if 'logs' in result:
                    print("\nDebug Logs:")
                    for log in result['logs']:
                        print(log)
                    
            except Exception as query_error:
                print(f"[TEST ERROR] Error processing query: {str(query_error)}")
                print("[TEST ERROR] Traceback:")
                print(traceback.format_exc())
                
            print("="*50)
            
    except KeyboardInterrupt:
        print("\n[TEST] Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"[TEST ERROR] Critical error in test_rag: {str(e)}")
        print("[TEST ERROR] Full traceback:")
        print(traceback.format_exc())
        sys.exit(1)
    finally:
        if rag and hasattr(rag, 'get_logs'):
            print("\n[TEST] Final RAG System Logs:")
            for log in rag.get_logs():
                print(log)
        print("\n[TEST] Test completed")