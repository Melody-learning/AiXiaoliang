import sys
import io

def test_exec_capture():
    code = """
import sys
if __name__ == "__main__":
    print(f"Inside Sandbox: name={__name__}")
    print("Logic running")
"""
    
    old_stdout = sys.stdout
    redirected_output = io.StringIO()
    sys.stdout = redirected_output
    
    exec_globals = {"__name__": "__main__", "print": print}
    
    try:
        exec(code, exec_globals)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sys.stdout = old_stdout
        
    result = redirected_output.getvalue()
    print(f"Captured:\n{result}")

if __name__ == "__main__":
    test_exec_capture()
