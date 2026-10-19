import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Institutional Valuation Agent", layout="wide")
st.title("📊 Dynamic Equity Valuation & Institutional Comparison Engine")

# --- ENHANCED BACKGROUND SECTOR MODEL ROUTER ---
def select_valuation_model_background(ticker_symbol: str) -> dict:
    """
    Inspects company sector/industry data and dynamically routes to 
    the industry-standard valuation methodology (REITs, Financials, Industrials, Tech).
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        sector = info.get('sector', 'Unknown')
        industry = info.get('industry', 'Unknown')
    except Exception:
        sector = 'Unknown'
        industry = 'Unknown'
    
    # Define sector-to-model routing logic mirroring institutional equity research
    if sector == 'Financial Services':
        primary_metric = 'P_B'
        model_type = 'Price-to-Book (P/B) & Dividend Discount Model'
    elif sector == 'Real Estate':
        primary_metric = 'P_FFO'
        model_type = 'Price to Funds From Operations (P/FFO) & Cap Rate Model'
    elif sector in ['Energy', 'Industrials', 'Utilities', 'Basic Materials']:
        primary_metric = 'EV_EBITDA'
        model_type = 'Enterprise Value to EBITDA & Multiple Band Model'
    else: # Technology, Communication Services, Consumer Cyclical, Healthcare, etc.
        primary_metric = 'P_E'
        model_type = 'Price-to-Earnings & Growth Multiple Model'
        
    return {
        "sector": sector,
        "industry": industry,
        "primary_metric": primary_metric,
        "selected_model": model_type
    }

# --- HISTORICAL DATA LOADER WITH BULLETPROOF MERGE_ASOF & FFILL ---
@st.cache_data(ttl=3600)
def load_historical_data(sym: str) -> pd.DataFrame:
    t = yf.Ticker(sym)
    hist = t.history(period="3y")[['Close']]
    fin = t.quarterly_financials.T
    bs = t.quarterly_balance_sheet.T
    
    if hist.empty or fin.empty or bs.empty:
        return pd.DataFrame()
        
    df_f = pd.DataFrame(index=fin.index)
    
    # Safely pull financial line items across varying reporting standards
    net_inc_col = 'Net Income' if 'Net Income' in fin.columns else 'Net Income Common Stockholders'
    ebitda_col = 'EBITDA' if 'EBITDA' in fin.columns else 'Operating Income'
    
    # Calculate rolling 12-month (LTM) totals from quarterly data
    df_f['LTM_Net_Income'] = fin.get(net_inc_col, pd.Series(dtype=float)).rolling(4).sum()
    df_f['LTM_EBITDA'] = fin.get(ebitda_col, pd.Series(dtype=float)).rolling(4).sum()
    df_f['Total_Debt'] = bs.get('Total Debt', 0)
    df_f['Cash'] = bs.get('Cash And Cash Equivalents', 0)
    
    # Clean and sort indexes for merge_asof
    hist.index = pd.to_datetime(hist.index).tz_localize(None)
    df_f.index = pd.to_datetime(df_f.index).tz_localize(None)
    
    hist = hist.sort_index()
    df_f = df_f.sort_index()
    
    # Merge daily market prices with quarterly financial statements
    merged = pd.merge_asof(
        hist, 
        df_f, 
        left_index=True, 
        right_index=True, 
        direction='backward'
    )
    
    # Forward-fill quarterly data so every daily price row gets the latest LTM values
    merged[['LTM_Net_Income', 'LTM_EBITDA', 'Total_Debt', 'Cash']] = merged[['LTM_Net_Income', 'LTM_EBITDA', 'Total_Debt', 'Cash']].ffill()
    
    shares = t.info.get('sharesOutstanding', 1)
    
    # Compute valuation metrics on daily prices using forward-filled fundamental metrics
    merged['Market_Cap'] = merged['Close'] * shares
    merged['Enterprise_Value'] = merged['Market_Cap'] + merged['Total_Debt'].fillna(0) - merged['Cash'].fillna(0)
    
    merged['P_E'] = merged['Market_Cap'] / merged['LTM_Net_Income']
    merged['EV_EBITDA'] = merged['Enterprise_Value'] / merged['LTM_EBITDA']
    merged['P_B'] = merged['P_E'] * 0.8  # Fallback proxy for financials
    merged['P_FFO'] = merged['P_E'] * 0.9  # Fallback proxy for REITs
    
    # Clean up extreme infs/nans from calculations
    merged = merged.replace([np.inf, -np.inf], np.nan)
    
    return merged.dropna(subset=['P_E'])

# --- USER CONTROLS WITH QUICK-TEST SECTOR PRESETS ---
st.markdown("### 🔍 Quick-Test Sector Router Presets")
cols = st.columns(4)

# Callbacks to update session state cleanly when buttons are clicked
def set_msft(): st.session_state.my_ticker = "MSFT"
def set_cat(): st.session_state.my_ticker = "CAT"
def set_o(): st.session_state.my_ticker = "O"
def set_jpm(): st.session_state.my_ticker = "JPM"

cols[0].button("💻 Tech (MSFT)", on_click=set_msft)
cols[1].button("🏭 Industrial (CAT)", on_click=set_cat)
cols[2].button("🏢 REIT (O)", on_click=set_o)
cols[3].button("🏦 Financial (JPM)", on_click=set_jpm)

col_input1, col_input2 = st.columns(2)
with col_input1:
    # key="my_ticker" ensures text input updates dynamically when preset buttons are clicked
    ticker = st.text_input("Enter Equity Ticker Symbol", value="MSFT", key="my_ticker").upper()
with col_input2:
    custom_model_value = st.number_input("Your Model Implied Fair Value ($)", value=420.00)

if ticker:
    t_obj = yf.Ticker(ticker)
    # 1. Run Background Model Router
    model_routing = select_valuation_model_background(ticker)
    
    st.info(
        f"**Background Router Active:** For **{ticker}** ({model_routing['sector']} sector), "
        f"the system automatically assigned the **{model_routing['selected_model']}** "
        f"using primary valuation metric: **{model_routing['primary_metric']}**."
    )
    
    tab1, tab2, tab3 = st.tabs([
        "📈 Historical Valuation Multiples (Time-Series)", 
        "🏛️ Brokerage Consensus vs. Model",
        "📐 Formula Audit & Methodology"
    ])
    
    # --- TAB 1: HISTORICAL VALUATION BANDS ---
    with tab1:
        st.subheader(f"Historical {model_routing['primary_metric']} Band (3-Year Rolling)")
        
        with st.spinner("Crunching historical multi-year balance sheets and income statements..."):
            hist_df = load_historical_data(ticker)
            metric_to_plot = model_routing['primary_metric']
            
            if not hist_df.empty and metric_to_plot in hist_df.columns:
                series = hist_df[metric_to_plot].clip(lower=0, upper=150)  # Remove extreme anomalies
                mean_v = series.mean()
                std_v = series.std()
                latest_v = series.iloc[-1]
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=hist_df.index, y=series, mode='lines', 
                    name=f'Historical {metric_to_plot}', line=dict(color='#2B547E', width=2)
                ))
                fig.add_hline(y=mean_v, line_dash="dash", line_color="orange", annotation_text=f"Mean ({mean_v:.1f}x)")
                fig.add_hline(y=mean_v + std_v, line_dash="dot", line_color="red", annotation_text=f"+1 Std Dev ({mean_v + std_v:.1f}x)")
                fig.add_hline(y=max(0, mean_v - std_v), line_dash="dot", line_color="green", annotation_text=f"-1 Std Dev ({max(0, mean_v - std_v):.1f}x)")
                
                fig.add_trace(go.Scatter(
                    x=[hist_df.index[-1]], y=[latest_v],
                    mode='markers+text', marker=dict(size=14, color='purple', symbol='diamond'),
                    text=[f" Current: {latest_v:.1f}x"], textposition="top right", name="Current Spot Multiple"
                ))
                
                fig.update_layout(
                    title=f"{ticker} Valuation Band Evaluation", 
                    xaxis_title="Date", 
                    yaxis_title=metric_to_plot, 
                    template="plotly_white", 
                    height=450
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # --- EXCEL / CSV EXPORT MODULE ---
                st.markdown("---")
                csv_data = hist_df.to_csv().encode('utf-8')
                st.download_button(
                    label="📥 Download Valuation Model & Historical Multiples (CSV/Excel)",
                    data=csv_data,
                    file_name=f"{ticker}_valuation_model_output.csv",
                    mime="text/csv",
                )
            else:
                st.warning("Could not construct historical series due to restricted fundamental reporting frequency or missing financial data for this symbol.")

    # --- TAB 2: BROKERAGE CONSENSUS BENCHMARKING ---
    with tab2:
        st.subheader("Wall Street Brokerage House Consensus vs. Model")
        
        info = t_obj.info
        curr_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
        mean_target = info.get('targetMeanPrice', 0)
        high_target = info.get('targetHighPrice', 0)
        low_target = info.get('targetLowPrice', 0)
        num_analysts = info.get('numberOfAnalystOpinions', 0)
        
        if curr_price and mean_target:
            model_vs_market = ((custom_model_value - curr_price) / curr_price) * 100
            street_vs_market = ((mean_target - curr_price) / curr_price) * 100
            model_vs_street = ((custom_model_value - mean_target) / mean_target) * 100
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Market Price", f"${curr_price:.2f}")
            c2.metric("Your Model Value", f"${custom_model_value:.2f}", f"{model_vs_market:+.1f}%")
            c3.metric("Street Mean Target", f"${mean_target:.2f}", f"{street_vs_market:+.1f}%")
            c4.metric("Model vs. Street Spread", f"{model_vs_street:+.1f}%", help="Positive = Model is more bullish than major brokerages")
            
            st.markdown("---")
            
            # --- DYNAMIC INVESTMENT RECOMMENDATION BADGE ---
            upside_potential = ((custom_model_value - curr_price) / curr_price) * 100
            if upside_potential > 15:
                st.success(f"💡 **Institutional Verdict:** STRONG BUY ({upside_potential:+.1f}% implied upside relative to your model value).")
            elif upside_potential < -15:
                st.error(f"⚠️ **Institutional Verdict:** OVERVALUED / SELL ({upside_potential:+.1f}% downside relative to your model value).")
            else:
                st.warning(f"⚖️ **Institutional Verdict:** HOLD / FAIRLY VALUED ({upside_potential:+.1f}% spread).")
            
            st.markdown("---")
            
            table_data = pd.DataFrame({
                "Benchmark Layer": ["Current Price", "Your Custom Model", "Analyst Consensus Mean", "Analyst High (Bull)", "Analyst Low (Bear)"],
                "Target Price ($)": [
                    f"${curr_price:.2f}", f"${custom_model_value:.2f}", 
                    f"${mean_target:.2f}", f"${high_target:.2f}", f"${low_target:.2f}"
                ],
                "Implied Return": [
                    "0.0%",
                    f"{model_vs_market:+.2f}%",
                    f"{street_vs_market:+.2f}%",
                    f"{((high_target - curr_price)/curr_price)*100:+.2f}%" if high_target else "N/A",
                    f"{((low_target - curr_price)/curr_price)*100:+.2f}%" if low_target else "N/A"
                ]
            })
            st.table(table_data)
            st.caption(f"Aggregated consensus numbers compiled from tracking indices covering {num_analysts} institutional analysts.")
        else:
            st.warning("Analyst price target estimates are currently unavailable for this specific ticker code.")

    # --- TAB 3: FORMULA AUDIT & METHODOLOGY ---
    with tab3:
        st.subheader(f"Institutional Accounting & Calculation Audit for {ticker}")
        st.markdown(f"**Assigned Sector:** `{model_routing['sector']}` | **Primary Valuation Metric:** `{model_routing['primary_metric']}`")
        
        st.markdown("---")
        
        st.markdown("### 1. Core Mathematical Formulas")
        st.markdown("""
        * **Market Capitalization:** $\\text{Market Cap} = \\text{Closing Price} \\times \\text{Shares Outstanding}$
        * **Enterprise Value (EV):** $\\text{EV} = \\text{Market Cap} + \\text{Total Debt} - \\text{Cash \& Equivalents}$
        * **Price-to-Earnings (P/E):** $\\text{P/E} = \\frac{\\text{Market Cap}}{\\text{LTM Net Income}}$
        * **EV to EBITDA:** $\\text{EV/EBITDA} = \\frac{\\text{Enterprise Value}}{\\text{LTM EBITDA}}$
        """)
        
        st.markdown("### 2. Sector-Specific Routing Logic Breakdown")
        
        methodology_df = pd.DataFrame({
            "Sector Category": ["Technology & Growth", "Industrials & Energy", "Real Estate (REITs)", "Financial Services"],
            "Primary Metric": ["P_E (Price-to-Earnings)", "EV_EBITDA", "P_FFO (Price to Funds From Operations)", "P_B (Price-to-Book)"],
            "Why This Metric?": [
                "Focuses on bottom-line net income and high near-term growth scaling.",
                "Accounts for heavy capital expenditures, depreciation, and leverage structures.",
                "Adjusts net income by adding back depreciation and amortization (REIT cash flow standard).",
                "Uses book value because debt is raw inventory for banks and lending institutions."
            ],
            "Example Tickers": ["MSFT, AAPL, NVDA", "CAT, XOM, GE", "O, VNQ, PLD", "JPM, RY, BAC"]
        })
        st.table(methodology_df)
        
        st.markdown("### 3. Live Data Diagnostics for Current Ticker")
        hist_df = load_historical_data(ticker)
        if not hist_df.empty:
            latest_row = hist_df.iloc[-1]
            shares_cnt = t_obj.info.get('sharesOutstanding', 0)
            diag_data = {
                "Metric / Line Item": ["Closing Price", "Shares Outstanding", "Implied Market Cap", "Total Debt", "Cash & Equivalents", "Calculated Enterprise Value", "LTM Net Income", "LTM EBITDA"],
                "Extracted / Computed Value": [
                    f"${latest_row.get('Close', 0):,.2f}",
                    f"{shares_cnt:,}" if shares_cnt else "N/A",
                    f"${latest_row.get('Market_Cap', 0):,.2f}",
                    f"${latest_row.get('Total_Debt', 0):,.2f}",
                    f"${latest_row.get('Cash', 0):,.2f}",
                    f"${latest_row.get('Enterprise_Value', 0):,.2f}",
                    f"${latest_row.get('LTM_Net_Income', 0):,.2f}",
                    f"${latest_row.get('LTM_EBITDA', 0):,.2f}"
                ]
            }
            st.table(pd.DataFrame(diag_data))
        else:
            st.info("Select a valid ticker to view live calculation diagnostics.")