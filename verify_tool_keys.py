
from aixiaoliang_agent.tools.stock_data import get_fundamentals_data

print("Fetching data for 000001.SZ...")
data = get_fundamentals_data('000001.SZ')

keys = list(data.keys())
print(f"Keys returned: {keys}")

if 'pe_ttm' in keys:
    print("PASS: 'pe_ttm' is present.")
else:
    print("FAIL: 'pe_ttm' is MISSING.")

if 'pe_ratio_ttm' not in keys:
    print("PASS: 'pe_ratio_ttm' is correctly REMOVED.")
else:
    print("FAIL: 'pe_ratio_ttm' is still present (Snake legs!).")
