import pytest
from src.schema import FinancialMetrics
from src.valuation_engine import calculate_valuation

def test_calculate_valuation():
    # Setup mock financial metrics
    mock_metrics = FinancialMetrics(
        ticker="TEST",
        company_name="Test Corp",
        fiscal_year=2024,
        revenue=1000.0,         # $1B revenue
        operating_income=300.0, # $300M EBIT
        net_income=200.0,       # $200M Net Income
        depreciation_amortization=50.0,
        cash_and_equivalents=500.0,
        total_debt=1000.0
    )
    
    # Run valuation engine
    valuation = calculate_valuation(mock_metrics)
    
    # Assertions to check correctness
    assert valuation.ticker == "TEST"
    assert valuation.company_name == "Test Corp"
    assert valuation.ebitda == 350.0 # operating_income + D&A
    assert valuation.ev_to_revenue > 0
    assert valuation.pe_ratio > 0