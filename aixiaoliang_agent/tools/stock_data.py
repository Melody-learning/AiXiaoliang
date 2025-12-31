import os
import tushare as ts
import pandas as pd
import time
from dotenv import load_dotenv
from .registry import register_tool
from .data_utils import normalize_stock_records, create_envelope

load_dotenv()

_PRO = None
_IS_INIT = False

def ensure_tushare_init():
    # Always enforce Tushare Proxy (Ping-Pong Strategy with Gemini)
    ts_proxy = os.getenv("TUSHARE_PROXY", "http://tushare.xyz:5000")
    if ts_proxy and ts_proxy.lower() != "none":
         os.environ["HTTP_PROXY"] = ts_proxy
         
    global _PRO, _IS_INIT
    if _IS_INIT:
        return _PRO
    
    token = os.getenv("TUSHARE_TOKEN")
    if not token:
        print("[!] Error: TUSHARE_TOKEN is missing in environment.")
        return None

    try:
        # Init Pro API
        _PRO = ts.pro_api(token)
        _IS_INIT = True
        print("[*] Tushare Pro initialized successfully.")
        return _PRO
    except Exception as e:
        print(f"[!] Tushare initialization failed: {e}")
        return None

@register_tool(description="Search for a stock code by name. Example: '平安' -> '000001.SZ'. Returns Envelope.")
def search_stock(keyword: str):
    """
    Search for stock code (ts_code) by display name.
    """
    pro = ensure_tushare_init()
    if not pro:
        return create_envelope(None, status="error", error="Tushare not initialized")
    
    try:
        df = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,industry')
        matches = df[df['name'].str.contains(keyword, case=False, na=False) | 
                     df['ts_code'].str.contains(keyword, case=False, na=False)]
        
        if matches.empty:
            return create_envelope([], status="empty", meta={"hint": f"No stock found matching '{keyword}'. Try a different keyword."})
            
        records = []
        for _, row in matches.head(5).iterrows():
            records.append({
                "ts_code": row['ts_code'],
                "name": row['name'],
                "industry": row['industry']
            })
        data = normalize_stock_records(records)
        return create_envelope(data, status="success")
    except Exception as e:
        return create_envelope(None, status="error", error=f"Search failed: {e}")

@register_tool(description="Get the current price (or latest close) of a stock. Returns Envelope.")
def get_current_price(stock_code: str):
    """
    Returns the latest daily close price.
    """
    pro = ensure_tushare_init()
    if not pro:
        return create_envelope(None, status="error", error="Tushare not initialized")
    
    try:
        df = pro.daily(ts_code=stock_code, limit=1)
        if df.empty:
             return create_envelope(None, status="empty", meta={"hint": f"No price data for {stock_code}. Check if code is correct."})
        
        data = df.iloc[0]
        # Return a simple description for the agent to use
        payload = f"{data['close']} (Date: {data['trade_date']})"
        return create_envelope(payload, status="success")
    except Exception as e:
        return create_envelope(None, status="error", error=f"Fetch price failed: {e}")

@register_tool(description="Get fundamental data (PE, PB, Market Cap, Revenue, etc.). Returns Envelope.")
def get_fundamentals_data(stock_code: str):
    """
    Returns key financial indicators (daily basic) and income data.
    """
    pro = ensure_tushare_init()
    if not pro:
        return create_envelope(None, status="error", error="Tushare not initialized")

    try:
        df_daily = pro.daily_basic(ts_code=stock_code, limit=1, fields='ts_code,trade_date,pe,pe_ttm,pb,total_mv,dv_ratio,dv_ttm')
        df_income = pro.income(ts_code=stock_code, limit=1, fields='total_revenue,n_income_attr_p')
        
        result = {}
        if not df_daily.empty:
            d = df_daily.iloc[0]
            result['pe'] = d['pe']
            result['pe_ttm'] = d['pe_ttm']
            result['pb'] = d['pb']
            result['dv_ratio'] = d['dv_ratio']
            result['dv_ttm'] = d['dv_ttm']
            result['total_mv'] = d['total_mv']
        
        if not df_income.empty:
            inc = df_income.iloc[0]
            result['revenue'] = inc['total_revenue']
            result['net_profit'] = inc['n_income_attr_p']
            
        if not result:
            return create_envelope({}, status="empty", meta={"hint": "No fundamentals data found. Stock might be delisted or new."})
            
        return create_envelope(result, status="success")
    except Exception as e:
        return create_envelope(None, status="error", error=f"Fetch fundamentals failed: {e}")

