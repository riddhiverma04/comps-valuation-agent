from openai import OpenAI
from src.config import GROQ_API_KEY
from src.schema import FinancialMetrics

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

def extract_relevant_snippet(filing_path: str, max_chars: int = 8000) -> str:
    with open(filing_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    keywords = [
        "CONSOLIDATED STATEMENTS OF OPERATIONS",
        "CONSOLIDATED STATEMENTS OF INCOME",
        "STATEMENTS OF OPERATIONS",
        "CONSOLIDATED BALANCE SHEETS",
        "BALANCE SHEETS"
    ]

    for kw in keywords:
        idx = content.upper().find(kw)
        if idx != -1:
            return content[idx : idx + max_chars]

    return content[:max_chars]

def parse_financials_from_filing(filing_path: str, ticker: str) -> tuple[FinancialMetrics, str]:
    """Reads filing snippet, extracts metrics, and returns both metrics and raw snippet for auditing."""
    print(f"Reading and parsing SEC filing text for {ticker}...")
    
    filing_text = extract_relevant_snippet(filing_path)
        
    prompt = f"""
    You are an elite Investment Banking Analyst. Extract the key financial statement metrics 
    for ticker '{ticker}' from the following SEC filing text excerpt. 
    Ensure all financial numbers are normalized and expressed in **millions of USD**.
    
    Return your answer STRICTLY as a JSON object matching these keys:
    - ticker (string)
    - company_name (string)
    - fiscal_year (integer)
    - revenue (float)
    - operating_income (float)
    - net_income (float)
    - depreciation_amortization (float)
    - cash_and_equivalents (float)
    - total_debt (float)
    - revenue_prior_year (float)
    - revenue_two_years_ago (float)
    - ltm_revenue (float)
    
    If a line item is not explicitly found, output 0.0.
    
    Filing Excerpt:
    {filing_text}
    """

    completion = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": "You are a precise financial document parser. Output valid JSON only."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    extracted_metrics = FinancialMetrics.model_validate_json(completion.choices[0].message.content)
    return extracted_metrics, filing_text