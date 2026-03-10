import logging
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.language_models.chat_models import BaseChatModel

logger = logging.getLogger(__name__)

class SQLOutput(BaseModel):
    """Pydantic schema to strictly enforce structured output from the LLM."""
    query: str = Field(description="A valid, executable, read-only SQL SELECT query. No conversational text or markdown formatting outside of the JSON payload.")

class LLMSQLGenerator:
    """
    Interfaces with the LLM via LangChain to generate initial SQL schemas and run correction cycles.
    """
    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        self.output_parser = PydanticOutputParser(pydantic_object=SQLOutput)
        
        self.base_prompt = PromptTemplate(
            template=(
                "You are an expert SQL engineer. Generate a strictly valid, read-only SQL query "
                "to answer the user's question based strictly on the provided schema.\n\n"
                "[DATABASE SCHEMA]\n{schema}\n\n"
                "[USER QUESTION]\n{question}\n\n"
                "[INSTRUCTIONS]\n{format_instructions}"
            ),
            input_variables=["schema", "question"],
            partial_variables={"format_instructions": self.output_parser.get_format_instructions()}
        )
        
        self.correction_prompt = PromptTemplate(
            template=(
                "You are an expert SQL engineer. The previous SQL query you generated resulted in an database error.\n\n"
                "[DATABASE SCHEMA]\n{schema}\n\n"
                "[USER QUESTION]\n{question}\n\n"
                "[FAILED SQL QUERY]\n{failed_query}\n\n"
                "[DATABASE ERROR MESSAGE]\n{error_message}\n\n"
                "Review the error, correct the syntax, and provide the fixed valid read-only SQL query.\n\n"
                "[INSTRUCTIONS]\n{format_instructions}"
            ),
            input_variables=["schema", "question", "failed_query", "error_message"],
            partial_variables={"format_instructions": self.output_parser.get_format_instructions()}
        )

    def generate(self, schema: str, question: str) -> str:
        logger.info("Requesting LLM to generate initial SQL...")
        chain = self.base_prompt | self.llm | self.output_parser
        return chain.invoke({"schema": schema, "question": question}).query

    def fix_query(self, schema: str, question: str, failed_query: str, error_message: str) -> str:
        logger.info("Requesting LLM to correct failed SQL...")
        chain = self.correction_prompt | self.llm | self.output_parser
        return chain.invoke({
            "schema": schema, 
            "question": question, 
            "failed_query": failed_query, 
            "error_message": error_message
        }).query
