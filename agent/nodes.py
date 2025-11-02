# agent/nodes.py
"""
LangGraph Node Definitions
Each node is a step in the agent workflow
"""

import time
from agent.state import AgentState
from agent.tools import NewSearchTool, ContentExtractorTool, SourceAnalyzerTool
from config import MAX_RESULTS, SEARCH_QUERY_VARIANTS

def plan_node(state: AgentState, logger=None) -> AgentState:
    """
    PLAN NODE: Analyze query and generate search strategies
    """
    query = state["query"]
    
    # Classify intent
    intent = "general"
    query_lower = query.lower()
    
    if any(x in query_lower for x in ["latest", "today", "now", "breaking", "just happened"]):
        intent = "breaking_news"
    elif any(x in query_lower for x in ["trend", "analysis", "why", "how", "impact"]):
        intent = "analysis"
    
    # Generate query variations
    variations = [
        query,  # Original
        f"{query} news 2025",  # Add context
        " ".join(query.split()[:3])  # Simplified
    ]
    
    # Log
    state["agent_log"].append({
        "step": "plan",
        "intent": intent,
        "query_variations": variations,
        "timestamp": time.time()
    })
    
    if logger:
        logger.info(f"Plan: intent={intent}, variations={len(variations)}")
    
    return {
        **state,
        "intent": intent,
        "search_queries": variations
    }


def search_node(state: AgentState, newsapi_key: str, gnews_key: str = None, logger=None) -> AgentState:
    """
    SEARCH NODE: Query news APIs for articles
    """
    try:
        search_tool = NewSearchTool(newsapi_key, gnews_key)
        
        # Use primary query
        primary_query = state["search_queries"][0]
        articles = search_tool.search(primary_query, max_results=MAX_RESULTS)
        
        if not articles:
            state["errors"].append("No articles found from any API")
        
        state["agent_log"].append({
            "step": "search",
            "query": primary_query,
            "articles_found": len(articles),
            "timestamp": time.time()
        })
        
        if logger:
            logger.info(f"Search: found {len(articles)} articles")
        
        return {
            **state,
            "raw_articles": articles
        }
    
    except Exception as e:
        state["errors"].append(f"Search failed: {str(e)}")
        if logger:
            logger.error(f"Search error: {e}")
        return state


def extract_node(state: AgentState, logger=None) -> AgentState:
    """
    EXTRACT NODE: Extract full content from article URLs
    """
    try:
        if not state["raw_articles"]:
            state["errors"].append("No articles to extract")
            return state
        
        extractor = ContentExtractorTool()
        extracted = extractor.extract(state["raw_articles"])
        
        success_count = sum(1 for a in extracted if a.get("extraction_success", False))
        
        state["agent_log"].append({
            "step": "extract",
            "total_articles": len(extracted),
            "successful": success_count,
            "timestamp": time.time()
        })
        
        if logger:
            logger.info(f"Extract: {success_count}/{len(extracted)} successful")
        
        return {
            **state,
            "extracted_articles": extracted
        }
    
    except Exception as e:
        state["errors"].append(f"Extraction failed: {str(e)}")
        if logger:
            logger.error(f"Extract error: {e}")
        return state


def analyze_node(state: AgentState, logger=None) -> AgentState:
    """
    ANALYZE NODE: Score sources by credibility
    """
    try:
        if not state["extracted_articles"]:
            state["errors"].append("No articles to analyze")
            return state
        
        analyzer = SourceAnalyzerTool()
        analyzed = analyzer.analyze(state["extracted_articles"])
        
        # Sort by credibility
        ranked = sorted(analyzed, key=lambda a: a.get("credibility_score", 0), reverse=True)
        
        state["agent_log"].append({
            "step": "analyze",
            "articles_analyzed": len(analyzed),
            "top_credibility": ranked[0].get("credibility_score", 0) if ranked else 0,
            "timestamp": time.time()
        })
        
        if logger:
            logger.info(f"Analyze: scored {len(analyzed)} articles")
        
        return {
            **state,
            "analyzed_articles": ranked
        }
    
    except Exception as e:
        state["errors"].append(f"Analysis failed: {str(e)}")
        if logger:
            logger.error(f"Analyze error: {e}")
        return state


def summarize_node(state: AgentState, groq_key: str, logger=None) -> AgentState:
    """
    SUMMARIZE NODE: Generate AI summary using Groq LLM
    """
    try:
        if not state["analyzed_articles"]:
            state["errors"].append("No articles to summarize")
            return state
        
        from langchain_groq import ChatGroq
        from config import GROQ_MODEL, LLM_MAX_TOKENS, LLM_TEMPERATURE
        
        llm = ChatGroq(
            model=GROQ_MODEL,
            groq_api_key=groq_key,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS
        )
        
        # Prepare context
        articles_context = "\n\n".join([
            f"[Source: {a.get('source', 'Unknown')} - {a.get('credibility_tier', 'unknown')}]\n"
            f"Title: {a.get('title', 'N/A')}\n"
            f"Content: {a.get('full_content', a.get('description', ''))[:800]}"
            for a in state["analyzed_articles"][:5]
        ])
        
        prompt = f"""You are an expert news analyst. Synthesize the following articles about "{state['query']}" into a comprehensive, 300-500 word summary.

ARTICLES:
{articles_context}

REQUIREMENTS:
1. Write a flowing summary that synthesizes insights from multiple articles
2. Start with the most important finding
3. Integrate information from different sources naturally
4. Use [Source Name] format to attribute claims
5. Identify common themes and key insights
6. Note any conflicting viewpoints
7. Use accessible, professional language
8. Focus on facts, avoid speculation
9. End with implications or what's next

SUMMARY:"""
        
        response = llm.invoke(prompt)
        summary = response.content
        
        state["agent_log"].append({
            "step": "summarize",
            "summary_length": len(summary),
            "timestamp": time.time()
        })
        
        if logger:
            logger.info(f"Summarize: generated {len(summary)} char summary")
        
        return {
            **state,
            "summary": summary
        }
    
    except Exception as e:
        state["errors"].append(f"Summarization failed: {str(e)}")
        if logger:
            logger.error(f"Summarize error: {e}")
        return state
