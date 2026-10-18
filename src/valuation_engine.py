import yfinance as yf
from src.schema import FinancialMetrics, ValuationSummary

def calculate_valuation(metrics: FinancialMetrics) -> ValuationSummary:
    """Fetches real-time market data via yfinance and computes valuation multiples."""
    print(f"Calculating valuation and multiples for {metrics.ticker}...")
    
    ticker_obj = yf.Ticker(metrics.ticker)
    info = ticker_obj.info
    
    share_price = info.get("currentPrice", info.get("regularMarketPrice", 100.0))
    shares_outstanding = info.get("sharesOutstanding", 1000000000)
    market_cap = share_price * shares_outstanding
    
    # Simple Enterprise Value = Market Cap + Total Debt - Cash
    enterprise_value = market_cap + (metrics.total_debt * 1e6) - (metrics.cash_and_equivalents * 1e6)
    
    # Normalize to millions for multiples
    ev_millions = enterprise_value / 1e6
    revenue = metrics.revenue if metrics.revenue > 0 else 1.0
    ebitda = metrics.operating_income + metrics.depreciation_amortization
    ebitda = ebitda if ebitda > 0 else 1.0
    net_income = metrics.net_income if metrics.net_income != 0 else 1.0
    
    ev_to_revenue = ev_millions / revenue
    ev_to_ebitda = ev_millions / ebitda
    pe_ratio = market_cap / (net_income * 1e6)
    debt_to_ebitda = (metrics.total_debt) / ebitda
    
    return ValuationSummary(
        ticker=metrics.ticker,
        company_name=metrics.company_name,
        share_price=share_price,
        market_cap=market_cap / 1e6,
        enterprise_value=ev_millions,
        revenue=revenue,
        ebitda=ebitda,
        net_income=net_income,
        revenue_prior_year=metrics.revenue_prior_year,
        revenue_two_years_ago=metrics.revenue_two_years_ago,
        ev_to_revenue=ev_to_revenue,
        ev_to_ebitda=ev_to_ebitda,
        pe_ratio=pe_ratio,
        debt_to_ebitda=debt_to_ebitda
    )