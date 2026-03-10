import logging
from typing import Optional, List
from sqlalchemy import inspect
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

class SchemaExtractor:
    """
    Extracts Database Schema (DDL) and Table Definitions to be used as context for the LLM.
    Strictly queries metadata dictionaries. NEVER retrieves row-level data.
    """
    def __init__(self, engine: Engine):
        self.engine = engine
        self.inspector = inspect(self.engine)

    def get_database_schema(self, include_tables: Optional[List[str]] = None) -> str:
        """
        Retrieves the DDL-like schema representation for all tables or a targeted subset.
        """
        schema_definition = []
        tables = include_tables if include_tables else self.inspector.get_table_names()
        
        logger.info(f"Extracting schema for {len(tables)} tables...")
        
        for table in tables:
            try:
                columns = self.inspector.get_columns(table)
                pk_constraint = self.inspector.get_pk_constraint(table)
                fk_constraints = self.inspector.get_foreign_keys(table)
                
                # Base column definitions
                col_defs = [f"{col['name']} {col['type']}" for col in columns]
                
                # Append primary keys if available
                if pk_constraint and pk_constraint.get('constrained_columns'):
                    pks = ", ".join(pk_constraint['constrained_columns'])
                    col_defs.append(f"PRIMARY KEY ({pks})")
                
                # Append foreign keys if available
                for fk in fk_constraints:
                    fk_cols = ", ".join(fk['constrained_columns'])
                    ref_cols = ", ".join(fk['referred_columns'])
                    ref_table = fk['referred_table']
                    col_defs.append(f"FOREIGN KEY ({fk_cols}) REFERENCES {ref_table}({ref_cols})")
                
                # Format into a standardized pseudo-DDL string
                table_schema = f"TABLE {table} (\n    " + ",\n    ".join(col_defs) + "\n);"
                schema_definition.append(table_schema)
                
            except Exception as e:
                logger.error(f"Failed to extract schema for table '{table}': {e}")
                
        return "\n\n".join(schema_definition)
