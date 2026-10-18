import sqlite3
from datetime import datetime

DB_NAME = "comps_database.db"

def init_db():
    """Initializes the SQLite database for historical comps tracking."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS valuation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            ticker TEXT,
            company_name TEXT,
            fiscal_year INTEGER,
            revenue REAL,
            operating_income REAL,
            net_income REAL,
            enterprise_value REAL,
            ev_to_revenue REAL,
            ev_to_ebitda REAL,
            pe_ratio REAL
        )
    ''')
    conn.commit()
    conn.close()

def save_valuation_to_db(metrics, valuation):
    """Saves structured metrics and valuation output to SQL."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO valuation_history (
            timestamp, ticker, company_name, fiscal_year, revenue, 
            operating_income, net_income, enterprise_value, 
            ev_to_revenue, ev_to_ebitda, pe_ratio
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().isoformat(),
        metrics.ticker,
        metrics.company_name,
        metrics.fiscal_year,
        metrics.revenue,
        metrics.operating_income,
        metrics.net_income,
        valuation.enterprise_value,
        valuation.ev_to_revenue,
        valuation.ev_to_ebitda,
        valuation.pe_ratio
    ))
    conn.commit()
    conn.close()
    print(f"Saved historical record for {metrics.ticker} to SQL database.")