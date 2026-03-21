"""TLDR agent: finance tips or business concepts, for beginner / intermediate / expert."""

import serpapi
from config import NEWS_API_KEY
import tools.scoring
import mlflow

TRUSTED_DOMAINS = {
    "reuters.com", "bloomberg.com", "wsj.com",
    "ft.com", "cnbc.com", "marketwatch.com",
    "economist.com", "forbes.com", "medium.com",
    "reddit.com", "quora.com"}

KEYWORDS = {"market", "stocks", "earnings", "inflation", "rates", "economy", "business, chatgpt, anthropic, "}

@mlflow.trace(name="internet_searcher")

def browse_internet(search_query : str = "", tbm: str ="") -> str:
    """
    Search the web using SerpAPI.
    
    Use the tbm parameter to specify the type of search.
    The tbm parameter is optional and if not provided, the search will be a classic web search.
    This parameter chosen should exactly match the following values:
    - tbm="nws"  → news search (latest articles, press releases)
    - tbm=""     → classic web search (general information)
    - tbm="shop" → shopping search (products, prices)
    - tbm="isch" → image search
    - tbm="vid"  → video search
    - tbm="fin"  → finance search (stock prices, financial data)
    
    Always pick the most appropriate tbm value based on the user's request.
    Examples:
    - "latest AI news" → tbm="nws"
    - "Tesla stock price" → tbm="fin"
    - "best Python books" → tbm="shop"
    - "what is LangGraph" → tbm=""
    """
    web_search = internet_search(search_query, tbm)
    articles = normalize_results(web_search)

    scoring = tools.scoring.Scoring(TRUSTED_DOMAINS, KEYWORDS)

    top_articles = scoring.select_top_articles(articles)
    cleaned_articles = scoring.build_article_html(top_articles)
    good_articles = [a for a in cleaned_articles if a["success"] and len(a.get("body","").split()) > 100]

    concatenated = ""
    for article in good_articles:
        article_nbr=good_articles.index(article) + 1
        body = article.get("body") or ""
        link = article.get("link") or ""
        if body:
            concatenated += f"[START ARTICLE {article_nbr}]\n" + body.strip() + f"\n**Link article source**:{link}" + f"\n[END ARTICLE {article_nbr}]\n"

    return concatenated

#region WEB BROWSING
def internet_search(search_query, tbm) -> str:
    """Browse the internet."""
    params = {
        "q": search_query,
        "tbm": tbm,
        "api_key": NEWS_API_KEY
    }
    # remove tbm if empty (classic search doesn't need it)
    if not tbm:
        params.pop("tbm")
        
    serpApi_output = serpapi.GoogleSearch(params)
    result = serpApi_output.get_dict()
    return result

def normalize_results(serp):
    return serp.get("news_results") or serp.get("organic_results") or []
