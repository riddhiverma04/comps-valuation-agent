import streamlit as st
import os
import pandas as pd
import io
import time
import matplotlib.pyplot as plt
import numpy as np
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

# --- FOOTBALL FIELD CHART GENERATOR ---
def generate_football_field_chart(target_ticker, current_price, dcf_implied_val):
    fig, ax = plt.subplots(figsize=(10, 4))
    
    methods = ["52-Week Range", "Trading Comps", "DCF Valuation"]
    # Derive implied valuation ranges based on current price and DCF output
    lows = [current_price * 0.75, current_price * 0.85, dcf_implied_val * 0.85]
    highs = [current_price * 1.25, current_price * 1.35, dcf_implied_val * 1.15]
    
    y_pos = np.arange(len(methods))
    
    for i, (low, high) in enumerate(zip(lows, highs)):
        ax.barh(y_pos[i], high - low, left=low, height=0.4, color='#1f77b4', alpha=0.8, edgecolor='black')
        ax.text((low + high) / 2, y_pos[i], f"${low:.1f} - ${high:.1f}", ha='center', va='center', color='white', fontweight='bold', fontsize=9)
        
    ax.set_yticks(y_pos)
    ax.set_yticklabels(methods, fontweight='bold')
    ax.set_xlabel("Implied Share Price ($)")
    ax.set_title(f"Valuation Summary ('Football Field') - {target_ticker}", fontsize=12, fontweight='bold')
    
    ax.axvline(x=current_price, color='red', linestyle='--', linewidth=1.5, label=f'Current Price (${current_price:.2f})')
    ax.legend(loc='upper right')
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    
    plt.savefig("football_field_chart.png", dpi=300)
    plt.close()

# --- DYNAMIC SIDEBAR CONFIGURATION ---
st.sidebar.header("Configuration")
target_ticker = st.sidebar.text_input("Target Ticker", value="AAPL").upper()

PEER_MAP = {
    "AAPL": ["MSFT", "NVDA", "AMZN", "GOOGL", "META"],
    "MSFT": ["AAPL", "GOOGL", "AMZN", "ORCL", "IBM"],
    "NVDA": ["AMD", "INTC", "TSM", "AVGO", "QCOM"],
    "AMZN": ["WMT", "TGT", "EBAY", "BABA", "MSFT"],
    "TSLA": ["RIVN", "LCID", "F", "GM", "NIO"]
}

suggested_peers = PEER_MAP.get(target_ticker, ["MSFT", "META", "NVDA", "AMZN"])

use_mock_data = st.sidebar.checkbox("🚀 Use Offline Mock Mode (Bypass Groq API)", value=True)

selected_peers = st.sidebar.multiselect(
    "Peer Group Selection",
    options=list(set(suggested_peers + ["AAPL", "MSFT", "META", "NVDA", "AMZN", "TSLA", "GOOGL", "AMD"])),
    default=suggested_peers[:3]
)

# --- DCF ASSUMPTIONS SIDEBAR ---
st.sidebar.markdown("---")
st.sidebar.header("DCF Valuation Assumptions")
wacc = st.sidebar.slider("WACC (Discount Rate)", min_value=0.05, max_value=0.15, value=0.09, step=0.005)
terminal_growth = st.sidebar.slider("Terminal Growth Rate", min_value=0.01, max_value=0.04, value=0.025, step=0.005)
projection_years = st.sidebar.selectbox("Projection Period (Years)", options=[5, 10], index=0)

run_button = st.sidebar.button("Run Valuation Pipeline")

init_db()

if run_button:
    tickers = list(set([target_ticker] + selected_peers))
    
    if use_mock_data:
        with st.spinner("⚡ Loading Offline Mock Data (API bypassed)..."):
            time.sleep(1)
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
            generate_comps_chart(valuations)
            st.success("Mock valuation pipeline execution complete!")
    else:
        with st.spinner(f"Running live pipeline for target {target_ticker} and peer group..."):
            st.sidebar.success(f"Processing Tickers: {', '.join(tickers)}")

            valuations = []
            progress_bar = st.progress(0)
            
            for i, ticker in enumerate(tickers):
                try:
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

    # --- EXCEL DOWNLOAD FUNCTIONALITY ---
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Trading Comps')
    buffer.seek(0)

    st.download_button(
        label="📥 Export Trading Comps to Excel",
        data=buffer,
        file_name=f"{target_ticker}_Trading_Comps.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.subheader("Valuation Multiples Chart (EV / EBITDA)")
    if os.path.exists("comps_chart.png"):
        st.image("comps_chart.png", width="stretch")

    # --- INTRINSIC DCF VALUATION MODEL ---
    st.markdown("---")
    st.subheader(f"Intrinsic DCF Valuation Model ({target_ticker})")
    
    target_data = next((v for v in vals if getattr(v, 'ticker', '') == target_ticker), None)
    
    if target_data:
        base_ebitda = getattr(target_data, 'ebitda', 115000.0)
        base_fcf = base_ebitda * 0.60
        fcf_growth_rate = 0.08
        
        projected_fcfs = []
        current_fcf = base_fcf
        for year in range(1, projection_years + 1):
            current_fcf *= (1 + fcf_growth_rate)
            discounted_fcf = current_fcf / ((1 + wacc) ** year)
            projected_fcfs.append(discounted_fcf)
            
        sum_pv_fcf = sum(projected_fcfs)
        
        final_year_fcf = projected_fcfs[-1]
        terminal_value = (final_year_fcf * (1 + terminal_growth)) / (wacc - terminal_growth)
        pv_terminal_value = terminal_value / ((1 + wacc) ** projection_years)
        
        implied_ev = sum_pv_fcf + pv_terminal_value
        current_share_price = getattr(target_data, 'share_price', 150.0)
        
        # Approximate implied share price from DCF Enterprise Value
        dcf_implied_share_price = current_share_price * (implied_ev / 2600000.0) if implied_ev > 0 else current_share_price
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Cumulative PV of FCF ($M)", f"${sum_pv_fcf:,.1f}")
        col2.metric("PV of Terminal Value ($M)", f"${pv_terminal_value:,.1f}")
        col3.metric("Implied Enterprise Value ($M)", f"${implied_ev:,.1f}")
        col4.metric("Current Share Price ($)", f"${current_share_price:.2f}")

        # --- GENERATE & RENDER FOOTBALL FIELD CHART ---
        generate_football_field_chart(target_ticker, current_share_price, dcf_implied_share_price)
        
        st.markdown("---")
        st.subheader("Valuation Summary ('Football Field' Chart)")
        if os.path.exists("football_field_chart.png"):
            st.image("football_field_chart.png", width="stretch")
    else:
        st.info("Select a valid target ticker in the sidebar to run the DCF model.")
else:
    st.info("Configure your target ticker and peer group in the sidebar, then click **Run Valuation Pipeline** to get started.")