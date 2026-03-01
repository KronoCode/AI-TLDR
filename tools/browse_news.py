"""News agent: fetch latest business news from around the world."""
# Option A: use a news API (e.g. NewsAPI, GNews). Option B: scrape or use RSS.

from serpapi import GoogleSearch
from config import NEWS_API_KEY
import mlflow
import tools.scoring

TRUSTED_DOMAINS = {
    "reuters.com", "bloomberg.com", "wsj.com",
    "ft.com", "cnbc.com", "marketwatch.com",
    "economist.com", "forbes.com", "medium.com"}

KEYWORDS = {"market", "stocks", "earnings", "inflation", "rates", "economy", "business"}

@mlflow.trace(name="news_fetcher_tool")
def browse_news(search_query : str = "latest business news") -> str:
    """Fetch latest business news from around the world. Call this first if you want to include recent news in the TLDR."""
    web_search = browse_internet_for_news(search_query)
    articles = normalize_results(web_search)
    top_articles = tools.scoring.select_top_articles(articles)
    cleaned_articles = tools.scoring.build_article_html(top_articles)
    good_articles = [a for a in cleaned_articles if a["success"] and len(a.get("body","").split()) > 300]

    concatenated = ""
    for article in good_articles:
        body = article.get("body") or ""
        link = article.get("link") or ""
        if body:
            concatenated += "[START]\n" + body.strip() + f"\nlink:{link}" + "\n[END]\n"

    return concatenated

#region NEWS WEB BROWSING
def browse_internet_for_news(search_query) -> str:
    """Browse the internet for the latest business news."""
    serpApi_output = GoogleSearch({
        "engine": "google_news",
        "q": search_query,
        "api_key": NEWS_API_KEY,
    })
    result = serpApi_output.get_dict()
    return result

def normalize_results(serp):
    return serp.get("news_results") or serp.get("organic_results") or []

#endregion
