# AGENTIC-NEWS-SUMMARISER

## Overview
**AGENTIC-NEWS-SUMMARISER** is an **AI-powered news aggregator and summarizer** built using Python. It leverages the LangGraph framework to orchestrate intelligent workflows for news search, extraction, credibility analysis, and summarization. The tool is designed to provide users with cohesive, reliable, and synthesized news summaries on any topic by aggregating content from multiple news APIs and applying credibility scoring, deep extraction, and LLM-based synthesis.

## What Problem Does It Solve?
Modern news consumption is hindered by:
- Floods of articles, duplicates, conflicting perspectives
- Difficulty in finding trustworthy, summarized information from credible sources
- Fragmented news APIs with limited context extraction

**AGENTIC-NEWS-SUMMARISER** solves these challenges by:
- Aggregating, deduplicating, and analyzing news from multiple sources (NewsAPI, GNews)
- Extracting full content even from restricted articles
- Scoring credibility (tiered sources, recency, content quality)
- Synthesizing a comprehensive, fact-focused summary using advanced LLMs

## Project Architecture

The architecture is modular, orchestrated by the LangGraph workflow. Here’s an overview:

### Main Components

| Component         | Purpose / Functionality                                |
|-------------------|-------------------------------------------------------|
| `app.py`          | Gradio-based UI frontend and main entry point. Handles user input, invokes agent graph, displays results. |
| `config.py`       | Centralized configuration of API endpoints, workflow parameters, LLM settings, timeouts, and logging.    |
| `requirements.txt`| Project dependencies (Gradio, LangGraph, LangChain, Groq, Requests, Pandas, etc.).                       |
| `utils.py`        | Utilities for loading API keys, validating input, and logger setup.                                      |

### The `agent/` Directory

Contains the heart of the AI agent logic:

- `__init__.py`: Initializes modules for graph-based agent and state management.
- `graph.py`: Defines the LangGraph workflow:
    - Nodes: `plan`, `search`, `extract`, `analyze`, `summarize`
    - Edges: Node connections representing the agent’s sequential steps
    - Entry point: "plan"
    - Finish point: "summarize"
    - Orchestrates full agent execution, passing evolving state between nodes
- `state.py`: Structures the full agent state, including inputs, intermediate results, logs, errors, and execution metrics.
- `nodes.py`: Implements each workflow step as a distinct node:
    - `plan_node`: Interprets intent, generates search strategies and variations
    - `search_node`: Queries news APIs for articles
    - `extract_node`: Scrapes and extracts full article content
    - `analyze_node`: Scores each article for credibility (tiered source, recency, content evidence)
    - `summarize_node`: Synthesizes a structured summary using Groq LLM
- `tools.py`: Utility tools for search, extraction, and source analysis:
    - `NewSearchTool`: Aggregates from NewsAPI/GNews, deduplicates results