@register_tool(description="Get list of stocks in a specific industry. Returns Envelope.")
def get_industry_stocks(industry_name: str):
    """
    Search for stocks belonging to a specific industry.
    """
    pro = ensure_tushare_init()
    if not pro:
        return create_envelope(None, status="error", error="Tushare not initialized")
    
    try:
        df = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,industry')
        matches = df[df['industry'].str.contains(industry_name, case=False, na=False)]
        
        if matches.empty:
            return create_envelope([], status="empty", meta={"hint": f"No stocks found for industry '{industry_name}'. Check industry name."})
            
        records = []
        for _, row in matches.head(20).iterrows():
            records.append({
                "ts_code": row['ts_code'],
                "name": row['name'],
                "industry": row['industry']
            })
        return create_envelope(normalize_stock_records(records), status="success")
    except Exception as e:
        return create_envelope(None, status="error", error=f"Fetch industry failed: {e}")

@register_tool(description="Get historical daily price data. Returns Envelope.")
def get_history_data(stock_code: str, start_date: str, end_date: str):
    """
    Get daily Open/High/Low/Close/Vol data. 
    Dates should be 'YYYYMMDD'.
    """
    pro = ensure_tushare_init()
    if not pro:
        return create_envelope(None, status="error", error="Tushare not initialized")
    
    try:
        start_date = start_date.replace('-', '')
        end_date = end_date.replace('-', '')
        
        df = pro.daily(ts_code=stock_code, start_date=start_date, end_date=end_date)
        
        if df.empty:
            return create_envelope([], status="empty", meta={"hint": f"No data between {start_date} and {end_date}."})
            
        df = df.sort_values('trade_date')
        records = df[['ts_code', 'trade_date', 'close', 'open', 'high', 'low', 'vol', 'pct_chg']].to_dict(orient='records')
        return create_envelope(normalize_stock_records(records), status="success")
    except Exception as e:
        return create_envelope(None, status="error", error=f"Fetch history failed: {e}")

@register_tool(description="Plot stock price history. Returns Envelope.")
def plot_price_history(stock_code: str, start_date: str, end_date: str):
    """
    Generates a line chart and returns file path.
    """
    import matplotlib.pyplot as plt
    pro = ensure_tushare_init()
    if not pro:
        return create_envelope(None, status="error", error="Tushare not initialized")
    
    try:
        df = pro.daily(ts_code=stock_code, start_date=start_date, end_date=end_date)
        if df.empty:
            return create_envelope(None, status="empty", meta={"hint": "No data to plot."})
            
        df = df.sort_values('trade_date')
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        
        plt.figure(figsize=(10, 6))
        plt.plot(df['trade_date'], df['close'], label=f'{stock_code} Close')
        plt.title(f'{stock_code} Price History')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.grid(True)
        plt.legend()
        
        filename = f"plot_{stock_code.replace('.','_')}_{start_date}_{end_date}.png"
        filepath = os.path.abspath(filename)
        plt.savefig(filepath)
        plt.close()
        
        return create_envelope(filepath, status="success")
    except Exception as e:
        return create_envelope(None, status="error", error=f"Plotting failed: {e}")

@register_tool(description="获取市场概念列表。src='ts'为Tushare概念，'ths'为同花顺概念。Returns Envelope.")
def get_concepts(src: str = 'ts'):
    """
    Get list of concepts/industries.
    """
    try:
        pro = ensure_tushare_init()
        if src == 'ts':
            df = pro.concept()
            records = df[['code', 'name', 'src']].to_dict(orient='records')
        elif src == 'ths':
            df = pro.ths_index()
            records = df[['ts_code', 'name', 'count', 'exchange', 'list_date', 'type']].to_dict(orient='records')
        else:
            return create_envelope(None, status="error", error="src must be 'ts' or 'ths'")
            
        return create_envelope(records, status="success")
    except Exception as e:
        return create_envelope(None, status="error", error=f"Fetch concepts failed: {e}")

