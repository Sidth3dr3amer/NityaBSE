import os
from dotenv import load_dotenv
load_dotenv()

from summarizer import summarize_text


def main():
    print("[TEST] GROQ_API_KEY present:", bool(os.getenv("GROQ_API_KEY")))

    title = "Company announces quarterly results"
    subject = "Q4 financial results"
    description = ("Healthy resource profile with strong brand equity in Kerala. "
"Resource profile of the bank has remained resilient, backed by its strong market position among NRIs, especially in Kerala. "
"Deposits (standalone) increased 12.3% on-year to Rs 2.84 lakh crore as on March 31, 2025, out of which NRIs accounted "
"for around 29%. As on September 30, 2025, the deposit base stood at Rs 2.89 lakh crore. The bank had a market share of "
"18.4% in India's inward remittances in fiscal 2025, compared to 18.7% in the previous fiscal. These factors impart stability to "
"the resource base while aiding the overall profitability through fee income."
                    
        
    )

    summary = summarize_text(title, subject, description)
    print("\n[TEST] Summary:\n", summary)

if __name__ == "__main__":
    main()
