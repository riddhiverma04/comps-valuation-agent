import sqlite3
from src.database import DB_NAME

def get_valuation_history(ticker_filter: str = None):
    """Queries the SQLite database for historical valuation runs."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    if ticker_filter:
        cursor.execute('''
            SELECT timestamp, ticker, company_name, fiscal_year, revenue, 
                   enterprise_value, ev_to_revenue, ev_to_ebitda, pe_ratio
            FROM valuation_history
            WHERE ticker = ?
            ORDER BY timestamp DESC
        ''', (ticker_filter.upper(),))
    else:
        cursor.execute('''
            SELECT timestamp, ticker, company_name, fiscal_year, revenue, 
                   enterprise_value, ev_to_revenue, ev_to_ebitda, pe_ratio
            FROM valuation_history
            ORDER BY timestamp DESC
        ''')
        
    records = cursor.fetchall()
    conn.close()
    return records

def print_history_report(ticker_filter: str = None):
    """Prints a clean formatted table of historical valuations from SQLite."""
    records = get_valuation_history(ticker_filter)
    
    if not records:
        print(f"No historical valuation records found{f' for {ticker_filter}' if ticker_filter else ''}.")
        return

    print("=" * 105)
    print(f"{'Timestamp':<20} | {'Ticker':<6} | {'FY':<6} | {'Revenue ($M)':<12} | {'EV ($M)':<12} | {'EV/Rev':<8} | {'EV/EBITDA':<10} | {'P/E':<6}")
    print("-" * 105)
    
    for row in records:
        ts, ticker, name, fy, rev, ev, ev_rev, ev_ebitda, pe = row
        # Trim timestamp for clean display
        short_ts = ts[:19] if ts else "N/A"
        print(f"{short_ts:<20} | {ticker:<6} | {fy:<6} | ${rev:<11,.1f} | ${ev:<11,.1f} | {ev_rev:<8.1f} | {ev_ebitda:<10.1f} | {pe:<6.1f}")
    
    print("=" * 105)

if __name__ == "__main__":
    import sys
    ticker_arg = sys.argv[1] if len(sys.argv) > 1 else None
    print_history_report(ticker_arg)