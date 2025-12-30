import os
import sys
import gradio as gr
from dotenv import load_dotenv

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aixiaoliang_agent.agent.code_agent import CodeAgent
from aixiaoliang_agent.tools.registry import default_registry
import aixiaoliang_agent.tools.stock_data
import aixiaoliang_agent.tools.knowledge_tool

# Load env
load_dotenv()

def create_agent():
    tools = default_registry.get_tools()
    model_name = os.getenv("MODEL_NAME", "gemini-3-pro-preview")
    return CodeAgent(model_name=model_name, tools=tools)

agent = create_agent()


import time
import uuid

def generate_session_id():
    # Use UUID for unique session ID
    return f"session_{int(time.time())}_{str(uuid.uuid4())[:8]}"

def predict(message, history, session_id):
    """
    Generator function for Gradio ChatInterface.
    """
    if not session_id:
        session_id = generate_session_id()
    
    print(f"DEBUG: message={message}, history={history}")
    formatted_history = []
    for item in history:
        # Robust unpacking for different Gradio versions
        user_msg = None
        bot_msg = None
        
        # Case 1: List/Tuple (Old Gradio) -> [user, bot]
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            user_msg = item[0]
            bot_msg = item[1]
        
        # Case 2: Dictionary (New Gradio ChatMessage)
        elif isinstance(item, dict):
            role = item.get('role')
            content = item.get('content')
            
            # Content might be a string or a list of dicts [{'text': ...}]
            text_content = ""
            if isinstance(content, str):
                text_content = content
            elif isinstance(content, list):
                # Join text parts
                for part in content:
                    if isinstance(part, dict) and 'text' in part:
                        text_content += part['text']
                    elif isinstance(part, str): # Fallback
                        text_content += part
            
            if role == 'user':
                # formatted_history expects "User: ..."
                # logic requires pairing... wait.
                # CodeAgent expects a list of strings: ["User: ...", "Assistant: ..."]
                # If history is a flat list of dicts (user, assistant, user, assistant...)
                # We can just append directly based on role.
                if text_content: formatted_history.append(f"User: {text_content}")
            elif role == 'assistant':
                if text_content: formatted_history.append(f"Assistant: {text_content}")
                
        # If we got tuple unpacking above
        if user_msg: formatted_history.append(f"User: {user_msg}")
        if bot_msg: formatted_history.append(f"Assistant: {bot_msg}")
        
    # Use 'full' mode so CodeAgent manages the buffer and replacement
    for buffer in agent.run(message, history=formatted_history, stream_mode="full", session_id=session_id):
        yield buffer

with gr.Blocks() as demo:
    session_state = gr.State(generate_session_id)
    
    chatbot = gr.ChatInterface(
        fn=predict,
        additional_inputs=[session_state],
        title="AiXiaoliang 2.0 (A-Share Agent)",
        description="Ask me about A-share stocks. I can search codes, check prices, and analyze fundamentals.",
        # examples removed to avoid 'list of lists' error with additional_inputs
        fill_height=True,
    )


if __name__ == "__main__":
    try:
        # Load Env (Force reload if packaged)
        load_dotenv()
        
        # FIX: Ensure localhost traffic bypasses the proxy
        if "NO_PROXY" not in os.environ:
            os.environ["NO_PROXY"] = "localhost,127.0.0.1,::1"
        
        port = int(os.getenv("APP_PORT", 7860))
        print(f"[*] Starting AiXiaoliang on port {port}...")
        
        demo.launch(
            server_name="127.0.0.1", 
            server_port=port, 
            share=False
        )
    except Exception as e:
        import traceback
        print("\n" + "!"*50)
        print("CRITICAL ERROR: Application failed to start.")
        print(f"Error: {e}")
        print("Details:")
        traceback.print_exc()
        print("!"*50 + "\n")
        
        input("Press Enter to exit...")
