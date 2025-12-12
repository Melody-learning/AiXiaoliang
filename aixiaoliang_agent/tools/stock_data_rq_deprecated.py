import os
import rqdatac
from dotenv import load_dotenv
from .registry import register_tool

load_dotenv()

_IS_INIT = False

import time

def ensure_rq_init(force_reinit=False):
    global _IS_INIT
    if _IS_INIT and not force_reinit:
        return
    
    _IS_INIT = False 
    license_key = os.getenv("RQ_LICENSE_KEY")
    if not license_key:
        print("[!] Error: RQ_LICENSE_KEY is missing in environment.")
        return

    # Retry logic for initialization (competing for connection slot)
    max_retries = 5
    for attempt in range(max_retries):
        try:
            print(f"[*] RQData Init Attempt {attempt+1}/{max_retries}...")
            rqdatac.init(username=license_key, password=license_key)
            _IS_INIT = True
            print("[*] RQData initialized successfully.")
            return
        except Exception as e:
            print(f"[!] Init failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2) # Wait 2s before retry
            else:
                print("[!] Max retries reached for RQData init.")

import functools

def retry_rq_call(func):
    """Decorator to retry RQ API calls on auth failure."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        for attempt in range(3):
            try:
                ensure_rq_init()
                return func(*args, **kwargs)
            except Exception as e:
                error_msg = str(e)
                # Check for common auth/connection errors
                if "Authentication failed" in error_msg or "quota exceeded" in error_msg or "not initialized" in error_msg:
                    print(f"[!] RQ Call failed ({error_msg}). Retrying {attempt+1}/3...")
                    ensure_rq_init(force_reinit=True)
                    time.sleep(1) # Wait 1s before retry
                else:
                    raise e
        return func(*args, **kwargs)
    return wrapper

@register_tool(description="Get the current price of a stock. Symbol format: '000001.XSHE' or '600000.XSHG'.")
@retry_rq_call
def get_current_price(order_book_id: str):
    """
    Returns the last price of the given stock.
    """
    try:
        snapshot = rqdatac.current_snapshot(order_book_id)
        return snapshot.last
    except Exception as e:
        return f"Error fetching price: {e}"

@register_tool(description="Get historical daily data for a stock.")
@retry_rq_call
def get_history(order_book_id: str, start_date: str, end_date: str):
    """
    Returns historical data as a pandas DataFrame (converted to string/dict for the agent view).
    """
    try:
        df = rqdatac.get_price(order_book_id, start_date=start_date, end_date=end_date, frequency='1d')
        return df
    except Exception as e:
        return f"Error fetching history: {e}"

@register_tool(description="Search for a stock code by name. Example: 'Ping An' -> '000001.XSHE'. Returns a LIST of dictionaries with keys 'order_book_id', 'symbol', 'industry_name'.")
@retry_rq_call
def search_stock(keyword: str):
    """
    Search for stock order_book_id (symbol) by display name or pinyin.
    Returns: List[Dict] or empty list.
    """
    try:
        # User might provide Chinese or English
        insts = rqdatac.all_instruments(type='CS') # CS = Common Stock
        # Simple local filtering
        matches = insts[insts['symbol'].str.contains(keyword, case=False, na=False) | 
                         insts['abbrev_symbol'].str.contains(keyword, case=False, na=False)]
        
        if matches.empty:
             return []
             
        # Return top 5 matches as list of dicts
        # Rename 'order_book_id' to 'code' for simpler agent usage if preferred, but keeping original is safer
        records = matches.head(5)[['order_book_id', 'symbol', 'industry_name']].to_dict(orient='records')
        return records
    except Exception as e:
        return f"Error searching stock: {e}"

@register_tool(description="Get fundamental data (PE, PB, Market Cap, Revenue, etc.) for a stock. Returns a DICTIONARY values.")
@retry_rq_call
def get_fundamentals_data(order_book_id: str):
    """
    Returns key financial indicators for the given stock for the most recent trading day.
    Returns: Dict with keys ['pe_ratio', 'pb_ratio', 'market_cap', 'return_on_equity', 'revenue', 'net_profit']
    """
    ensure_rq_init()
    try:
        # Querying fundamentals
        q = rqdatac.query(
            rqdatac.fundamentals.eod_derivative_indicator.pe_ratio,
            rqdatac.fundamentals.eod_derivative_indicator.pb_ratio,
            rqdatac.fundamentals.eod_derivative_indicator.market_cap,
            rqdatac.fundamentals.financial_indicator.return_on_equity, # ROE
            rqdatac.fundamentals.income_statement.total_operating_revenue, # Revenue
            rqdatac.fundamentals.income_statement.net_profit # Net Profit
        ).filter(
            rqdatac.fundamentals.stock_code.in_([order_book_id])
        )
        
        # Get data for today (or latest available)
        df = rqdatac.get_fundamentals(q, entry_date=None, interval='1d', report_quarter=False)
        
        if df is None or df.empty:
             return {}

        # Convert to dictionary (first row)
        # Result columns: pe_ratio, pb_ratio, market_cap, return_on_equity, total_operating_revenue, net_profit
        data = df.iloc[0].to_dict()
        
        # Normalize keys for agent (optional, but good for stability)
        # RQ returns generic names, let's keep them but ensure specific names are clear
        normalized = {
            'pe_ratio': data.get('pe_ratio'),
            'pb_ratio': data.get('pb_ratio'),
            'market_cap': data.get('market_cap'),
            'roe': data.get('return_on_equity'),
            'revenue': data.get('total_operating_revenue'),
            'net_profit': data.get('net_profit')
        }
        return normalized
    except Exception as e:
        return f"Error fetching fundamentals: {e}"
