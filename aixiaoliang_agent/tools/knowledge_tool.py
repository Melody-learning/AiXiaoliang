import os
import time
from google import genai
# from google.genai import types # types not strictly needed for basic usage
from .registry import register_tool
from dotenv import load_dotenv

load_dotenv()

_CLIENT = None

def get_gemini_client():
    global _CLIENT
    if _CLIENT:
        return _CLIENT
    
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[!] Error: GEMINI_API_KEY/GOOGLE_API_KEY is missing.")
        return None
        
    try:
        _CLIENT = genai.Client(api_key=api_key)
        return _CLIENT
    except Exception as e:
        print(f"[!] Gemini Client init failed: {e}")
        return None

@register_tool(description="Search the Data Dictionary for correct field names and Tool usage. Use this BEFORE writing stock data code.")
def search_knowledge(query: str):
    """
    Retrieves information from the Project Data Dictionary (knowledge/data_dictionary.md).
    Useful for finding:
    - Correct API keys for Tushare (e.g., 'pe' vs 'PE', 'vol' vs 'volume').
    - Unit definitions (e.g., is dividend yield % or nominal?).
    
    Args:
        query: The natural language question, e.g., "What is the key for dividend yield?"
    """
    client = get_gemini_client()
    if not client:
        return "Error: Gemini Client not initialized. Check API Key."

    # Locate the dictionary file
    # Assuming relative path from the project root. 
    # Current CWD is usually project root e:\aixiaoliang2.0
    file_path = os.path.join(os.getcwd(), 'knowledge', 'data_dictionary.md')
    
    if not os.path.exists(file_path):
        return f"Error: Knowledge base file not found at {file_path}"
        
    try:
        # Strategy: Upload file -> Generate Content (Long Context RAG)
        file_ref = client.files.upload(file=file_path, config={'mime_type': 'text/markdown'})
        
        # 2. Wait for processing (for text/markdown usually instant, but good practice)
        while file_ref.state.name == "PROCESSING":
             time.sleep(1)
             file_ref = client.files.get(name=file_ref.name)
             
        if file_ref.state.name == "FAILED":
            return "Error: Failed to process knowledge base file."

        # 3. Generate Answer
        # We use a lightweight model for this RAG task
        model_id = "gemini-2.0-flash-exp" # Or gemini-1.5-flash if 2.0 not available
        
        prompt = f"""
        You are a Data Dictionary Assistant. Use the provided documentation to answer the user's question.
        
        User Question: {query}
        
        Instructions:
        1. Only answer based on the provided file.
        2. When identifying a field, ALWAYS return:
           - The exact '字段名 (Key)'
           - The '代码示例 (Usage Example)' (from the "MUST READ" section)
        3. Do NOT summarize into a list without the code examples.
        4. Be concise but comprehensive regarding the syntax.
        """
        
        response = client.models.generate_content(
            model=model_id,
            contents=[file_ref, prompt]
        )
        return response.text

    except Exception as e:
        return f"Error searching knowledge: {e}"
