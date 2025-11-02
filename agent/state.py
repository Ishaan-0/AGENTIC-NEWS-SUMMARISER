"""
LangGraph Agent State Definition
Defines the complete state passed between nodes
"""
from typing import TypedDict, Annotated, Optional
import operator
import pandas as pd

class AgentState(TypedDict):
    """Complete state for the news aggregation agent"""

    # Input
    query: str
    
    # Planning phase
    intent: str  # "breaking_news" | "analysis" | "general"
    search_queries: list  
    
    raw_articles: list  # Raw API results
    
    extracted_articles: list  # Articles with full content extracted
    
    analyzed_articles: list  # Articles with credibility scores
    
    summary: str  # Final AI summary
    sources_dataframe: Optional[pd.DataFrame]  # Formatted sources table
    
    processing_time: float  # Total execution time
    errors: Annotated[list, operator.add]  # Error log (accumulates)
    agent_log: list  # Step-by-step execution log
