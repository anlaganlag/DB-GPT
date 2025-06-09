import json
import logging
import xml.etree.ElementTree as ET
from typing import Dict, NamedTuple, Optional

import numpy as np
import pandas as pd
import sqlparse

from dbgpt._private.config import Config
from dbgpt.core.interface.output_parser import BaseOutputParser
from dbgpt.util.json_utils import serialize

from ...exceptions import AppActionException

CFG = Config()


class SqlAction(NamedTuple):
    sql: str
    thoughts: Dict
    display: str
    direct_response: str

    def to_dict(self) -> Dict[str, Dict]:
        return {
            "sql": self.sql,
            "thoughts": self.thoughts,
            "display": self.display,
            "direct_response": self.direct_response,
        }


logger = logging.getLogger(__name__)


class DbChatOutputParser(BaseOutputParser):
    def __init__(self, is_stream_out: bool = False, connector=None, **kwargs):
        super().__init__(is_stream_out=is_stream_out, **kwargs)
        self._sql_validator = None
        self._connector = connector
        
        # Auto-initialize SQL validator if connector is provided
        if connector:
            self._initialize_sql_validator()

    def _initialize_sql_validator(self):
        """Initialize SQL validator with the provided connector."""
        try:
            from .sql_validator import SQLValidator
            self._sql_validator = SQLValidator(self._connector)
            logger.info("SQL validator initialized successfully")
        except ImportError as e:
            logger.warning(f"Could not import SQL validator: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize SQL validator: {e}")

    def set_sql_validator(self, validator):
        """Set the SQL validator instance."""
        self._sql_validator = validator

    def set_connector(self, connector):
        """Set the database connector and initialize SQL validator."""
        self._connector = connector
        if connector and not self._sql_validator:
            self._initialize_sql_validator()

    def is_sql_statement(self, statement):
        parsed = sqlparse.parse(statement)
        if not parsed:
            return False
        for stmt in parsed:
            if stmt.get_type() != "UNKNOWN":
                return True
        return False

    def parse_prompt_response(self, model_out_text):
        clean_str = super().parse_prompt_response(model_out_text)
        logger.info(f"clean prompt response: {clean_str}")
        # Compatible with community pure sql output model
        if self.is_sql_statement(clean_str):
            return SqlAction(clean_str, "", "", "")
        else:
            try:
                response = json.loads(clean_str, strict=False)
                sql = ""
                thoughts = dict
                display = ""
                resp = ""
                for key in sorted(response):
                    if key.strip() == "sql":
                        sql = response[key]
                    if key.strip() == "thoughts":
                        thoughts = response[key]
                    if key.strip() == "display_type":
                        display = response[key]
                    if key.strip() == "direct_response":
                        resp = response[key]
                return SqlAction(
                    sql=sql, thoughts=thoughts, display=display, direct_response=resp
                )
            except Exception as e:
                logger.error(f"json load failed: {clean_str}, error: {e}")
                return SqlAction("", clean_str, "", "")

    def _safe_parse_vector_data_with_pca(self, df):
        """Enhanced PCA parsing with better error handling."""
        try:
            from sklearn.decomposition import PCA
        except ImportError:
            logger.error("scikit-learn not available for PCA processing")
            raise ImportError(
                "Could not import scikit-learn package. "
                "Please install it with `pip install scikit-learn`."
            )

        try:
            nrow, ncol = df.shape
            if nrow == 0 or ncol == 0:
                logger.warning("Empty DataFrame provided for PCA processing")
                return df, False

            vec_col = -1
            for i_col in range(ncol):
                try:
                    first_val = df.iloc[0, i_col]
                    if isinstance(first_val, list):
                        vec_col = i_col
                        break
                    elif isinstance(first_val, bytes):
                        try:
                            decoded_val = json.loads(first_val.decode())
                            if isinstance(decoded_val, list):
                                vec_col = i_col
                                break
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            continue
                    elif isinstance(first_val, str):
                        try:
                            parsed_val = json.loads(first_val)
                            if isinstance(parsed_val, list):
                                vec_col = i_col
                                break
                        except json.JSONDecodeError:
                            continue
                except (IndexError, TypeError):
                    continue
                    
            if vec_col == -1:
                logger.info("No vector column found for PCA processing")
                return df, False
                
            # Validate vector data
            try:
                first_vec = df.iloc[0, vec_col]
                if isinstance(first_vec, bytes):
                    first_vec = json.loads(first_vec.decode())
                elif isinstance(first_vec, str):
                    first_vec = json.loads(first_vec)
                    
                vec_dim = len(first_vec)
                if min(nrow, vec_dim) < 2:
                    logger.warning(f"Insufficient data for PCA: rows={nrow}, dimensions={vec_dim}")
                    return df, False
                    
            except Exception as e:
                logger.error(f"Error validating vector data: {e}")
                return df, False

            # Process vector data
            try:
                if isinstance(df.iloc[0, vec_col], bytes):
                    df.iloc[:, vec_col] = df.iloc[:, vec_col].apply(
                        lambda x: json.loads(x.decode()) if isinstance(x, bytes) else x
                    )
                elif isinstance(df.iloc[0, vec_col], str):
                    df.iloc[:, vec_col] = df.iloc[:, vec_col].apply(
                        lambda x: json.loads(x) if isinstance(x, str) else x
                    )
                    
                X = np.array(df.iloc[:, vec_col].tolist())
                
                # Validate array shape
                if X.ndim != 2:
                    logger.error(f"Invalid vector array shape: {X.shape}")
                    return df, False
                    
                pca = PCA(n_components=2)
                X_pca = pca.fit_transform(X)

                new_df = pd.DataFrame()
                for i_col in range(ncol):
                    if i_col == vec_col:
                        continue
                    col_name = df.columns[i_col]
                    new_df[col_name] = df[col_name]
                new_df["__x"] = [pos[0] for pos in X_pca]
                new_df["__y"] = [pos[1] for pos in X_pca]
                
                logger.info(f"PCA processing successful: {nrow} rows, {vec_dim} dimensions -> 2D")
                return new_df, True
                
            except Exception as e:
                logger.error(f"Error during PCA transformation: {e}")
                return df, False
                
        except Exception as e:
            logger.error(f"Unexpected error in PCA processing: {e}")
            return df, False

    def parse_vector_data_with_pca(self, df):
        """Wrapper for backward compatibility."""
        return self._safe_parse_vector_data_with_pca(df)

    def _create_detailed_error_message(self, error: Exception, sql: str = "", context: str = "") -> str:
        """Create a detailed, user-friendly error message."""
        error_type = type(error).__name__
        error_msg = str(error)
        
        # Categorize common errors
        if "Unknown column" in error_msg or "doesn't exist" in error_msg:
            error_category = "Column Reference Error"
            icon = "🔍"
        elif "syntax error" in error_msg.lower() or "SQL syntax" in error_msg:
            error_category = "SQL Syntax Error"
            icon = "⚠️"
        elif "connection" in error_msg.lower() or "connect" in error_msg.lower():
            error_category = "Database Connection Error"
            icon = "🔌"
        elif "permission" in error_msg.lower() or "access" in error_msg.lower():
            error_category = "Permission Error"
            icon = "🔒"
        elif "timeout" in error_msg.lower():
            error_category = "Timeout Error"
            icon = "⏱️"
        else:
            error_category = "General Error"
            icon = "❌"
            
        detailed_msg = f"""
<div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 10px 0;">
    <h4 style="color: #856404; margin: 0 0 10px 0;">{icon} {error_category}</h4>
    <p style="margin: 5px 0;"><strong>Error:</strong> {error_msg}</p>
    {f'<p style="margin: 5px 0;"><strong>SQL:</strong> <code>{sql}</code></p>' if sql else ''}
    {f'<p style="margin: 5px 0;"><strong>Context:</strong> {context}</p>' if context else ''}
    
    <div style="margin-top: 10px; padding: 10px; background-color: #e8f4f8; border-radius: 3px;">
        <strong>💡 Quick Fixes:</strong>
        <ul style="margin: 5px 0; padding-left: 20px;">
            <li>Check your database schema and column names</li>
            <li>Verify your database connection is working</li>
            <li>Run the diagnostic tool: <code>python debug_view_content_error.py</code></li>
            <li>Check the logs for more detailed information</li>
        </ul>
    </div>
</div>
        """.strip()
        
        return detailed_msg

    def parse_view_response(self, speak, data, prompt_response) -> str:
        param = {}
        api_call_element = ET.Element("chart-view")
        err_msg = None
        success = False
        detailed_error_info = {}
        
        try:
            if (
                not prompt_response.direct_response
                or len(prompt_response.direct_response) <= 0
            ) and (not prompt_response.sql or len(prompt_response.sql) <= 0):
                raise AppActionException("Can not find sql in response", speak)

            if prompt_response.sql:
                logger.info(f"Processing SQL: {prompt_response.sql}")
                
                # Enhanced SQL validation
                if self._sql_validator:
                    try:
                        is_valid, validation_errors = self._sql_validator.validate_sql(prompt_response.sql)
                        if not is_valid:
                            error_msg = "SQL validation failed:\n" + "\n".join(validation_errors)
                            suggestions = self._sql_validator.suggest_corrections(prompt_response.sql, validation_errors)
                            if suggestions:
                                error_msg += f"\n\nSuggestions:\n{suggestions}"
                            
                            logger.error(f"SQL validation failed: {error_msg}")
                            detailed_error = self._create_detailed_error_message(
                                Exception(error_msg), 
                                prompt_response.sql, 
                                "SQL Validation"
                            )
                            raise AppActionException(
                                "Generated SQL contains invalid column references", 
                                detailed_error
                            )
                    except Exception as validation_error:
                        logger.warning(f"SQL validation error (continuing anyway): {validation_error}")
                else:
                    logger.warning("SQL validator not available - skipping validation")
                
                # Execute SQL with enhanced error handling
                try:
                    df = data(prompt_response.sql)
                    logger.info(f"SQL executed successfully, got {len(df)} rows")
                except Exception as sql_error:
                    logger.error(f"SQL execution failed: {sql_error}")
                    detailed_error = self._create_detailed_error_message(
                        sql_error, 
                        prompt_response.sql, 
                        "SQL Execution"
                    )
                    raise AppActionException("SQL execution failed", detailed_error)
                
                param["type"] = prompt_response.display

                # Enhanced vector processing
                if param["type"] == "response_vector_chart":
                    try:
                        df, visualizable = self._safe_parse_vector_data_with_pca(df)
                        param["type"] = (
                            "response_scatter_chart" if visualizable else "response_table"
                        )
                        if visualizable:
                            logger.info("Vector data successfully processed with PCA")
                        else:
                            logger.info("Vector data processing failed, falling back to table view")
                    except Exception as pca_error:
                        logger.error(f"PCA processing failed: {pca_error}")
                        param["type"] = "response_table"

                param["sql"] = prompt_response.sql
                
                # Enhanced JSON conversion with better error handling
                try:
                    param["data"] = json.loads(
                        df.to_json(orient="records", date_format="iso", date_unit="s")
                    )
                    logger.info(f"Data conversion successful: {len(param['data'])} records")
                except Exception as json_error:
                    logger.error(f"JSON conversion failed: {json_error}")
                    # Try alternative conversion methods
                    try:
                        # Convert problematic columns to strings
                        df_clean = df.copy()
                        for col in df_clean.columns:
                            if df_clean[col].dtype == 'object':
                                df_clean[col] = df_clean[col].astype(str)
                        param["data"] = json.loads(
                            df_clean.to_json(orient="records", date_format="iso", date_unit="s")
                        )
                        logger.info("Data conversion successful with string conversion fallback")
                    except Exception as fallback_error:
                        logger.error(f"Fallback JSON conversion also failed: {fallback_error}")
                        detailed_error = self._create_detailed_error_message(
                            fallback_error, 
                            prompt_response.sql, 
                            "Data Conversion"
                        )
                        raise AppActionException("Data conversion failed", detailed_error)
                
                view_json_str = json.dumps(param, default=serialize, ensure_ascii=False)
                success = True
                
            elif prompt_response.direct_response:
                speak = prompt_response.direct_response
                view_json_str = ""
                success = True
                
        except AppActionException:
            # Re-raise AppActionException as-is
            raise
        except Exception as e:
            logger.error(f"parse_view_response error: {e}", exc_info=True)
            
            # Create detailed error information
            detailed_error_info = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "sql": getattr(prompt_response, 'sql', ''),
                "context": "View Response Parsing"
            }
            
            err_param = {
                "sql": f"{prompt_response.sql}",
                "type": "response_table",
                "data": [],
            }
            err_msg = self._create_detailed_error_message(
                e, 
                getattr(prompt_response, 'sql', ''), 
                "View Response Parsing"
            )
            view_json_str = json.dumps(err_param, default=serialize, ensure_ascii=False)

        # Generate final result
        if len(view_json_str) != 0:
            api_call_element.set("content", view_json_str)
            result = ET.tostring(api_call_element, encoding="utf-8")
        else:
            result = b""
            
        if not success:
            view_content = f'{speak}\n{err_msg}\n{result.decode("utf-8")}'
            raise AppActionException("Generate view content failed", view_content)
        else:
            return speak + "\n" + result.decode("utf-8")
