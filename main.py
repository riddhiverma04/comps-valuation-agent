import os
import argparse
from src.database import init_db, save_valuation_to_db
from src.peer_discovery import discover_peers
from src.sec_fetcher import fetch_latest_10k
from src.parser_agent import parse_financials_from_filing
from src.auditor_agent import audit_financial_extraction
from src.valuation_engine import calculate_valuation
from src.excel_exporter import export_comps_to_excel
from src.chart_generator import generate_comps_chart

def main():
    parser = argparse.ArgumentParser(description="Automated Comps & Valuation Agent")
    parser.add_argument("--ticker", type=str, default="AAPL", help="Target stock ticker for comps analysis")
    args = parser.parse_args()

    print("==================================================")
    print("   Enterprise Automated Comps & Valuation Agent   ")
    print("==================================================")

    # 1. Initialize SQLite Database
    init_db()

    # 2. Dynamic Peer Discovery based on target argument
    tickers = discover_peers(args.ticker)
    print(f"\nDiscovered Peer Group for {args.ticker}: {tickers}\n")

    valuations = []

    for ticker in tickers:
        print(f"--- Processing Ticker: {ticker} ---")
        try:
            # Step A: Download SEC Filing
            filing_path = fetch_latest_10k(ticker)
            if not filing_path or not os.path.exists(filing_path):
                print(f"Skipping {ticker}: Filing not found.")
                continue

            # Step B: Parse Financials
            metrics, raw_snippet = parse_financials_from_filing(filing_path, ticker)

            # Step C: Multi-Agent Auditor Review
            audited_metrics = audit_financial_extraction(metrics, raw_snippet)

            # Step D: Pure Python Valuation Math
            valuation = calculate_valuation(audited_metrics)
            valuations.append(valuation)

            # Step E: Save to SQL Database
            save_valuation_to_db(audited_metrics, valuation)
            print(f"Successfully processed and saved valuation for {ticker}!\n")

        except Exception as e:
            print(f"Error processing {ticker}: {e}\n")

    if valuations:
        # Step F: Export final styled spreadsheet and peer comparison chart
        export_comps_to_excel(valuations)
        generate_comps_chart(valuations)
        print("Workflow complete! Saved to comps_output.xlsx, comps_chart.png, and recorded in comps_database.db.")
    else:
        print("No valuations were successfully generated.")

if __name__ == "__main__":
    main()