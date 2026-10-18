import streamlit as st
import os
import pandas as pd
import time
from src.database import init_db, save_valuation_to_db
from src.peer_discovery import discover_peers
from src.sec_fetcher import fetch_latest_10k
from src.parser_agent import parse_financials_from_filing
from src.auditor_agent import audit_financial_extraction
from src.valuation_engine import calculate_valuation
from src.chart_generator import generate_comps_chart

st.set_page_config(page_title="Comps & Valuation Platform", layout="wide")

st.title("📊 Institutional Automated Comps & Valuation Platform")
st.markdown("*Multi-Agent SEC Financial Parsing, Valuation Engine & Peer Comparison*")

# --- MOCK DATA FALLBACK CLASS ---
class MockValuation:
    def __init__(self, ticker, company_name, share_price, market_cap, enterprise_value, revenue, revenue_two_years_ago, ebitda, ev_to_revenue, ev_to_ebitda, pe_ratio, debt_to_ebitda):
        self.ticker = ticker
        self.company_name = company_name
        self.share_price = share_price
        self.market_cap = market_cap
        self.enterprise_value = enterprise_value
        self.revenue = revenue
        self.revenue_two_years_ago = revenue_two_years_ago
        self.ebitda = ebitda
        self.ev_to_revenue = ev_to_revenue
        self.ev_to_ebitda = ev_to_ebitda
        self.pe_ratio = pe_ratio
        self.debt_to_ebitda = debt_to_ebitda

# Sidebar configuration
st.sidebar.header("Configuration")
target_ticker = st.sidebar.text_input("Target Ticker", value="AAPL").upper()

# Offline Mock Mode Toggle (Defaults to True to bypass rate limits immediately)
use_mock_data = st.sidebar.checkbox("🚀 Use Offline Mock Mode (Bypass Groq API)", value=True)

available_peers = ["AAPL", "MSFT", "META", "NVDA", "AMZN", "TSLA"]
selected_peers = st.sidebar.multiselect(
    "Peer Group Selection",
    options=available_peers,
    default=["MSFT", "META", "NVDA"]
)

run_button = st.sidebar.button("Run Valuation Pipeline")

init_db()

if run_button:
    tickers = list(set([target_ticker] + selected_peers))
    
    if use_mock_data:
        with st.spinner("⚡ Loading Offline Mock Data (API bypassed)..."):
            time.sleep(1) # Simulated loading delay
            valuations = []
            for i, t in enumerate(tickers):
                valuations.append(MockValuation(
                    ticker=t,
                    company_name=f"{t} Corporation",
                    share_price=150.0 + (i * 25),
                    market_cap=2500000.0 + (i * 400000),
                    enterprise_value=2600000.0 + (i * 380000),
                    revenue=380000.0 + (i * 45000),
                    revenue_two_years_ago=310000.0 + (i * 35000),
                    ebitda=115000.0 + (i * 18000),
                    ev_to_revenue=6.8 + (i * 0.3),
                    ev_to_ebitda=21.5 + (i * 1.1),
                    pe_ratio=28.4 + (i * 1.4),
                    debt_to_ebitda=1.2
                ))
            st.session_state['valuations'] = valuations
            st.success("Mock valuation pipeline execution complete!")
    else:
        with st.spinner(f"Running live pipeline for target {target_ticker} and peer group..."):
            st.sidebar.success(f"Processing Tickers: {', '.join(tickers)}")

            valuations = []
            progress_bar = st.progress(0)
            
            for i, ticker in enumerate(tickers):
                try:
                    time.sleep(2) # Respect Groq rate limits
                    
                    filing_path = fetch_latest_10k(ticker)
                    if not filing_path or not os.path.exists(filing_path):
                        st.warning(f"Skipping {ticker}: 10-K filing path not found.")
                        continue
                        
                    metrics, raw_snippet = parse_financials_from_filing(filing_path, ticker)
                    audited_metrics = audit_financial_extraction(metrics, raw_snippet)
                    valuation = calculate_valuation(audited_metrics)
                    valuations.append(valuation)
                    save_valuation_to_db(audited_metrics, valuation)
                    
                except Exception as e:
                    error_msg = str(e)
                    if "429" in error_msg or "rate_limit" in error_msg.lower() or "tokens" in error_msg.lower():
                        st.error(f"⚠️ Groq token rate limit reached for {ticker}. Reduce peer group size or switch on Mock Mode.")
                    else:
                        st.error(f"Error processing {ticker}: {e}")
                    continue
                    
                progress_bar.progress((i + 1) / len(tickers))

            if valuations:
                st.session_state['valuations'] = valuations
                generate_comps_chart(valuations)
                st.success("Live pipeline execution complete!")
            else:
                st.warning("No valuations generated due to errors or rate limits.")

if 'valuations' in st.session_state:
    vals = st.session_state['valuations']
    
    data = []
    for v in vals:
        cagr = 0.0
        rev_2y = getattr(v, 'revenue_two_years_ago', 0)
        rev = getattr(v, 'revenue', 0)
        if rev_2y > 0 and rev > 0:
            cagr = (rev / rev_2y) ** (1 / 2) - 1
            
        data.append({
            "Ticker": getattr(v, 'ticker', 'N/A'),
            "Company": getattr(v, 'company_name', 'N/A'),
            "Share Price ($)": getattr(v, 'share_price', 0.0),
            "Market Cap ($M)": getattr(v, 'market_cap', 0.0),
            "EV ($M)": getattr(v, 'enterprise_value', 0.0),
            "Revenue ($M)": rev,
            "Rev CAGR": f"{cagr:.1%}",
            "EBITDA ($M)": getattr(v, 'ebitda', 0.0),
            "EV / Rev": f"{getattr(v, 'ev_to_revenue', 0.0):.1f}x",
            "EV / EBITDA": f"{getattr(v, 'ev_to_ebitda', 0.0):.1f}x",
            "P/E Ratio": f"{getattr(v, 'pe_ratio', 0.0):.1f}x",
            "Debt / EBITDA": f"{getattr(v, 'debt_to_ebitda', 0.0):.1f}"
        })
    
    df = pd.DataFrame(data)
    
    st.subheader("Peer Group Trading Comparables Table")
    st.dataframe(df, use_container_width=True)

    st.subheader("Valuation Multiples Chart (EV / EBITDA)")
    if os.path.exists("comps_chart.png"):
        st.image("comps_chart.png", width="stretch")
else:
    st.info("Configure your target ticker and peer group in the sidebar, then click **Run Valuation Pipeline** to get started.")