import logging
from typing import Optional, Tuple
import pandas as pd
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from langchain_core.language_models.chat_models import BaseChatModel

from .schema_extractor import SchemaExtractor
from .sql_generator import LLMSQLGenerator
from .sql_validator import SQLValidator

logger = logging.getLogger(__name__)

class NL2SQLPipeline:
    """
    Orchestrates the securely robust NL2SQL extraction, generation, and self-correction pipeline.
    """
    def __init__(self, engine: Engine, llm: BaseChatModel, max_retries: int = 2):
        self.engine = engine
        self.schema_extractor = SchemaExtractor(engine)
        self.sql_generator = LLMSQLGenerator(llm)
        self.max_retries = max_retries

    def run(self, question: str) -> Tuple[str, Optional[pd.DataFrame]]:
        """
        Executes the NL2SQL pipeline from natural language to DataFrame.
        Returns the final executed SQL query (for auditing) and the resulting pandas DataFrame.
        """
        logger.info(f"Processing question: '{question}'")
        schema = self.schema_extractor.get_database_schema()
        sql_query = self.sql_generator.generate(schema, question)
        
        retries = 0
        while retries <= self.max_retries:
            logger.info(f"Attempt {retries + 1}/{self.max_retries + 1} - Validating and Executing SQL...")
            
            try:
                # 1. Validate Security Constraints programmatically
                SQLValidator.validate_read_only(sql_query)
                
                # 2. Execute directly into a Pandas DataFrame
                # DEFENSE IN DEPTH: The DBA should still strictly ensure the `self.engine` user 
                # credential explicitly lacks DML/DDL permissions (GRANT SELECT ONLY).
                df = pd.read_sql(sql_query, self.engine)
                logger.info("Query successfully executed and data fetched into DataFrame.")
                
                return sql_query, df
                
            except ValueError as ve:
                # Security validation failed (e.g., DROP statement detected)
                logger.error(f"Validation Error: {ve}")
                break  # Security violations immediately abort; no LLM retry needed.

            except SQLAlchemyError as db_err:
                # Triggers on syntax errors, missing tables/columns, invalid logic, etc.
                error_msg = str(db_err)
                logger.warning(f"Database Execution Error: {error_msg}")
                
                if retries < self.max_retries:
                    logger.info("Initiating LLM Self-Correction Loop...")
                    sql_query = self.sql_generator.fix_query(schema, question, sql_query, error_msg)
                else:
                    logger.error("Max retries exhausted. Returning the failed query context.")
                    
            retries += 1
            
        return sql_query, None
