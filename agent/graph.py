# agent/graph.py
"""
LangGraph Workflow Definition
Main graph that orchestrates all nodes
"""
from langgraph.graph import StateGraph
from agent.state import AgentState
from agent.nodes import plan_node, search_node, extract_node, analyze_node, summarize_node
from agent.formatter import ResultsFormatter
import time

def build_agent_graph(newsapi_key: str, groq_key: str, gnews_key: str = None, logger=None):
    """
    Build the complete LangGraph workflow
    
    Flow: Plan → Search → Extract → Analyze → Summarize
    """
    
    # Create graph
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node(
        "plan",
        lambda state: plan_node(state, logger=logger)
    )
    
    graph.add_node(
        "search",
        lambda state: search_node(state, newsapi_key, gnews_key, logger=logger)
    )
    
    graph.add_node(
        "extract",
        lambda state: extract_node(state, logger=logger)
    )
    
    graph.add_node(
        "analyze",
        lambda state: analyze_node(state, logger=logger)
    )
    
    graph.add_node(
        "summarize",
        lambda state: summarize_node(state, groq_key, logger=logger)
    )
    
    # Define edges (workflow)
    graph.add_edge("plan", "search")
    graph.add_edge("search", "extract")
    graph.add_edge("extract", "analyze")
    graph.add_edge("analyze", "summarize")
    
    # Set entry and finish points
    graph.set_entry_point("plan")
    graph.set_finish_point("summarize")
    
    # Compile
    return graph.compile()


def execute_agent(query: str, newsapi_key: str, groq_key: str, gnews_key: str = None, logger=None):
    """
    Execute the agent and return formatted results
    """
    start_time = time.time()
    
    try:
        # Build graph
        agent_graph = build_agent_graph(newsapi_key, groq_key, gnews_key, logger=logger)
        
        # Initialize state
        initial_state = {
            "query": query,
            "intent": "",
            "search_queries": [],
            "raw_articles": [],
            "extracted_articles": [],
            "analyzed_articles": [],
            "summary": "",
            "sources_dataframe": None,
            "processing_time": 0,
            "errors": [],
            "agent_log": []
        }
        
        # Execute
        result = agent_graph.invoke(initial_state)
        
        # Calculate total time
        processing_time = time.time() - start_time
        result["processing_time"] = processing_time
        
        # Format output
        summary_md = ResultsFormatter.format_summary(
            result["summary"],
            processing_time,
            query
        )
        
        sources_df = ResultsFormatter.format_sources(result["analyzed_articles"])
        
        return {
            "success": True,
            "summary": summary_md,
            "sources": sources_df,
            "processing_time": processing_time,
            "errors": result["errors"],
            "agent_log": result["agent_log"]
        }
    
    except Exception as e:
        processing_time = time.time() - start_time
        if logger:
            logger.error(f"Agent execution failed: {e}")
        
        return {
            "success": False,
            "summary": f"❌ Agent failed: {str(e)}",
            "sources": None,
            "processing_time": processing_time,
            "errors": [str(e)],
            "agent_log": []
        }
