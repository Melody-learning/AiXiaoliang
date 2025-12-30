import os
import google.generativeai as genai
from .registry import register_tool
from dotenv import load_dotenv

load_dotenv()

@register_tool(description="Search the Data Dictionary for correct field names and Tool usage. Use this BEFORE writing stock data code.")
def search_knowledge(query: str) -> str:
    """
    Retrieves information from the Project Data Dictionary (knowledge/data_dictionary.md).
    Useful for finding:
    - Correct API keys for Tushare (e.g., 'pe_ttm', 'dividend_yield').
    - Unit definitions and code examples.
    
    Args:
        query: The natural language question, e.g., "What is the key for dividend yield?"
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return "Error: GOOGLE_API_KEY is missing."
        
    # Use the same configuration as the main agent
    genai.configure(api_key=api_key, transport="rest")
    
    # Locate the dictionary file
    file_path = os.path.join(os.getcwd(), 'knowledge', 'data_dictionary.md')
    if not os.path.exists(file_path):
        return f"Error: Knowledge base file not found at {file_path}"
        
    try:
        # Load dictionary content directly (Small enough for context)
        with open(file_path, 'r', encoding='utf-8') as f:
            dictionary_content = f.read()

        model_name = os.getenv("MODEL_NAME", "gemini-3-flash-preview")
        model = genai.GenerativeModel(model_name) # Consistency with main agent
        
        prompt = f"""
        You are a Data Dictionary Assistant. Use the provided documentation to answer the user's question accurately.
        
        [Documentation Content]
        {dictionary_content}
        
        User Question: {query}
        
        Instructions:
        1. Only answer based on the provided documentation.
        2. When identifying a field, ALWAYS return:
           - The exact '字段名 (Key)'
           - The '代码示例 (Usage Example)' (from the "MUST READ" section)
        3. Be concise and prioritize accuracy in field names.
        """
        
        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"Error searching knowledge: {e}"
