import json
import logging
import xml.etree.ElementTree as ET
from typing import Dict, NamedTuple, Optional
import re

import numpy as np
import pandas as pd
import sqlparse
from sqlalchemy.exc import SQLAlchemyError
import pymysql

from dbgpt._private.config import Config
from dbgpt.core.interface.output_parser import BaseOutputParser
from dbgpt.util.json_utils import serialize

from ...exceptions import AppActionException
from .sql_fixer import create_sql_fixer

CFG = Config()


class SqlAction(NamedTuple):
    sql: str
    thoughts: Dict
    display: str
    direct_response: str
    missing_info: str = ""
    analysis_report: Dict = {}

    def to_dict(self) -> Dict[str, Dict]:
        return {
            "sql": self.sql,
            "thoughts": self.thoughts,
            "display": self.display,
            "direct_response": self.direct_response,
            "missing_info": self.missing_info,
            "analysis_report": self.analysis_report,
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
        self.sql_fixer = create_sql_fixer()

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
        logger.info(f"=== DEBUG: parse_prompt_response ===")
        logger.info(f"Original model_out_text: {model_out_text}")
        logger.info(f"Clean prompt response: {clean_str}")
        logger.info(f"=== END DEBUG ===")
        
        # Compatible with community pure sql output model
        if self.is_sql_statement(clean_str):
            logger.info("Detected pure SQL statement")
            return SqlAction(clean_str, "", "", "", "", {})
        else:
            try:
                response = json.loads(clean_str, strict=False)
                logger.info(f"Successfully parsed JSON response: {response}")
                sql = ""
                thoughts = dict
                display = ""
                resp = ""
                missing_info = ""
                analysis_report = {}
                for key in sorted(response):
                    if key.strip() == "sql":
                        sql = response[key]
                    if key.strip() == "thoughts":
                        thoughts = response[key]
                    if key.strip() == "display_type":
                        display = response[key]
                    if key.strip() == "direct_response":
                        resp = response[key]
                    if key.strip() == "missing_info":
                        missing_info = response[key]
                    if key.strip() == "analysis_report":
                        analysis_report = response[key] if isinstance(response[key], dict) else {}
                return SqlAction(
                    sql=sql, thoughts=thoughts, display=display, direct_response=resp, 
                    missing_info=missing_info, analysis_report=analysis_report
                )
            except Exception as e:
                logger.error(f"json load failed: {clean_str}, error: {e}")
                return SqlAction("", clean_str, "", "", "", {})

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

    def format_sql_error_for_user(self, error: Exception, sql: str = None) -> str:
        """
        Format SQL error for user-friendly display
        将SQL错误格式化为用户友好的信息
        """
        error_msg = str(error)
        
        # Common SQL error patterns and their user-friendly explanations
        error_patterns = {
            r"Unknown column '([^']+)' in 'field list'": "字段 '{0}' 不存在，请检查字段名是否正确",
            r"Table '([^']+)' doesn't exist": "表 '{0}' 不存在，请检查表名是否正确", 
            r"You have an error in your SQL syntax": "SQL语法错误，请检查查询语句",
            r"Duplicate column name '([^']+)'": "重复的字段名 '{0}'",
            r"Unknown table '([^']+)'": "未知的表 '{0}'",
            r"Column '([^']+)' in field list is ambiguous": "字段 '{0}' 存在歧义，需要指定表名",
        }
        
        # Try to match common patterns
        for pattern, template in error_patterns.items():
            match = re.search(pattern, error_msg)
            if match:
                try:
                    return template.format(*match.groups())
                except:
                    return template
        
        # If no pattern matches, return a generic but informative message
        if "1054" in error_msg:
            return f"字段引用错误: {error_msg}"
        elif "1146" in error_msg:
            return f"表不存在错误: {error_msg}"
        elif "1064" in error_msg:
            return f"SQL语法错误: {error_msg}"
        else:
            return f"数据库查询错误: {error_msg}"

    def validate_sql_basic(self, sql: str) -> tuple[bool, str]:
        """
        Basic SQL validation
        基本的SQL验证
        """
        if not sql or not sql.strip():
            return False, "SQL查询为空"
        
        sql_upper = sql.upper().strip()
        
        # Check for dangerous operations (basic security)
        dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT', 'UPDATE']
        for keyword in dangerous_keywords:
            if keyword in sql_upper and not sql_upper.startswith('SELECT'):
                return False, f"不允许执行 {keyword} 操作"
        
        # Check for basic SQL structure
        if not sql_upper.startswith('SELECT') and not sql_upper.startswith('WITH'):
            return False, "只支持 SELECT 查询"
        
        return True, ""

    def parse_view_response(self, speak, data, prompt_response=None):
        """
        Parse view response with enhanced error handling and SQL fixing
        解析视图响应，增强错误处理和SQL修复
        
        Args:
            speak: AI response text
            data: Query result data or callable
            prompt_response: Parsed prompt response (optional)
        """
        logger.info(f"DEBUG parse_view_response called with speak: {speak}")
        logger.info(f"DEBUG parse_view_response called with data type: {type(data)}")
        logger.info(f"DEBUG parse_view_response called with prompt_response type: {type(prompt_response)}")
        
        if hasattr(prompt_response, 'direct_response'):
            logger.info(f"DEBUG prompt_response.direct_response: {prompt_response.direct_response}")
        if hasattr(prompt_response, 'sql'):
            logger.info(f"DEBUG prompt_response.sql: {prompt_response.sql}")
        
        try:
            # Check if we have analysis report - if so, we should execute SQL and format the full report
            has_analysis_report = (hasattr(prompt_response, 'analysis_report') and 
                                 prompt_response.analysis_report and 
                                 isinstance(prompt_response.analysis_report, dict) and
                                 any(prompt_response.analysis_report.values()))
            
            # Only return direct_response if there's no SQL and no analysis report
            if (hasattr(prompt_response, 'direct_response') and prompt_response.direct_response and
                not has_analysis_report and 
                (not hasattr(prompt_response, 'sql') or not prompt_response.sql)):
                return prompt_response.direct_response
            
            if not hasattr(prompt_response, 'sql') or not prompt_response.sql:
                # If we have analysis report but no SQL, format the report without data
                if has_analysis_report:
                    return self._format_analysis_report_only(prompt_response.analysis_report)
                
                error_msg = "AI模型未生成SQL查询，请尝试重新描述您的需求"
                logger.error(f"parse_view_response error: {error_msg}")
                return f"❌ 查询失败: {error_msg}"
            
            original_sql = prompt_response.sql.strip()
            logger.info(f"DEBUG Original SQL: {original_sql}")
            
            # Apply SQL fixes
            fixed_sql, fixes_applied = self.sql_fixer.fix_sql(original_sql)
            
            if fixes_applied:
                logger.info(f"Applied SQL fixes: {fixes_applied}")
                sql_to_execute = fixed_sql
                fix_info = f"\n🔧 自动修复: {', '.join(fixes_applied)}"
            else:
                sql_to_execute = original_sql
                fix_info = ""
            
            logger.info(f"DEBUG SQL to execute: {sql_to_execute}")
            
            # Basic SQL validation
            is_valid, validation_error = self.validate_sql_basic(sql_to_execute)
            if not is_valid:
                error_msg = f"SQL验证失败: {validation_error}"
                logger.error(f"SQL validation failed: {error_msg}")
                return f"❌ 查询失败: {error_msg}"
            
            # Execute SQL with enhanced error handling
            try:
                result = data(sql_to_execute)
                
                if result is None or result.empty:
                    # Even with empty results, show analysis report if available
                    if has_analysis_report:
                        empty_result_msg = "📊 查询执行成功，但没有找到匹配的数据。请尝试调整查询条件。\n\n"
                        analysis_report_content = self._format_analysis_report_only(prompt_response.analysis_report)
                        return empty_result_msg + analysis_report_content + fix_info
                    else:
                        return f"📊 查询执行成功，但没有找到匹配的数据。请尝试调整查询条件。{fix_info}"
                
                # Format result for display
                view_content = self._format_result_for_display(result, prompt_response)
                return view_content + fix_info
                
            except (SQLAlchemyError, pymysql.Error, Exception) as sql_error:
                # If fixed SQL still fails, try the original SQL
                if fixes_applied:
                    logger.info("Fixed SQL failed, trying original SQL...")
                    try:
                        result = data(original_sql)
                        if result is not None and not result.empty:
                            view_content = self._format_result_for_display(result, prompt_response)
                            return view_content + "\n⚠️ 注意: 使用了原始SQL查询（自动修复失败）"
                    except Exception:
                        pass  # Continue with error handling below
                
                # Enhanced SQL error handling
                user_friendly_error = self.format_sql_error_for_user(sql_error, sql_to_execute)
                technical_error = str(sql_error)
                
                logger.error(f"SQL execution failed: {technical_error}")
                logger.error(f"SQL that failed: {sql_to_execute}")
                
                # Return detailed error information
                error_response = f"""❌ 数据库查询失败

🔍 错误原因: {user_friendly_error}

📝 执行的SQL:
```sql
{sql_to_execute}
```

🔧 技术详情: {technical_error}

💡 建议: 请尝试简化查询或检查字段名是否正确"""

                if fixes_applied:
                    error_response += f"\n\n🔧 已尝试的修复: {', '.join(fixes_applied)}"
                
                return error_response
                
        except Exception as e:
            # Catch-all for any other errors
            logger.error(f"Unexpected error in parse_view_response: {str(e)}")
            return f"❌ 系统错误: {str(e)}"

    def _format_result_for_display(self, result, prompt_response):
        """
        Format query result for display with analysis report
        格式化查询结果用于显示，包含分析报告
        """
        try:
            # Convert DataFrame to a user-friendly format
            if len(result) == 0:
                return "📊 查询执行成功，但没有找到匹配的数据。"
            
            # Create a formatted table
            formatted_result = "📊 查询结果:\n\n"
            formatted_result += result.to_string(index=False, max_rows=50)
            
            if len(result) > 50:
                formatted_result += f"\n\n... 显示前50条记录，共{len(result)}条记录"
            
            # Add analysis report if available
            if hasattr(prompt_response, 'analysis_report') and prompt_response.analysis_report:
                report = prompt_response.analysis_report
                formatted_result += "\n\n" + "="*60 + "\n"
                formatted_result += "📋 **分析报告**\n"
                formatted_result += "="*60 + "\n\n"
                
                if report.get('summary'):
                    formatted_result += f"**📝 分析摘要:**\n{report['summary']}\n\n"
                
                if report.get('key_findings') and isinstance(report['key_findings'], list):
                    formatted_result += "**🔍 关键发现:**\n"
                    for i, finding in enumerate(report['key_findings'], 1):
                        formatted_result += f"{i}. {finding}\n"
                    formatted_result += "\n"
                
                if report.get('insights') and isinstance(report['insights'], list):
                    formatted_result += "**💡 业务洞察:**\n"
                    for i, insight in enumerate(report['insights'], 1):
                        formatted_result += f"{i}. {insight}\n"
                    formatted_result += "\n"
                
                if report.get('recommendations') and isinstance(report['recommendations'], list):
                    formatted_result += "**🎯 建议措施:**\n"
                    for i, rec in enumerate(report['recommendations'], 1):
                        formatted_result += f"{i}. {rec}\n"
                    formatted_result += "\n"
                
                if report.get('methodology'):
                    formatted_result += f"**🔬 分析方法:**\n{report['methodology']}\n\n"
            
            return formatted_result
            
        except Exception as e:
            logger.error(f"Error formatting result: {str(e)}")
            return f"✅ 查询执行成功，但结果格式化失败: {str(e)}"

    def _format_analysis_report_only(self, analysis_report):
        """
        Format analysis report without query data
        仅格式化分析报告（无查询数据）
        """
        try:
            formatted_result = "📋 **分析报告**\n"
            formatted_result += "="*60 + "\n\n"
            
            if analysis_report.get('summary'):
                formatted_result += f"**📝 分析摘要:**\n{analysis_report['summary']}\n\n"
            
            if analysis_report.get('key_findings') and isinstance(analysis_report['key_findings'], list):
                formatted_result += "**🔍 关键发现:**\n"
                for i, finding in enumerate(analysis_report['key_findings'], 1):
                    formatted_result += f"{i}. {finding}\n"
                formatted_result += "\n"
            
            if analysis_report.get('insights') and isinstance(analysis_report['insights'], list):
                formatted_result += "**💡 业务洞察:**\n"
                for i, insight in enumerate(analysis_report['insights'], 1):
                    formatted_result += f"{i}. {insight}\n"
                formatted_result += "\n"
            
            if analysis_report.get('recommendations') and isinstance(analysis_report['recommendations'], list):
                formatted_result += "**🎯 建议措施:**\n"
                for i, rec in enumerate(analysis_report['recommendations'], 1):
                    formatted_result += f"{i}. {rec}\n"
                formatted_result += "\n"
            
            if analysis_report.get('methodology'):
                formatted_result += f"**🔬 分析方法:**\n{analysis_report['methodology']}\n\n"
            
            return formatted_result
            
        except Exception as e:
            logger.error(f"Error formatting analysis report: {str(e)}")
            return f"📋 分析报告格式化失败: {str(e)}"
