import os
from rag import RAGSystem

def test_rag():
    # Initialize RAG system
    rag = RAGSystem()
    
    # Load transcripts from directory
    transcript_dir = os.path.join(os.path.dirname(__file__), 'transcripts')
    rag.load_transcripts(transcript_dir)
    
    # Test queries
    test_queries = [
        "What are common greeting patterns in the dialogues?",
        "How are questions typically structured in JLPT N5 listening comprehension?",
        "What types of locations and situations appear in these conversations?",
        "How do people typically ask for directions in these dialogues?"
    ]
    
    for query in test_queries:
        print("\n" + "="*50)
        print("\nQuery:", query)
        result = rag.query(query)
        
        print("\nRetrieved Contexts:")
        for i, ctx in enumerate(result['contexts'], 1):
            print(f"\n{i}. {ctx}")
        print("\nGenerated Answer:")
        print(result['answer'])
        print("="*50)

if __name__ == '__main__':
    test_rag()