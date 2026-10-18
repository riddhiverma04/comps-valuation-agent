from pydantic import BaseModel, Field

class FinancialMetrics(BaseModel):
    ticker: str = Field(description="Stock ticker symbol")
    company_name: str = Field(default="Unknown")
    fiscal_year: int = Field(default=2024)
    
    # Latest FY Metrics
    revenue: float = Field(default=0.0)
    operating_income: float = Field(default=0.0)
    net_income: float = Field(default=0.0)
    depreciation_amortization: float = Field(default=0.0)
    cash_and_equivalents: float = Field(default=0.0)
    total_debt: float = Field(default=0.0)
    
    # Multi-Year Historical Growth Context (in millions)
    revenue_prior_year: float = Field(default=0.0, description="Revenue for FY-1")
    revenue_two_years_ago: float = Field(default=0.0, description="Revenue for FY-2")
    ltm_revenue: float = Field(default=0.0, description="Last Twelve Months Revenue")

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