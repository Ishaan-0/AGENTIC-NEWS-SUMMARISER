import os
from dotenv import find_dotenv, load_dotenv
import logging
from config import LOG_LEVEL

def get_api_keys():
    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path)
    news_key = os.getenv("NEWS_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    gnews_key = os.getenv("GNEWS_API_KEY")
    
    return news_key, groq_key, gnews_key

def validate_query(query: str):
    query = query.strip() if query else ""
    
    if not query:
        return False, "❌ Please enter a news topic"
    
    if len(query) < 3:
        return False, "❌ Topic too short (minimum 3 characters)"
    
    if len(query) > 200:
        return False, "❌ Topic too long (maximum 200 characters)"
    
    return True, query

def setup_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger
