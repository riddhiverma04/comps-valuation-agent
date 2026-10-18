import streamlit as os_st # using st consistently
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

# Sidebar inputs - defaulted to a single ticker/peer to conserve daily tokens
st.sidebar.header("Configuration")
target_ticker = st.sidebar.text_input("Target Ticker", value="AAPL").upper()

# Optional peer selection override
available_peers = ["AAPL", "MSFT", "META", "NVDA", "AMZN", "TSLA"]
selected_peers = st.sidebar.multiselect(
    "Peer Group Selection",
    options=available_peers,
    default=["MSFT"]  # Conserves daily token limit by defaulting to 1 peer
)

run_button = st.sidebar.button("Run Valuation Pipeline")

init_db()

if run_button:
    with st.spinner(f"Running pipeline for target {target_ticker} and peer group..."):
        # Combine target and selected peers for structured processing
        tickers = list(set([target_ticker] + selected_peers))
        st.sidebar.success(f"Processing Tickers: {', '.join(tickers)}")

        valuations = []
        progress_bar = st.progress(0)
        
        for i, ticker in enumerate(tickers):
            try:
                # Enforce pause between LLM calls to respect Groq rate limits
                time.sleep(2)
                
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
                    st.error(f"⚠️ Groq token rate limit reached for {ticker}. Reduce peer group size or wait for daily reset.")
                else:
                    st.error(f"Error processing {ticker}: {e}")
                continue
                
            progress_bar.progress((i + 1) / len(tickers))

        if valuations:
            st.session_state['valuations'] = valuations
            generate_comps_chart(valuations)
            st.success("Pipeline execution complete!")
        else:
            st.warning("No valuations generated due to errors or rate limits.")

if 'valuations' in st.session_state:
    vals = st.session_state['valuations']
    
    # Convert valuation objects to DataFrame for clean display
    data = []
    for v in vals:
        cagr = 0.0
        if getattr(v, 'revenue_two_years_ago', 0) > 0 and getattr(v, 'revenue', 0) > 0:
            cagr = (v.revenue / v.revenue_two_years_ago) ** (1 / 2) - 1
            
        data.append({
            "Ticker": getattr(v, 'ticker', 'N/A'),
            "Company": getattr(v, 'company_name', 'N/A'),
            "Share Price ($)": getattr(v, 'share_price', 0.0),
            "Market Cap ($M)": getattr(v, 'market_cap', 0.0),
            "EV ($M)": getattr(v, 'enterprise_value', 0.0),
            "Revenue ($M)": getattr(v, 'revenue', 0.0),
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