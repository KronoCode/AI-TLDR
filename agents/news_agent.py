"""News agent: fetch latest business news from around the world."""
# Option A: use a news API (e.g. NewsAPI, GNews). Option B: scrape or use RSS.
from config import NEWS_API_KEY


def get_business_news() -> str:
    """Fetch latest business news from around the world. Call this first if you want to include recent news in the TLDR."""
    # TODO: call NewsAPI / GNews / RSS with "business" query, return top N headlines + snippets
    # Example: requests.get(f"https://newsapi.org/v2/everything?q=business&apiKey={NEWS_API_KEY}")
    return ""
