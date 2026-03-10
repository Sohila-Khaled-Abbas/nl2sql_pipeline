import logging
from langchain_openai import ChatOpenAI
from sqlalchemy import create_engine
from src.pipeline import NL2SQLPipeline

# Configure logging for the application
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')

def main():
    # 1. Provide read-only connection limits (Replace with actual connection string)
    try:
        # Example using an in-memory SQLite database for demonstration
        engine = create_engine("sqlite:///:memory:")
        
        # Prefer deterministic, highly logical LLMs
        # Make sure OPENAI_API_KEY is set in your environment
        llm = ChatOpenAI(temperature=0, model="gpt-4")
        
        # Initialize Orchestrator
        pipeline = NL2SQLPipeline(engine=engine, llm=llm, max_retries=2)
        
        # Trigger
        question = "Show me the top 5 customers by revenue strictly descending."
        final_sql, resulting_df = pipeline.run(question)
        
        if resulting_df is not None:
            print("\n--- Final SQL Query ---")
            print(final_sql)
            print("\n--- Resulting DataFrame ---")
            print(resulting_df.head())
        else:
            print("\nPipeline failed to generate a valid result.")
            
    except Exception as e:
        logging.error(f"Application error: {e}")

if __name__ == "__main__":
    main()
