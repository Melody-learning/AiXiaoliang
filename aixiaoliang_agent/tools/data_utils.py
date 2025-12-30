
from typing import Dict, Any, List

def normalize_stock_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Standardize a stock data record to ensure consistent keys across all tools.
    
    Rules:
    1. If 'ts_code' exists, ensure 'code' also exists and matches it.
    2. (Future) Add other standardizations here.
    """
    # Create a shallow copy to avoid mutating the original if needed, 
    # but here we usually want to enhance the record in place or return a new one.
    # Let's simple return a modified dictionary.
    
    new_record = record.copy()
    
    # Rule 1: 'code' alias for 'ts_code'
    # This accommodates Agent's strong bias towards using 'code' key
    if 'ts_code' in new_record and 'code' not in new_record:
        new_record['code'] = new_record['ts_code']
        
    return new_record

def normalize_stock_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Batch normalize a list of records.
    """
    return [normalize_stock_record(r) for r in records]

def create_envelope(data: Any, status: str = "success", error: str = None, meta: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Create a standardized response envelope for tools (Rich Signals Pattern).
    
    Args:
        data: The actual payload (List, Dict, etc.) or None.
        status: 'success', 'empty', or 'error'.
        error: Error message if status is 'error'.
        meta: Additional metadata (reason, hint, suggestion).
    
    Returns:
        Dict: Standardized JSON-like response.
    """
    return {
        "status": status,
        "data": data,
        "meta": meta or {},
        "error": error
    }
