# agent/tools.py
"""
LangGraph tools for the agent
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from config import SEARCH_TIMEOUT, EXTRACT_TIMEOUT, NEWS_API_BASE, GNEWS_API_BASE

class NewSearchTool:
    """Search for news articles from multiple APIs"""
    
    def __init__(self, newsapi_key: str, gnews_key: str = None):
        self.newsapi_key = newsapi_key
        self.gnews_key = gnews_key
    
    def search(self, query: str, max_results: int = 5) -> list:
        """Search articles from NewsAPI and GNews"""
        articles = []
        
        # Try NewsAPI
        try:
            resp = requests.get(
                f"{NEWS_API_BASE}/everything",
                params={
                    "q": query,
                    "sortBy": "publishedAt",
                    "language": "en",
                    "pageSize": max_results,
                    "apiKey": self.newsapi_key
                },
                timeout=SEARCH_TIMEOUT
            )
            resp.raise_for_status()
            for a in resp.json().get("articles", []):
                articles.append({
                    "title": a.get("title"),
                    "source": a.get("source", {}).get("name", "Unknown"),
                    "url": a.get("url"),
                    "image": a.get("urlToImage"),
                    "description": a.get("description"),
                    "published_at": a.get("publishedAt"),
                    "content": a.get("content"),
                    "api_source": "newsapi"
                })
        except Exception as e:
            print(f"NewsAPI error: {e}")
        
        # Try GNews fallback if available
        if self.gnews_key and len(articles) < max_results:
            try:
                resp = requests.get(
                    f"{GNEWS_API_BASE}/search",
                    params={
                        "q": query,
                        "lang": "en",
                        "max": max_results,
                        "token": self.gnews_key
                    },
                    timeout=SEARCH_TIMEOUT
                )
                resp.raise_for_status()
                for a in resp.json().get("articles", []):
                    articles.append({
                        "title": a.get("title"),
                        "source": a.get("source", {}).get("name", "Unknown"),
                        "url": a.get("url"),
                        "image": a.get("image"),
                        "description": a.get("description"),
                        "published_at": a.get("publishedAt"),
                        "content": a.get("content"),
                        "api_source": "gnews"
                    })
            except Exception as e:
                print(f"GNews error: {e}")
        
        # Deduplicate by URL
        unique = {}
        for article in articles:
            url = article.get("url", "")
            if url and url not in unique:
                unique[url] = article
        
        return list(unique.values())[:max_results]


class ContentExtractorTool:
    """Extract full content from article URLs"""
    
    def __init__(self, timeout: int = EXTRACT_TIMEOUT):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0'
        })
    
    def extract(self, articles: list) -> list:
        """Extract content from all articles"""
        extracted = []
        
        for article in articles:
            try:
                url = article.get("url")
                if not url:
                    article["full_content"] = article.get("description", "")
                    extracted.append(article)
                    continue
                
                resp = self.session.get(url, timeout=self.timeout)
                resp.raise_for_status()
                
                soup = BeautifulSoup(resp.content, 'html.parser')
                
                # Remove noise
                for tag in soup(['script', 'style', 'nav', 'footer', 'ads']):
                    tag.decompose()
                
                # Extract body
                text = ""
                selectors = [
                    'article', '[role="main"]', '.article-content',
                    '.post-content', '.entry-content', 'main'
                ]
                
                for selector in selectors:
                    element = soup.select_one(selector)
                    if element:
                        text = element.get_text(separator='\n', strip=True)
                        if len(text) > 100:
                            break
                
                # Fallback: all paragraphs
                if not text or len(text) < 100:
                    paragraphs = soup.find_all('p')
                    text = '\n'.join([p.get_text(strip=True) for p in paragraphs[:10]])
                
                article["full_content"] = text if len(text) > 100 else article.get("description", "")
                article["extraction_success"] = True
                
            except Exception as e:
                article["full_content"] = article.get("description", "")
                article["extraction_success"] = False
            
            extracted.append(article)
        
        return extracted


class SourceAnalyzerTool:
    """Analyze and score source credibility"""
    
    TIER_1 = {"reuters", "apnews", "bbc", "guardian", "ft", "wsj"}
    TIER_2 = {"nytimes", "washingtonpost", "economist"}
    TIER_3 = {"techcrunch", "arstechnica", "wired"}
    
    def analyze(self, articles: list) -> list:
        """Score articles by credibility"""
        analyzed = []
        
        for article in articles:
            source = article.get("source", "Unknown").lower()
            
            # Publication tier (40%)
            pub_score = self._score_publication(source)
            
            # Recency (20%)
            recency_score = self._score_recency(article.get("published_at"))
            
            # Content quality (40%)
            quality_score = self._score_content(article.get("full_content", ""))
            
            # Weighted average
            total_score = (pub_score * 0.4 + recency_score * 0.2 + quality_score * 0.4)
            
            article["credibility_score"] = min(total_score, 5.0)
            article["credibility_tier"] = self._get_tier(total_score)
            
            analyzed.append(article)
        
        return analyzed
    
    def _score_publication(self, source: str) -> float:
        for t1 in self.TIER_1:
            if t1 in source:
                return 5.0
        for t2 in self.TIER_2:
            if t2 in source:
                return 4.0
        for t3 in self.TIER_3:
            if t3 in source:
                return 3.5
        return 2.0
    
    def _score_recency(self, published_at: str) -> float:
        try:
            pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            age_days = (datetime.now(pub_date.tzinfo) - pub_date).days
            
            if age_days < 1:
                return 5.0
            elif age_days < 7:
                return 4.5
            elif age_days < 30:
                return 4.0
            else:
                return 2.0
        except:
            return 3.0
    
    def _score_content(self, content: str) -> float:
        if not content or len(content) < 100:
            return 1.0
        
        evidence_phrases = ["according to", "said", "research", "data", "study"]
        evidence_count = sum(content.lower().count(p) for p in evidence_phrases)
        
        if evidence_count > 3:
            return 4.5
        elif evidence_count > 0:
            return 3.5
        else:
            return 2.5
    
    def _get_tier(self, score: float) -> str:
        if score >= 4.5:
            return "highly_credible"
        elif score >= 3.5:
            return "credible"
        elif score >= 2.5:
            return "moderately_credible"
        else:
            return "low_credibility"
