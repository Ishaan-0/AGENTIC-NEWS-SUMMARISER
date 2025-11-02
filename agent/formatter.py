# agent/formatter.py
"""
Format agent results for display
"""

import pandas as pd
from datetime import datetime

class ResultsFormatter:
    """Format agent output for UI display"""
    
    @staticmethod
    def format_summary(summary: str, processing_time: float, query: str) -> str:
        """Format summary as markdown"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return f"""## 📋 Summary for: "{query}"

{summary}

---

**Generated:** {timestamp}  
**Processing Time:** {processing_time:.2f} seconds  
**Status:** ✅ Successfully aggregated and synthesized
"""
    
    @staticmethod
    def format_sources(articles: list) -> pd.DataFrame:
        """Format articles as dataframe for UI"""
        data = []
        
        for i, article in enumerate(articles[:5], 1):
            credibility_score = article.get("credibility_score", 0)
            stars = "⭐" * int(credibility_score) + "☆" * (5 - int(credibility_score))
            
            data.append({
                "Rank": i,
                "Title": article.get("title", "N/A")[:70] + "..." if len(article.get("title", "")) > 70 else article.get("title", "N/A"),
                "Source": article.get("source", "Unknown"),
                "Date": article.get("published_at", "N/A")[:10],
                "Credibility": stars,
                "URL": article.get("url", "N/A"),
            })
        
        return pd.DataFrame(data)
    
    @staticmethod
    def format_error_message(errors: list) -> str:
        """Format error messages for display"""
        if not errors:
            return "✅ No errors"
        
        error_text = "\n".join([f"- {e}" for e in errors])
        return f"⚠️ Errors encountered:\n{error_text}"
