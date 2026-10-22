<div align="center">

# 📊 Institutional Equity Valuation & Comparison Engine

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-red.svg)](https://streamlit.io/)
[![Pandas](https://img.shields.io/badge/Pandas-Data%20Pipeline-orange.svg)](https://pandas.pydata.org/)
[![Plotly](https://img.shields.io/badge/Plotly-Interactive%20Charts-green.svg)](https://plotly.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

*An automated institutional equity research platform that bridges daily market pricing with quarterly fundamental filings to perform dynamic valuation modeling, peer comparison, and risk sensitivity analysis.*

</div>

---

## 🧭 Overview

In institutional equity research, comparing daily market volatility against discrete quarterly fundamental reporting (10-Q/10-K) introduces lookahead bias and data alignment challenges. 

The **Institutional Valuation & Comparison Engine** solves this by programmatically routing target companies to sector-specific valuation methodologies, executing timezone-safe as-of data merges, and generating Wall Street-grade comparable company analysis (Comps) alongside rolling multiple bands.

---

## ✨ Key Features

* **🧠 Dynamic Background Sector Model Router:** Automatically inspects company sector and industry metadata to assign the industry-standard valuation model:
  * *Technology & Growth* $\rightarrow$ Price-to-Earnings (P/E)
  * *Industrials, Energy & Utilities* $\rightarrow$ Enterprise Value to EBITDA (EV/EBITDA)
  * *Real Estate (REITs)* $\rightarrow$ Price to Funds From Operations (P/FFO)
  * *Financial Services* $\rightarrow$ Price-to-Book (P/B)
* **🛡️ Bulletproof As-Of Data Merging (`pd.merge_asof`):** Synchronizes high-frequency daily closing prices with quarterly financial statements using timezone normalization and forward-filling to prevent data leakage and lookahead bias.
* **📈 3-Year Rolling Valuation Bands:** Visualizes historical multiple expansion and contraction with mean, $+1$, and $-1$ standard deviation threshold lines using interactive Plotly charts.
* **🏛️ Comparable Company Analysis (Comps):** Automatically fetches peer group data, filters out unprofitable outlier multiples, and calculates median/mean benchmark statistics.
* **🎯 Sensitivity & Scenario Modeling:** Evaluates base, bear ($-15\%$), and bull ($+15\%$) valuation scenarios to benchmark model fair value against Wall Street analyst consensus price targets.
* **📥 Export & Audit Module:** Includes raw data CSV exports and an accounting audit trail verifying financial data lineage.

---

## 🛠️ Tech Stack

| Layer | Technology / Library | Purpose |
| :--- | :--- | :--- |
| **Frontend / UI** | `Streamlit` | Interactive web application dashboard & state management |
| **Data Engine** | `Pandas`, `NumPy` | As-of merging, LTM calculations, and multiple vectorization |
| **Data Provider** | `yfinance` | Real-time quote streaming and historical fundamental extraction |
| **Visualization** | `Plotly` | Interactive multi-year valuation band charting |

---

## 🚀 Installation & Local Setup

1. Clone the Repository
```bash
git clone [https://github.com/YOUR-USERNAME/comps-valuation-agent.git](https://github.com/YOUR-USERNAME/comps-valuation-agent.git)
cd comps-valuation-agent

2. Create and Activate a Virtual Environment
Bash
python -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows (Command Prompt):
# venv\Scripts\activate

3. Install Dependencies
Bash
pip install streamlit pandas numpy yfinance plotly

4. Launch the Application
Bash
python -m streamlit run app.py
Access the local web app in your browser at http://localhost:8501.


📊 Usage Guide
Select a Ticker: Use the quick-test sector preset buttons (MSFT, CAT, O, JPM) or enter any valid equity ticker symbol.
Input Fair Value: Enter your custom model-implied target price in the sidebar/input control.
Analyze Across Tabs:
Tab 1: Review historical valuation multiple bands and download model CSV data.
Tab 2: Compare your model target against brokerage consensus and bear/bull scenarios.
Tab 3: Inspect the peer group comparable analysis table and summary median multiples.
Tab 4: Audit core mathematical formulas, sector routing logic, and data lineage metadata.


🔮 Roadmap / Upcoming Features
[ ] Integration of a 3-stage Discounted Cash Flow (DCF) valuation model tab.
[ ] Automated generation of multi-sheet Excel workbook reports (.xlsx).
[ ] Real-time SEC filing parser integration for direct 10-Q/10-K data extraction.
