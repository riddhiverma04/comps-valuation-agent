import yfinance as yf

SECTOR_PEERS = {
    "Technology": ["AAPL", "MSFT", "GOOGL", "META", "NVDA"],
    "Financial Services": ["JPM", "BAC", "WFC", "GS", "MS"],
    "Consumer Cyclical": ["AMZN", "TSLA", "NKE", "SBUX", "HD"]
}

def discover_peers(target_ticker: str) -> list[str]:
    """Discovers peer tickers based on the target company's sector."""
    try:
        ticker_obj = yf.Ticker(target_ticker)
        sector = ticker_obj.info.get("sector", "Technology")
        print(f"Discovered sector for {target_ticker}: {sector}")
        
        peers = SECTOR_PEERS.get(sector, ["AAPL", "MSFT"])
        if target_ticker not in peers:
            peers.insert(0, target_ticker)
        return peers[:5]
    except Exception as e:
        print(f"Peer discovery fallback triggered due to: {e}")
        return [target_ticker]