import sys
import os
import time
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.getcwd())
load_dotenv()

from aixiaoliang_agent.app import create_agent

# Initialize Agent
agent = create_agent()

# Test Cases covering 4 categories
TEST_QUESTIONS = [
    # Category 1: Valuation (Pitfall: PE vs PE_TTM)
    "1. 平安银行现在的滚动市盈率是多少？", 
    "2. 帮我查一下贵州茅台的静态PE和股息率。",
    
    # Category 2: Market Data (Pitfall: Units)
    "3. 万科A昨天的成交量是多少？注意单位。",
    "4. 宁德时代今天的成交额是多少千元？",
    
    # Category 3: Financials (Pitfall: Key guessing)
    "5. 招商银行的净资产收益率(ROE)是多少？",
    "6. 查一下迈瑞医疗的毛利率。",
    "7. 爱尔眼科的总营收是多少？",
    
    # Category 4: Semantic Search (Pitfall: Slang)
    "8. 哪只银行股的分红率最高？",
    "9. 查一下‘量比’大于2的某种股票（举例即可）。",
    
    # Category 5: Complex/Combined
    "10. 筛选出市盈率小于10且股息率大于5%的股票。",
]

def run_tests():
    log_file = "test_results_log.txt"
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("=== RAG Agent Benchmark Test ===\n")
        
    for i, q in enumerate(TEST_QUESTIONS):
        print(f"\n\n>>> Running Test [{i+1}/10]: {q}")
        session_id = f"test_session_{i}"
        
        full_response = ""
        print("Agent is thinking...")
        
        # Capture stream
        start_time = time.time()
        for response_chunk in agent.run(q, history=[], session_id=session_id, stream_mode="full"):
            full_response = response_chunk
            
        duration = time.time() - start_time
        
        # Minimal console output
        print(f"Finished in {duration:.2f}s")
        
        # Log to file for detailed analysis
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"\n\n{'='*50}\n")
            f.write(f"Question {i+1}: {q}\n")
            f.write(f"Duration: {duration:.2f}s\n")
            f.write(f"Response:\n{full_response}\n")
            
        # Analysis heuristics
        if "search_knowledge" in full_response:
             print("✅ Tool Used: search_knowledge")
        else:
             print("⚠️ Warning: Did not use search_knowledge")

if __name__ == "__main__":
    run_tests()
