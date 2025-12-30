import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"

def summarize_text(title, subject, description):
    """
    Summarize announcement using Ollama.
    Returns summary or original description if Ollama fails.
    """
    
    # Combine all available information
    full_text = f"{title}. {subject}. {description if description else ''}"
    
    prompt = f"""You are a corporate communications expert. Create a professional 2-3 sentence summary of this BSE announcement.

ANNOUNCEMENT TEXT:
{full_text}

INSTRUCTIONS:
- Write in clear, professional business language
- State the key facts: what happened, who is involved, and when
- Focus on material information investors need to know
- Use active voice and present/past tense appropriately
- Do NOT say you cannot summarize or need more information
- Do NOT ask questions or mention missing details
- Work with the information provided and extract the essence

SUMMARY:"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Lower temperature for more consistent output
                    "num_predict": 120,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1
                }
            },
            timeout=30
        )
        
        if response.status_code == 200:
            summary = response.json().get("response", "").strip()
            
            # Filter out unhelpful responses
            unwanted_phrases = [
                "i cannot", "i can't", "i'm unable", "no information",
                "cannot determine", "not enough", "insufficient",
                "please provide", "need more", "missing"
            ]
            
            if summary and not any(phrase in summary.lower() for phrase in unwanted_phrases):
                # Clean up the summary
                summary = summary.replace("SUMMARY:", "").strip()
                summary = summary.split('\n')[0]  # Take only first paragraph
                
                if len(summary) > 20:  # Ensure it's substantial
                    print(f"   [SUMMARY] Generated summary using Ollama")
                    return summary
        
    except Exception as e:
        print(f"   [SUMMARY] Ollama not available: {e}")
    
    # Fallback: Create a basic summary from available text
    fallback = subject if subject else title
    if len(fallback) > 200:
        fallback = fallback[:197] + "..."
    
    return fallback