@register_tool(description="获取特定概念下的股票列表。id为概念代码。Returns Envelope.")
def get_concept_stocks(id: str):
    """
    Get stocks belonging to a specific concept.
    """
    try:
        pro = ensure_tushare_init()
        try:
           df = pro.concept_detail(id=id)
        except:
           df = pro.ths_member(ts_code=id)
           
        if df.empty:
             return create_envelope([], status="empty", meta={"hint": f"No stocks found for concept {id}."})
             
        if 'ts_code' not in df.columns and 'code' in df.columns:
             df['ts_code'] = df['code']
             
        records = df[['ts_code', 'name']].head(100).to_dict(orient='records')
        return create_envelope(normalize_stock_records(records), status="success")
    except Exception as e:
        return create_envelope(None, status="error", error=f"Fetch concept stocks failed: {e}")

@register_tool(description="《Market Screener Tool》Get daily market snapshot for ALL stocks. date: YYYYMMDD. Returns Envelope.")
def get_market_daily(trade_date: str):
    """
    Get daily quotes for ALL stocks on a specific date. 
    """
    try:
        pro = ensure_tushare_init()
        df = pro.daily(trade_date=trade_date)
        
        if df.empty:
            return create_envelope([], status="empty", meta={"hint": "No market data found for this date. It might be a holiday or data is not yet available."})
        
        fields = ['ts_code', 'trade_date', 'close', 'open', 'high', 'low', 'pct_chg', 'vol', 'amount']
        df = df[fields]
        records = df.to_dict(orient='records')
        return create_envelope(normalize_stock_records(records), status="success")
    except Exception as e:
        return create_envelope(None, status="error", error=f"Fetch market daily failed: {e}")

@register_tool(description="《Market Screener Tool》Get daily basic indicators (PE, PB, Turnover, Dividend, Market Cap) for ALL stocks. date: YYYYMMDD. Returns Envelope.")
def get_daily_basic(trade_date: str):
    """
    Get fundamental indicators for ALL stocks on a specific date.
    Essential for screening stocks by PE, PB, Dividend Yield, Market Cap, Revenue (TTM), and Net Profit (TTM).
    Note: 'total_revenue_ttm' and 'net_profit_ttm' are derived from MV/PS and MV/PE ratios.
    """
    try:
        pro = ensure_tushare_init()
        # Fetch daily basic data
        # Fields: ts_code, trade_date, close, turnover_rate, volume_ratio, pe, pe_ttm, pb, ps, ps_ttm, dv_ratio, dv_ttm, total_share, float_share, free_share, total_mv, circ_mv
        fields = 'ts_code,trade_date,close,turnover_rate,volume_ratio,pe,pe_ttm,pb,ps,ps_ttm,dv_ratio,dv_ttm,total_share,float_share,free_share,total_mv,circ_mv'
        df = pro.daily_basic(trade_date=trade_date, fields=fields)
        
        if df.empty:
            return create_envelope([], status="empty", meta={"hint": "No basic data found for this date. Check if it is a trading day or holiday."})
        
        # Calculate derived fields (Revenue TTM, Net Profit TTM)
        # total_mv is in 10k (万元), convert to Yuan.
        df['total_revenue_ttm'] = df.apply(lambda row: (row['total_mv'] * 10000) / row['ps_ttm'] if row['ps_ttm'] else None, axis=1)
        df['net_profit_ttm'] = df.apply(lambda row: (row['total_mv'] * 10000) / row['pe_ttm'] if row['pe_ttm'] else None, axis=1)
        
        records = df.to_dict(orient='records')
        return create_envelope(normalize_stock_records(records), status="success")
    except Exception as e:
        return create_envelope(None, status="error", error=f"Fetch daily basic failed: {e}")

