from pydantic import BaseModel
from typing import Optional

class FinancialMetrics(BaseModel):
    ticker: Optional[str] = None  # <-- Add this field
    revenue: Optional[float] = 0.0
    operating_income: Optional[float] = 0.0
    net_income: Optional[float] = 0.0
    depreciation_amortization: Optional[float] = 0.0
    cash_and_equivalents: Optional[float] = 0.0
    total_debt: Optional[float] = 0.0
    revenue_prior_year: Optional[float] = 0.0
    revenue_two_years_ago: Optional[float] = 0.0
    ltm_revenue: Optional[float] = 0.0

class ValuationSummary(BaseModel):
    ticker: str
    company_name: str
    share_price: float
    market_cap: float
    enterprise_value: float
    revenue: float
    ebitda: float
    net_income: float
    
    # Historical / Growth metrics
    revenue_prior_year: float = 0.0
    revenue_two_years_ago: float = 0.0
    
    ev_to_revenue: float
    ev_to_ebitda: float
    pe_ratio: float
    debt_to_ebitda: float