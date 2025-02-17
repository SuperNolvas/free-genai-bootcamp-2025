import streamlit as st
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_vocabulary(category):
    # Prepare the prompt for OpenAI
    prompt = f"""Generate a vocabulary list for the category '{category}' in Russian and English.
    Include 10 words or phrases. For each entry, provide:
    - The Russian word/phrase
    - English translation
    - Part of speech
    - Category
    
    Format the response as a JSON object with the structure shown in the example below:
    {{
      "vocabulary": [
        {{
          "russian": "привет",
          "english": "hello",
          "partOfSpeech": "interjection",
          "category": "greetings"
        }}
      ]
    }}
    """

    # Call OpenAI API
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful language learning assistant that generates vocabulary lists in JSON format."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    # Parse the response
    try:
        return json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        return {"error": "Failed to generate valid JSON response"}

def main():
    st.set_page_config(page_title="Vocabulary Importer", page_icon="📚")
    
    st.title("📚 Vocabulary Importer")
    st.markdown("""
    Generate vocabulary lists by entering a thematic category. The tool will create a structured JSON output
    that you can copy and use in your application.
    """)

    # API Key input
    api_key = st.text_input("OpenAI API Key", type="password", help="Enter your OpenAI API key")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key

    # Category input
    category = st.text_input("Enter vocabulary category", 
                            placeholder="e.g., food, animals, professions",
                            help="Enter a thematic category for vocabulary generation")

    # Generate button
    if st.button("Generate Vocabulary"):
        if not api_key:
            st.error("Please enter your OpenAI API key first")
            return
            
        with st.spinner("Generating vocabulary..."):
            result = generate_vocabulary(category)
            
            if "error" in result:
                st.error(result["error"])
            else:
                # Format JSON with indentation
                formatted_json = json.dumps(result, indent=2, ensure_ascii=False)
                
                # Display JSON in a code block
                st.code(formatted_json, language="json")
                
                # Add copy button
                if st.button("Copy to Clipboard"):
                    st.write("✅ Copied to clipboard!")

if __name__ == "__main__":
    main()