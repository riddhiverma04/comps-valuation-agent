import os
from sec_edgar_downloader import Downloader
from src.config import SEC_USER_AGENT

def get_sec_downloader():
    """Initializes the SEC EDGAR downloader using the required User-Agent."""
    # Split user agent into company name and email format required by the library
    parts = SEC_USER_AGENT.split(" ", 1)
    company_name = parts[0]
    email = parts[1] if len(parts) > 1 else "admin@domain.com"

    # Downloader stores filings in the local 'data' directory
    return Downloader(company_name, email, "data")

def fetch_latest_10k(ticker: str) -> str:
    """Downloads the latest 10-K filing for a ticker and returns the file path."""
    dl = get_sec_downloader()
    print(f"Downloading latest 10-K filing for {ticker} from SEC EDGAR...")

    # Download up to 1 latest 10-K filing
    dl.get("10-K", ticker, limit=1)

    # Locate the downloaded file path
    filing_dir = os.path.join("data", "sec-edgar-filings", ticker.upper(), "10-K")
    if not os.path.exists(filing_dir):
        raise FileNotFoundError(f"Could not find downloaded filing directory for {ticker}")

    # Find the specific filing accession folder and file
    sub_dirs = os.listdir(filing_dir)
    if not sub_dirs:
        raise FileNotFoundError(f"No filing subdirectories found for {ticker}")

    accession_dir = os.path.join(filing_dir, sub_dirs[0])
    files = os.listdir(accession_dir)

    target_file = None
    for f in files:
        if f.endswith(".txt") or f.endswith(".htm"):
            target_file = os.path.join(accession_dir, f)
            break

    if not target_file:
        raise FileNotFoundError(f"No valid filing document found in {accession_dir}")

    print(f"Successfully located filing at: {target_file}")
    return target_file