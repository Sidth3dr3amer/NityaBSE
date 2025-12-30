import os
from dotenv import load_dotenv
from summarizer import summarize_text

load_dotenv()  # <-- REQUIRED

def main():
    print("[TEST] GROQ_API_KEY present:", bool(os.getenv("GROQ_API_KEY")))

    title = "Company announces quarterly results"
    subject = "Q4 financial results"
    description = (
        "The company reported a 10% increase in revenue year over year and a net profit "
        "of $5 million. Management cited stronger demand and cost control measures."
    )

    summary = summarize_text(title, subject, description)
    print("\n[TEST] Summary:\n", summary)

if __name__ == "__main__":
    main()
