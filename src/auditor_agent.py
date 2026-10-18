from openai import OpenAI
from src.config import GROQ_API_KEY
from src.schema import FinancialMetrics

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

def audit_financial_extraction(metrics: FinancialMetrics, filing_snippet: str) -> FinancialMetrics:
    """Audits extracted financial metrics against the raw SEC snippet for accuracy."""
    print(f"Auditor Agent reviewing metrics for {metrics.ticker}...")
    
    audit_prompt = f"""
    You are a rigorous Investment Banking Senior Auditor. Review the extracted JSON metrics 
    against the provided SEC filing snippet. Ensure revenue ({metrics.revenue}) and net income 
    ({metrics.net_income}) are realistic and match the scale of the text. 
    If you spot any glaring discrepancy or hallucination, correct them in the JSON.
    
    Extracted JSON:
    {metrics.model_dump_json()}
    
    Filing Snippet:
    {filing_snippet[:4000]}
    
    Return the verified JSON object matching the exact schema keys.
    """

    completion = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": "You are a strict financial auditor. Output valid JSON only."},
            {"role": "user", "content": audit_prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    audited_json = completion.choices[0].message.content
    verified_metrics = FinancialMetrics.model_validate_json(audited_json)
    print(f"Audit complete for {verified_metrics.ticker}. Data verified.")
    return verified_metrics