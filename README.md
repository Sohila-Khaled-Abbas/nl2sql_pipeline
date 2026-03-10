# Natural Language to SQL (NL2SQL) Pipeline

A production-ready, secure Natural Language to SQL (NL2SQL) pipeline using Python, LangChain, and SQLAlchemy.

## Features Let
- **Security First:** The system never sends row data to the LLM. It extracts only database schemas.
- **Read-Only Enforcement:** Uses strict logic to reject modifications to the database before they even get to the execution engine.
- **Self-Correction:** Validates generated queries and catches SQL errors. If one occurs, the framework uses the LLM to auto-correct the query.
- **Auditing:** Returns both the executed query and the Pandas DataFrame.

## Project Structure
```tree
nl2sql_pipeline/
├── src/
│   ├── __init__.py           
│   ├── schema_extractor.py   # Extracts safely the schema 
│   ├── sql_validator.py      # Hardcoded security validator
│   ├── sql_generator.py      # Interfaces with the LLM and manages prompts
│   └── pipeline.py           # Orchestrates the whole flow
├── requirements.txt
└── main.py                   # Example usage
```

## Setup

1. Make sure you install the dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure your `OPENAI_API_KEY` environment variable is available if you map to the OpenAI models.
```bash
export OPENAI_API_KEY="your-api-key"
```

3. Run the pipeline:
```bash
python main.py
```