@register_tool(description="《Market Screener Tool》Get financial ratios (ROE, Margins) for ALL stocks. period: YYYYMMDD (Quarter End). Returns Envelope.")
def get_financial_indicator(period: str):
    """
    Get financial ratios (ROE, Gross Margin, Net Margin, etc.) for ALL stocks for a specific reporting period.
    Use Quarter End dates: e.g. '20241231', '20250331', '20250630'.
    Note: Iterates through all stocks in chunks, which may take ~10-20 seconds.
    """
    try:
        pro = ensure_tushare_init()
        # 1. Get all stock codes
        basics = pro.stock_basic(exchange='', list_status='L', fields='ts_code')
        if basics.empty:
            return create_envelope(None, status="error", error="Failed to fetch stock list.")
        
        all_codes = basics['ts_code'].tolist()
        
        # 2. Define fields
        fields = 'ts_code,end_date,roe,roe_dt,gross_margin,netprofit_margin,dt_eps'
        
        # 3. Chunk and fetch
        results = []
        chunk_size = 50 
        # Note: Depending on permission, 50-100 is safe.
        
        # Helper logging
        print(f"[*] Batch fetching financials for period {period} ({len(all_codes)} stocks)...")
        
        for i in range(0, len(all_codes), chunk_size):
            chunk = all_codes[i:i+chunk_size]
            codes_str = ",".join(chunk)

            try:
                # Tushare call
                df_chunk = pro.fina_indicator(ts_code=codes_str, period=period, fields=fields)
                if not df_chunk.empty:
                    results.extend(df_chunk.to_dict(orient='records'))
            except Exception as e:
                # Log but continue
                print(f"[!] Warn: Chunk {i} failed: {e}")
                
            time.sleep(0.5) # Rate limiting
                
        if not results:
            return create_envelope([], status="empty", meta={"hint": f"No financial data found for {period}. Ensure date is valid quarter end."})
            
        return create_envelope(normalize_stock_records(results), status="success")
    except Exception as e:
        return create_envelope(None, status="error", error=f"Fetch financial indicator failed: {e}")


@register_tool(description="Get financial indicators for a SPECIFIC stock over multiple periods (DuPont analysis). Returns Envelope.")
def get_stock_financials(stock_code: str, limit: int = 8):
    """
    Get ROE, Net Margin, Asset Turnover, and Equity Multiplier for a specific stock.
    Useful for DuPont analysis. limit: number of periods (quarters).
    """
    try:
        pro = ensure_tushare_init()
        fields = 'ts_code,end_date,roe,netprofit_margin,gross_margin,assets_turnover,equity_multiplier,debt_to_assets'
        df = pro.fina_indicator(ts_code=stock_code, limit=limit, fields=fields)
        
        if df.empty:
            return create_envelope([], status="empty", meta={"hint": f"No financial indicators found for {stock_code}."})
            
        records = df.to_dict(orient='records')
        return create_envelope(normalize_stock_records(records), status="success")
    except Exception as e:
        return create_envelope(None, status="error", error=f"Fetch stock financials failed: {e}")

@register_tool(description="Get historical valuation indicators (PE, PB, PS) for a specific stock. Returns Envelope.")
def get_valuation_history(stock_code: str, start_date: str, end_date: str):
    """
    Get historical PE, PB, PS, and Dividend Yield for a stock over a date range.
    Useful for calculating valuation percentiles.
    """
    try:
        pro = ensure_tushare_init()
        # Clean dates
        start_date = start_date.replace('-', '')
        end_date = end_date.replace('-', '')
        
        fields = 'ts_code,trade_date,pe,pe_ttm,pb,ps,ps_ttm,dv_ratio,dv_ttm'
        df = pro.daily_basic(ts_code=stock_code, start_date=start_date, end_date=end_date, fields=fields)
        
        if df.empty:
            return create_envelope([], status="empty", meta={"hint": f"No valuation history for {stock_code} in this range."})
            
        df = df.sort_values('trade_date')
        records = df.to_dict(orient='records')
        return create_envelope(normalize_stock_records(records), status="success")
    except Exception as e:
        return create_envelope(None, status="error", error=f"Fetch valuation history failed: {e}")
