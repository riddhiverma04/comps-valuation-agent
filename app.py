import streamlit as st
import os
import pandas as pd
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

# Sidebar inputs
st.sidebar.header("Configuration")
target_ticker = st.sidebar.text_input("Target Ticker", value="AAPL").upper()
run_button = st.sidebar.button("Run Valuation Pipeline")

init_db()

if run_button:
    with st.spinner(f"Running pipeline for {target_ticker} and peer group..."):
        tickers = discover_peers(target_ticker)
        st.sidebar.success(f"Discovered Peers: {', '.join(tickers)}")

        valuations = []
        for ticker in tickers:
            try:
                filing_path = fetch_latest_10k(ticker)
                if not filing_path or not os.path.exists(filing_path):
                    continue
                metrics, raw_snippet = parse_financials_from_filing(filing_path, ticker)
                audited_metrics = audit_financial_extraction(metrics, raw_snippet)
                valuation = calculate_valuation(audited_metrics)
                valuations.append(valuation)
                save_valuation_to_db(audited_metrics, valuation)
            except Exception as e:
                st.error(f"Error processing {ticker}: {e}")

        if valuations:
            st.session_state['valuations'] = valuations
            generate_comps_chart(valuations)
            st.success("Pipeline execution complete!")
        else:
            st.warning("No valuations generated.")

if 'valuations' in st.session_state:
    vals = st.session_state['valuations']
    
    # Convert valuation objects to DataFrame for clean display
    data = []
    for v in vals:
        cagr = 0.0
        if v.revenue_two_years_ago > 0 and v.revenue > 0:
            cagr = (v.revenue / v.revenue_two_years_ago) ** (1 / 2) - 1
            
        data.append({
            "Ticker": v.ticker,
            "Company": v.company_name,
            "Share Price ($)": v.share_price,
            "Market Cap ($M)": v.market_cap,
            "EV ($M)": v.enterprise_value,
            "Revenue ($M)": v.revenue,
            "Rev CAGR": f"{cagr:.1%}",
            "EBITDA ($M)": v.ebitda,
            "EV / Rev": f"{v.ev_to_revenue:.1f}x",
            "EV / EBITDA": f"{v.ev_to_ebitda:.1f}x",
            "P/E Ratio": f"{v.pe_ratio:.1f}x",
            "Debt / EBITDA": f"{v.debt_to_ebitda:.1f}"
        })
    
    df = pd.DataFrame(data)
    
    st.subheader("Peer Group Trading Comparables Table")
    st.dataframe(df, use_container_width=True)

    st.subheader("Valuation Multiples Chart (EV / EBITDA)")
    if os.path.exists("comps_chart.png"):
        st.image("comps_chart.png", use_column_width=True)
else:
    st.info("Enter a target ticker in the sidebar and click **Run Valuation Pipeline** to get started.")