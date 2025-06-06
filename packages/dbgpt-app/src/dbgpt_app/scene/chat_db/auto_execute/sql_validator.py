"""SQL Validator for DB-GPT Auto Execute."""

import logging
import re
from typing import Dict, List, Set

import sqlparse
from sqlparse.sql import IdentifierList, Token
from sqlparse.tokens import Keyword, Name

from dbgpt.datasource.base import BaseConnector

logger = logging.getLogger(__name__)


class SQLValidator:
    """Validates SQL queries against database schema."""

    def __init__(self, connector: BaseConnector):
        """Initialize the SQL validator.
        
        Args:
            connector: Database connector instance
        """
        self.connector = connector
        self._table_columns_cache: Dict[str, Set[str]] = {}

    def _get_table_columns(self, table_name: str) -> Set[str]:
        """Get all column names for a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Set of column names
        """
        if table_name not in self._table_columns_cache:
            try:
                columns = self.connector.get_columns(table_name)
                self._table_columns_cache[table_name] = {
                    col["name"].lower() for col in columns
                }
            except Exception as e:
                logger.warning(f"Failed to get columns for table {table_name}: {e}")
                # Fallback to simple fields
                try:
                    fields = self.connector.get_simple_fields(table_name)
                    self._table_columns_cache[table_name] = {
                        field[0].lower() for field in fields
                    }
                except Exception as e2:
                    logger.error(f"Failed to get simple fields for table {table_name}: {e2}")
                    self._table_columns_cache[table_name] = set()
        
        return self._table_columns_cache[table_name]

    def _extract_table_aliases(self, sql: str) -> Dict[str, str]:
        """Extract table aliases from SQL.
        
        Args:
            sql: SQL query string
            
        Returns:
            Dictionary mapping alias to table name
        """
        aliases = {}
        parsed = sqlparse.parse(sql)[0]
        
        # Look for FROM and JOIN clauses
        from_seen = False
        for token in parsed.flatten():
            if token.ttype is Keyword and token.value.upper() in ('FROM', 'JOIN'):
                from_seen = True
                continue
            
            if from_seen and token.ttype is Name:
                # This could be a table name or alias
                # Simple heuristic: if it's followed by another name, it's table alias
                continue
                
        # More robust parsing using regex
        # Pattern to match: table_name alias or table_name AS alias
        pattern = r'\b(?:FROM|JOIN)\s+(\w+)(?:\s+(?:AS\s+)?(\w+))?\b'
        matches = re.findall(pattern, sql, re.IGNORECASE)
        
        for match in matches:
            table_name, alias = match
            if alias:
                aliases[alias.lower()] = table_name.lower()
            else:
                aliases[table_name.lower()] = table_name.lower()
                
        return aliases

    def _extract_column_references(self, sql: str) -> List[tuple]:
        """Extract column references from SQL.
        
        Args:
            sql: SQL query string
            
        Returns:
            List of (table_alias, column_name) tuples
        """
        column_refs = []
        
        # Pattern to match: alias.column_name or table.column_name
        pattern = r'\b(\w+)\.(\w+)\b'
        matches = re.findall(pattern, sql, re.IGNORECASE)
        
        for table_ref, column_name in matches:
            column_refs.append((table_ref.lower(), column_name.lower()))
            
        return column_refs

    def validate_sql(self, sql: str) -> tuple[bool, List[str]]:
        """Validate SQL query against database schema.
        
        Args:
            sql: SQL query to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            # Extract table aliases
            aliases = self._extract_table_aliases(sql)
            logger.info(f"Extracted aliases: {aliases}")
            
            # Extract column references
            column_refs = self._extract_column_references(sql)
            logger.info(f"Extracted column references: {column_refs}")
            
            # Validate each column reference
            for table_ref, column_name in column_refs:
                # Resolve table name from alias
                table_name = aliases.get(table_ref, table_ref)
                
                # Get table columns
                table_columns = self._get_table_columns(table_name)
                
                if not table_columns:
                    errors.append(f"Table '{table_name}' not found or has no accessible columns")
                    continue
                    
                if column_name not in table_columns:
                    errors.append(
                        f"Column '{column_name}' does not exist in table '{table_name}'. "
                        f"Available columns: {', '.join(sorted(table_columns))}"
                    )
            
            return len(errors) == 0, errors
            
        except Exception as e:
            logger.error(f"Error validating SQL: {e}")
            errors.append(f"SQL validation error: {str(e)}")
            return False, errors

    def suggest_corrections(self, sql: str, errors: List[str]) -> str:
        """Suggest corrections for SQL errors.
        
        Args:
            sql: Original SQL query
            errors: List of validation errors
            
        Returns:
            Suggested corrections as a string
        """
        suggestions = []
        
        for error in errors:
            if "does not exist in table" in error:
                # Extract table and column info from error
                match = re.search(r"Column '(\w+)' does not exist in table '(\w+)'", error)
                if match:
                    missing_column, table_name = match.groups()
                    table_columns = self._get_table_columns(table_name)
                    
                    # Find similar column names
                    similar_columns = [
                        col for col in table_columns 
                        if missing_column.lower() in col.lower() or col.lower() in missing_column.lower()
                    ]
                    
                    if similar_columns:
                        suggestions.append(
                            f"For missing column '{missing_column}' in table '{table_name}', "
                            f"consider using: {', '.join(similar_columns)}"
                        )
                    else:
                        suggestions.append(
                            f"Table '{table_name}' available columns: {', '.join(sorted(table_columns))}"
                        )
        
        return "\n".join(suggestions) if suggestions else "No specific suggestions available." 