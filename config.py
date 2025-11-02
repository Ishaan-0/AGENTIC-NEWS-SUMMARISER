# API Endpoints
NEWS_API_BASE = "https://newsapi.org/v2"
GNEWS_API_BASE = "https://gnews.io/api/v4"
GROQ_API_BASE = "https://api.groq.com/openai/v1"

# Agent Parameters
MAX_RESULTS = 5
MAX_SUMMARY_LENGTH = 500
SEARCH_QUERY_VARIANTS = 3

# Timeouts (seconds)
SEARCH_TIMEOUT = 5
EXTRACT_TIMEOUT = 10
SUMMARIZE_TIMEOUT = 6

# UI Configuration
GRADIO_THEME = "soft"
GRADIO_PORT = 7860
GRADIO_SHARE = False

# LLM Configuration
GROQ_MODEL = "mixtral-8x7b-32768"
LLM_MAX_TOKENS = 1200
LLM_TEMPERATURE = 0.7

# Logging
LOG_LEVEL = "INFO"
ENABLE_AGENT_LOGGING = True
