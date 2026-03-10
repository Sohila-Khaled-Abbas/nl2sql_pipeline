import logging
import re

logger = logging.getLogger(__name__)

class SQLValidator:
    """
    Enforces strict security constraints on generated SQL before execution.
    """
    FORBIDDEN_OPERATIONS = [
        r'\bDROP\b', r'\bDELETE\b', r'\bUPDATE\b', r'\bINSERT\b',
        r'\bALTER\b', r'\bTRUNCATE\b', r'\bGRANT\b', r'\bREVOKE\b',
        r'\bEXEC\b', r'\bEXECUTE\b', r'\bMERGE\b'
    ]

    @classmethod
    def validate_read_only(cls, sql: str) -> None:
        """
        Validates the SQL string. Raises a ValueError if the query fails security checks.
        """
        sql_upper = sql.upper()
        
        # 1. Reject any forbidden destructive operations
        for pattern in cls.FORBIDDEN_OPERATIONS:
            if re.search(pattern, sql_upper):
                logger.critical(f"SECURITY VIOLATION: Forbidden keyword detected matching '{pattern}'. Query blocked.")
                raise ValueError(f"Forbidden SQL operation detected: {pattern.replace(r'\\b', '')}")

        # 2. Must begin with SELECT or a CTE (WITH statement)
        if not re.search(r'^\s*(SELECT|WITH)\b', sql_upper):
            logger.critical("SECURITY VIOLATION: Query does not start with SELECT or WITH. Query blocked.")
            raise ValueError("Query must be an extraction (SELECT/WITH) statement.")
