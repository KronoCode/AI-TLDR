"""News agent: fetch latest business news from around the world."""
# Option A: use a news API (e.g. NewsAPI, GNews). Option B: scrape or use RSS.
import requests
import trafilatura
from urllib.parse import urlparse
from datetime import datetime,timezone
from serpapi import GoogleSearch
from config import NEWS_API_KEY

TRUSTED_DOMAINS = {
    "reuters.com", "bloomberg.com", "wsj.com",
    "ft.com", "cnbc.com", "marketwatch.com",
    "economist.com", "forbes.com", "medium.com"}

KEYWORDS = {"market", "stocks", "earnings", "inflation", "rates", "economy", "business"}


def get_business_news() -> str:
    """Fetch latest business news from around the world. Call this first if you want to include recent news in the TLDR."""
    web_search = browse_internet_for_news()
    top_articles = select_top_articles(web_search)
    top_articles_data = build_article_html(top_articles)
    
    return ""

def select_top_articles(serp_response, k=5):
    articles = normalize_results(serp_response)
    ranked_articles = sorted(articles, key=score_article, reverse=True)
    return ranked_articles[:k]

def browse_internet_for_news() -> str:
    """Browse the internet for the latest business news."""
    search_query = "latest business news"
    serpApi_output = GoogleSearch({
        "engine": "google_news",
        "q": search_query,
        "api_key": NEWS_API_KEY,
    })
    return serpApi_output

def build_article_html(top_articles):
    article_data = []
    for article in top_articles:
        link = article.get("link")
        body = None
        success = False

        if link:
            html = fetch_html(link)
            if html:
                body = extract_data(html)
                success = body is not None
        
        article_data.append({
            "link" : link,
            "body" : body,
            "success" : success
        })
    return article_data

def fetch_html(url_link):
    """Fetch raw HTML from a URL with a user-agent header."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url_link, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        print(f"Failed to fetch {url_link}: {e}")
    return None

def extract_data(htmlText):
    """Extract main article text using trafilatura."""
    return trafilatura.extract(htmlText)


def normalize_results(serp):
    return serp.get("news_results") or serp.get("organic_results") or []

def score_article(article):
    score = 0

    #domain trust score
    domain = urlparse(article.get("link","")).netloc.replace("www.","")
    if domain in TRUSTED_DOMAINS:
        score +=3

    #freshness score
    date_str = article.get("date")
    if date_str:
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            article_hours_old = (datetime.now(timezone.utc)-dt).total_seconds / 3600 

            if article_hours_old < 6 : score+=3
            if article_hours_old < 24 : score+=2
            if article_hours_old < 72 : score +=1
        except:
            pass
    
    #Keywords score
    title_and_snippet = (article.get("title","") + " " + article.get("snippet","")).lower()
    score += sum(1 for k in KEYWORDS if k in title_and_snippet)

    return score