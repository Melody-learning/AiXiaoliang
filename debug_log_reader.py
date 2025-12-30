
import json

import glob
import os

list_of_files = glob.glob('e:/aixiaoliang2.0/logs/session_*.jsonl') 
log_path = max(list_of_files, key=os.path.getctime)
print(f"Reading latest log: {log_path}")
with open(log_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

if not lines:
    print("Log file is empty.")
else:
    last_line = lines[-1]
    try:
        data = json.loads(last_line)
        print(f"Timestamp: {data.get('timestamp')}")
        steps = data.get('steps', [])
        print(f"Total Steps: {len(steps)}")
        
        if steps:
            last_step = steps[-1]
            print(f"Last Step Type: {last_step.get('type')}")
            print("Last Step Content (First 500 chars):")
            print(last_step.get('content', '')[:500])
            
            # Check for key phrases
            content = last_step.get('content', '')
            if 'search_knowledge' in content:
                print(" -> Contains 'search_knowledge'")
            if 'get_fundamentals_data' in content:
                print(" -> Contains 'get_fundamentals_data'")
    except json.JSONDecodeError:
        print("Last line is not valid JSON.")
