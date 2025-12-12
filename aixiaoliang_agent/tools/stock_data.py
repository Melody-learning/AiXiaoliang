import os
import tushare as ts
import pandas as pd
from dotenv import load_dotenv
from .registry import register_tool

load_dotenv()

_PRO = None
_IS_INIT = False

def ensure_tushare_init():
    global _PRO, _IS_INIT
    if _IS_INIT:
        return _PRO
    
    token = os.getenv("TUSHARE_TOKEN")
    if not token:
        print("[!] Error: TUSHARE_TOKEN is missing in environment.")
        return None

    try:
        # Set proxy for Tushare (Note: This specific token requires this internal proxy tunnel)
        os.environ["HTTP_PROXY"] = "http://tushare.xyz:5000"
        
        # Init Pro API
        _PRO = ts.pro_api(token)
        _IS_INIT = True
        print("[*] Tushare Pro initialized successfully.")
        return _PRO
    except Exception as e:
        print(f"[!] Tushare initialization failed: {e}")
        return None

@register_tool(description="Search for a stock code by name. Example: '平安' -> '000001.SZ'. Returns List[Dict].")
def search_stock(keyword: str):
    """
    Search for stock code (ts_code) by display name.
    """
    pro = ensure_tushare_init()
    if not pro:
        print("[!] Tushare not initialized.")
        return []
    
    try:
        # Tushare doesn't have a fuzzy search API like RQ, so we fetch basic list and filter locally
        # Cache this if possible in production
        df = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,industry')
        
        # Filter by name (contains)
        matches = df[df['name'].str.contains(keyword, case=False, na=False) | 
                     df['ts_code'].str.contains(keyword, case=False, na=False)]
        
        if matches.empty:
            return []
            
        # Return top 5 matches
        # Normalize keys: ts_code -> code, industry -> sector
        records = []
        for _, row in matches.head(5).iterrows():
            records.append({
                "code": row['ts_code'],
                "stock_code": row['ts_code'],
                "name": row['name'],
                "industry": row['industry']
            })
        return records
    except Exception as e:
        print(f"[!] Error searching stock: {e}")
        return []

@register_tool(description="Get the current price (or latest close) of a stock.")
def get_current_price(stock_code: str):
    """
    Returns the latest daily close price. Tushare basic interface is usually EOD.
    """
    pro = ensure_tushare_init()
    if not pro:
        return "Error: Tushare not initialized."
    
    try:
        # Get daily data for the symbol
        # stock_code format usually 000001.SZ or 600000.SH
        df = pro.daily(ts_code=stock_code, limit=1)
        if df.empty:
             return f"No price data found for {stock_code}."
        
        # Return the close price
        # columns: ts_code, trade_date, open, high, low, close, pre_close, change, pct_chg, vol, amount
        data = df.iloc[0]
        return f"{data['close']} (Date: {data['trade_date']})"
    except Exception as e:
        return f"Error fetching price: {e}"

@register_tool(description="Get fundamental data (PE, PB, Market Cap, Revenue, etc.) for a stock. Returns Dict.")
def get_fundamentals_data(stock_code: str):
    """
    Returns key financial indicators (daily basic) and income data.
    """
    pro = ensure_tushare_init()
    if not pro:
        return "Error: Tushare not initialized."

    try:
        # 1. Daily Basic (PE, PB, Market Cap)
        df_daily = pro.daily_basic(ts_code=stock_code, limit=1, fields='ts_code,trade_date,pe,pe_ttm,pb,total_mv')
        
        # 2. Income Statement (Revenue, Net Profit) - usually quarterly, taking latest
        df_income = pro.income(ts_code=stock_code, limit=1, fields='total_revenue,n_income_attr_p')
        
        result = {}
        
        if not df_daily.empty:
            d = df_daily.iloc[0]
            # Primary Keys
            result['pe_ratio'] = d['pe']
            result['pe_ratio_ttm'] = d['pe_ttm']
            result['pb_ratio'] = d['pb']
            result['market_cap'] = d['total_mv']
            
            # Aliases for robustness (Agent often guesses 'pe' or 'pb')
            result['pe'] = d['pe']
            result['pb'] = d['pb']
        
        if not df_income.empty:
            inc = df_income.iloc[0]
            result['revenue'] = inc['total_revenue']
            result['net_profit'] = inc['n_income_attr_p']
            
        if not result:
            return {}
            
        return result
    except Exception as e:
        return f"Error fetching fundamentals: {e}"

