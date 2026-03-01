import re
import requests
import trafilatura
from urllib.parse import urlparse
from datetime import datetime,timezone


class Scoring:

    def __init__(self, trusted_domains, keywords):
        self.trusted_domains = trusted_domains
        self.keywords = keywords

    def build_article_html(self, top_articles):
        article_data = []

        for article in top_articles:
            link = article.get("link")
            body = None
            success = False

            if link:
                html = self.fetch_html(link)
                if html:
                    body = self.extract_data(html)
                    success = body is not None
            
            article_data.append({
                "link" : link,
                "body" : body,
                "success" : success
            })
        return article_data

    def fetch_html(self, url_link):
        """Fetch raw HTML from a URL with a user-agent header."""
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            response = requests.get(url_link, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.text
        except Exception as e:
            print(f"Failed to fetch {url_link}: {e}")
        return None

    def extract_data(self, htmlText):
        """Extract main article text using trafilatura."""
        return trafilatura.extract(htmlText)

    #endregion
    #region RESULT SCORING

    def select_top_articles(self, articles, k=3):
        ranked_articles = sorted(articles, key=self.score_article, reverse=True)
        return ranked_articles[:k]

    def score_article(self, article):
        score = 0

        #domain trust score
        domain = urlparse(article.get("link","")).netloc.replace("www.","")
        if domain in self.trusted_domains:
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
        score += sum(1 for k in self.keywords if k in title_and_snippet)

        return score


    def is_good_article(self, text, min_words=300):
        if not text:
            return False
        words = len(text.split())
        if words < min_words:
            return False
        if re.search(r"\b(opinion|editorial|commentary|analysis)\b", text[:500].lower()):
            return False
        return True

    #endregion