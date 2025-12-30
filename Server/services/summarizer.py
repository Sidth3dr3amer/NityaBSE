import os
import requests
from typing import Optional

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama3-8b-8192"

# Phrases we never want in investor summaries
BANNED_PHRASES = [
    "i cannot", "i can't", "unable", "not enough information",
    "please provide", "insufficient", "cannot determine",
    "as an ai", "i am an ai"
]

def summarize_text(
    title: str,
    subject: str,
    description: Optional[str] = None
) -> str:
    """
    Generate a 2–3 sentence investor-focused summary using Groq (LLaMA-3).
    Guaranteed non-blocking and production-safe.
    """

    # Build clean input
    parts = [p for p in [title, subject, description] if p]
    full_text = ". ".join(parts).strip()

    # Hard fallback (never fail scraper)
    fallback = subject or title or ""

    # Safety guards
    if not GROQ_API_KEY:
        print("   [SUMMARY] GROQ_API_KEY not set, using fallback")
        return fallback

    if len(full_text) < 50:
        return fallback

    prompt = f"""
You are a corporate disclosure analyst.

Write a professional 2–3 sentence summary of the following BSE corporate announcement.

RULES:
- Be factual and concise
- Focus on material investor-relevant information
- Use formal business language
- Do NOT speculate
- Do NOT mention missing information

ANNOUNCEMENT:
{full_text}

SUMMARY:
"""

    try:
        response = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": "You summarize stock exchange announcements for investors."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
                "max_tokens": 180,
            },
            timeout=12,  # Railway-safe timeout
        )

        response.raise_for_status()
        data = response.json()

        summary = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )

        # Quality checks
        if (
            summary
            and len(summary) > 25
            and not any(p in summary.lower() for p in BANNED_PHRASES)
        ):
            print("   [SUMMARY] Generated via Groq")
            return summary.replace("SUMMARY:", "").strip()

    except Exception as e:
        print("   [SUMMARY] Groq failed:", str(e))

    # Guaranteed safe fallback
    return fallback[:200] + "..." if len(fallback) > 200 else fallback