@register_tool(description="Get list of stocks in a specific industry. Example: '银行' or '医药'. Returns List[Dict]. Keys: 'code', 'name', 'industry'.")
def get_industry_stocks(industry_name: str):
    """
    Search for stocks belonging to a specific industry.
    Returns: List of dicts, e.g. [{'code': '000001.SZ', 'name': 'PingAn', 'industry': 'Bank'}]
    """
    pro = ensure_tushare_init()
    if not pro:
        return "Error: Tushare not initialized."
    
    try:
        # Fetch all stocks and filter by industry
        df = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,industry')
        
        matches = df[df['industry'].str.contains(industry_name, case=False, na=False)]
        
        if matches.empty:
            return []
            
        # Return top 20
        # Provide BOTH 'code' and 'stock_code' to be robust against Agent hallucinations
        records = []
        for _, row in matches.head(20).iterrows():
            records.append({
                "code": row['ts_code'],       # For agents using 'code'
                "stock_code": row['ts_code'], # For agents using 'stock_code'
                "name": row['name'],
                "industry": row['industry']
            })
        return records
    except Exception as e:
        return f"Error fetching industry stocks: {e}"

@register_tool(description="Get historical daily price data for a stock. Returns List[Dict].")
def get_history_data(stock_code: str, start_date: str, end_date: str):
    """
    Get daily Open/High/Low/Close/Vol data. 
    Dates should be 'YYYYMMDD'.
    """
    pro = ensure_tushare_init()
    if not pro:
        return "Error: Tushare not initialized."
    
    try:
        # Normalize date format (remove dashes if present)
        start_date = start_date.replace('-', '')
        end_date = end_date.replace('-', '')
        
        # Tushare daily: ts_code, trade_date, open, high, low, close, vol
        df = pro.daily(ts_code=stock_code, start_date=start_date, end_date=end_date)
        
        if df.empty:
            return []
            
        # Sort by date ascending
        df = df.sort_values('trade_date')
        
        records = df[['ts_code', 'trade_date', 'close', 'open', 'high', 'low', 'vol', 'pct_chg']].to_dict(orient='records')
        return records
    except Exception as e:
        return f"Error fetching history: {e}"

@register_tool(description="Plot stock price history and save to file. Returns the file path of the plot.")
def plot_price_history(stock_code: str, start_date: str, end_date: str):
    """
    Generates a line chart of the stock's close price and saves it as a .png file.
    """
    import matplotlib.pyplot as plt
    import pandas as pd
    
    # Reuse get_history_data logic or call it directly? 
    # Calling internal tools is cleaner but self.tools usage inside function is tricky without context.
    # Better to just use the Tushare API directly here for self-containment.
    pro = ensure_tushare_init()
    if not pro:
        return "Error: Tushare not initialized."
    
    try:
        df = pro.daily(ts_code=stock_code, start_date=start_date, end_date=end_date)
        if df.empty:
            return f"No data to plot for {stock_code}."
            
        df = df.sort_values('trade_date')
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        
        plt.figure(figsize=(10, 6))
        plt.plot(df['trade_date'], df['close'], label=f'{stock_code} Close')
        plt.title(f'{stock_code} Price History')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.grid(True)
        plt.legend()
        
        # Save to static dir or temp? 
        # For Gradio, saving to a local path is fine.
        filename = f"plot_{stock_code.replace('.','_')}_{start_date}_{end_date}.png"
        filepath = os.path.abspath(filename)
        plt.savefig(filepath)
        plt.close()
        
        return filepath
    except Exception as e:
        return f"Error plotting: {e}"
