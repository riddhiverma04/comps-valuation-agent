import pandas as pd
import numpy as np
import pytest

def test_market_cap_calculation():
    """Verify market capitalization formula."""
    close_price = 150.0
    shares = 10_000_000
    market_cap = close_price * shares
    assert market_cap == 1_500_000_000.0

def test_enterprise_value_calculation():
    """Verify enterprise value formula incorporates total debt and cash correctly."""
    market_cap = 1_500_000_000.0
    total_debt = 200_000_000.0
    cash = 50_000_000.0
    ev = market_cap + total_debt - cash
    assert ev == 1_650_000_000.0

def test_negative_ebitda_handling():
    """Verify that negative or zero EBITDA is handled cleanly to avoid distortion."""
    ev = 1_000_000.0
    ltm_ebitda = -50_000.0
    ev_ebitda = ev / ltm_ebitda if ltm_ebitda > 0 else np.nan
    assert pd.isna(ev_ebitda)

def test_look_ahead_bias_merge_asof():
    """Verify that merge_asof with backward direction prevents look-ahead bias."""
    price_dates = pd.date_range(start='2023-01-01', periods=5, freq='D')
    hist = pd.DataFrame({'Close': [100, 101, 102, 103, 104]}, index=price_dates)
    
    fin_dates = pd.to_datetime(['2023-01-03'])
    fin_df = pd.DataFrame({'LTM_Net_Income': [500]}, index=fin_dates)
    
    hist = hist.sort_index()
    fin_df = fin_df.sort_index()
    
    merged = pd.merge_asof(hist, fin_df, left_index=True, right_index=True, direction='backward')
    
    assert pd.isna(merged.loc['2023-01-01', 'LTM_Net_Income'])
    assert pd.isna(merged.loc['2023-01-02', 'LTM_Net_Income'])
    assert merged.loc['2023-01-03', 'LTM_Net_Income'] == 500
    assert merged.loc['2023-01-04', 'LTM_Net_Income'] == 500