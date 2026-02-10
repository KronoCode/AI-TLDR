"""Tool: summarize text (optional extra shortening)."""
from ollama import chat


def summarize(text: str, max_sentences: int = 20) -> str:
    """Shorten long text to at most max_sentences sentences. Use when the TLDR is too long before emailing."""
    if not text or len(text) < 500:
        return text
    r = chat(
        model="llama3.2",
        messages=[
            {"role": "user", "content": f"Summarize in at most {max_sentences} sentences:\n\n{text}"}
        ],
    )
    return r["message"]["content"]
