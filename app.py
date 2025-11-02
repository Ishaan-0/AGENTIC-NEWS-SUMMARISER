import gradio as gr
import pandas as pd
import tempfile
from datetime import date
from utils import get_api_keys, validate_query, setup_logger
from agent.graph import execute_agent
from config import GRADIO_PORT, GRADIO_SHARE, GRADIO_THEME

news_key, groq_key, gnews_key = get_api_keys()

logger = setup_logger("news-aggregator-ui")

# State for API keys (session-based)
api_keys_store = {
    "news": news_key,
    "groq": groq_key,
    "gnews": gnews_key
}

def save_api_keys(news_key: str, groq_key: str, gnews_key: str = ""):
    api_keys_store["news"] = news_key
    api_keys_store["groq"] = groq_key
    api_keys_store["gnews"] = gnews_key
    
    logger.info("API keys saved to session")
    return "✅ Configuration saved successfully!"

def search_and_summarize(query: str, news_key: str, groq_key: str, gnews_key: str = ""):
    # Validate query
    valid, processed_query = validate_query(query)
    if not valid:
        return processed_query, pd.DataFrame(), f"❌ {processed_query}"
    
    # Use provided keys or fallback to session store
    news_api_key = news_key or api_keys_store.get("news")
    groq_api_key = groq_key or api_keys_store.get("groq")
    gnews_api_key = gnews_key or api_keys_store.get("gnews")
    
    # verify API keys
    if not news_api_key or not groq_api_key:
        return (
            "❌ Missing API keys. Please configure in Settings tab.",
            pd.DataFrame(),
            "❌ Configuration incomplete"
        )
    
    logger.info(f"Processing query: {processed_query}")
    
    result = execute_agent(
        processed_query,
        news_api_key,
        groq_api_key,
        gnews_api_key,
        logger=logger
    )
    
    if result["success"]:
        status = f"✅ Done in {result['processing_time']:.2f}s"
    else:
        status = f"❌ Error: {result['summary']}"

    sources = result.get("sources", pd.DataFrame())
    return result["summary"], sources, status

def export_summary(summary_md: str, sources_df):
    try:
        filename = f"summary_{date.today()}.txt"
        
        with tempfile.NamedTemporaryFile(
            delete=False,
            mode="w",
            encoding="utf-8",
            suffix=".txt"
        ) as f:
            f.write(summary_md)
            
            if isinstance(sources_df, pd.DataFrame) and not sources_df.empty:
                f.write("\n\n" + "="*80 + "\n")
                f.write("SOURCES\n")
                f.write("="*80 + "\n\n")
                
                for idx, row in sources_df.iterrows():
                    f.write(f"{int(row['Rank'])}. {row['Title']}\n")
                    f.write(f"   Source: {row['Source']}\n")
                    f.write(f"   Date: {row['Date']}\n")
                    f.write(f"   Credibility: {row['Credibility']}\n")
                    f.write(f"   URL: {row['URL']}\n\n")
        
        logger.info(f"Summary exported: {filename}")
        return f.name
    
    except Exception as e:
        logger.error(f"Export failed: {e}")
        return None

with gr.Blocks(
    title="📰 News Aggregator with LangGraph",
    theme=gr.themes.Soft(primary_hue="blue", secondary_hue="orange"),
    css=".block { border-radius: 8px; } h1 { color: #1e40af; }"
) as demo:
    
    gr.Markdown("# 📰 Smart News Aggregator & Summarizer")
    gr.Markdown("*AI-powered news aggregation with LangGraph framework*")
    
    with gr.Tabs():
        
        # TAB 1: SEARCH
        with gr.TabItem("🔍 Search", id="search_tab"):
            gr.Markdown("## Search for News")
            gr.Markdown("Enter a topic and we'll search, aggregate, and summarize the latest news for you.")
            
            query_input = gr.Textbox(
                label="What news topic interests you?",
                placeholder="e.g., AI regulations, climate change, tech news, quantum computing",
                lines=2,
                max_length=200
            )
            
            search_btn = gr.Button(
                "🔍 Find & Summarize News",
                variant="primary",
                size="lg"
            )
            
            search_status = gr.Markdown("**Status:** Ready")
        
        # TAB 2: RESULTS
        with gr.TabItem("📰 Results", id="results_tab"):
            gr.Markdown("## Results")
            
            summary_output = gr.Markdown(
                value="**Results will appear here after search**"
            )
            
            sources_output = gr.Dataframe(
                headers=["Rank", "Title", "Source", "Date", "Credibility", "URL"],
                interactive=False,
                label="Sources"
            )
            
            export_btn = gr.Button("📥 Export Summary", variant="secondary")
            file_output = gr.File(label="Download")
        
        # TAB 3: SETTINGS
        with gr.TabItem("⚙️ Settings", id="settings_tab"):
            gr.Markdown("## API Configuration")
            gr.Markdown("Configure your API keys for the agent to work. You can also pass keys directly in the Search tab.")
            
            news_key_input = gr.Textbox(
                label="NewsAPI Key",
                type="password",
                placeholder="Get free key from newsapi.org"
            )
            
            groq_key_input = gr.Textbox(
                label="Groq API Key",
                type="password",
                placeholder="Get free key from console.groq.com"
            )
            
            gnews_key_input = gr.Textbox(
                label="GNews API Key (Optional)",
                type="password",
                placeholder="Get free key from gnews.io"
            )
            
            save_btn = gr.Button("✓ Save Configuration", variant="primary")
            status_output = gr.Markdown("**Status:** Not configured")
            
            gr.Markdown("""
            ### Getting API Keys (All Free)
            
            **NewsAPI.org:**
            1. Go to https://newsapi.org
            2. Sign up (free tier: 100 requests/day)
            3. Copy API key from your dashboard
            
            **Groq API:**
            1. Go to https://console.groq.com
            2. Sign up (free tier: 30k tokens/min)
            3. Generate API key in your profile
            
            **GNews (Optional Fallback):**
            1. Go to https://gnews.io
            2. Sign up
            3. Copy your GNews token
            """)
    
    # Event handlers
    search_btn.click(
        fn=search_and_summarize,
        inputs=[query_input, news_key_input, groq_key_input, gnews_key_input],
        outputs=[summary_output, sources_output, search_status]
    )
    
    save_btn.click(
        fn=save_api_keys,
        inputs=[news_key_input, groq_key_input, gnews_key_input],
        outputs=[status_output]
    )
    
    export_btn.click(
        fn=export_summary,
        inputs=[summary_output, sources_output],
        outputs=[file_output]
    )

if __name__ == "__main__":
    logger.info("Starting News Aggregator App with LangGraph")
    demo.launch(
        server_port=GRADIO_PORT,
        share=GRADIO_SHARE,
        show_error=True,
        show_api=True
    )
