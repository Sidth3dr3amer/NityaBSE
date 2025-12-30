import os
import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.1-8b-instant"  # ✅ guaranteed

def summarize_text(title: str, subject: str, description: str | None = None) -> str | None:
    if not GROQ_API_KEY:
        print("[SUMMARY] GROQ_API_KEY not set")
        return None

    text = f"{title}. {subject}. {description or ''}".strip()

    if len(text) < 50:
        return subject or title

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a financial compliance summarizer. Write concise, factual summaries."
            },
            {
                "role": "user",
                "content": (
                    "Summarize the following BSE corporate announcement in 2–3 professional sentences. "
                    "Focus only on material investor-relevant information.\n\n"
                    f"{text}"
                )
            }
        ],
        "temperature": 0.2,
        "max_tokens": 200
    }

    try:
        resp = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=15,
        )

        resp.raise_for_status()
        summary = resp.json()["choices"][0]["message"]["content"].strip()
        print("   [SUMMARY] Generated via Groq")
        return summary

    except Exception as e:
        print("[SUMMARY] Groq failed:", e)
        return subject or title
