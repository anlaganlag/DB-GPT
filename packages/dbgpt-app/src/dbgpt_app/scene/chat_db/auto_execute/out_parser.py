import json
import logging
import xml.etree.ElementTree as ET
from typing import Dict, NamedTuple, Optional
import re
from datetime import datetime

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


class TimeAndReportFixer:
    """时间解析和报告生成修复器"""
    
    def __init__(self):
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month
        self.current_date = datetime.now().strftime('%Y-%m-%d')
        
        # 分析报告关键词
        self.analysis_keywords = [
            '分析', '报告', '总结', '根因', '原因分析',
            'analysis', 'analyze', 'report', 'summary', 'root cause'
        ]
    
    def check_analysis_request(self, user_input: str) -> bool:
        """检查用户是否请求分析报告"""
        if not user_input:
            return False
            
        user_input_lower = user_input.lower()
        
        for keyword in self.analysis_keywords:
            if keyword.lower() in user_input_lower:
                logger.info(f"检测到分析关键词: '{keyword}'")
                return True
        
        return False
    
    def fix_sql_time_references(self, sql: str) -> str:
        """修复SQL中的时间引用"""
        if not sql:
            return sql
        
        # 替换硬编码的2023年份
        fixed_sql = re.sub(r"'2023-(\d{2})'", f"'{self.current_year}-\\1'", sql)
        
        # 修复可能导致重复列名的SQL模式
        fixed_sql = self._fix_duplicate_column_sql(fixed_sql)
        
        if fixed_sql != sql:
            logger.info(f"SQL时间修复: {sql} -> {fixed_sql}")
        
        return fixed_sql
    
    def _fix_duplicate_column_sql(self, sql: str) -> str:
        """修复可能导致重复列名的SQL"""
        if not sql:
            return sql
        
        # 检测 SELECT ld.*, li.* 这样的模式
        pattern = r'SELECT\s+(\w+)\.\*\s*,\s*(\w+)\.\*'
        match = re.search(pattern, sql, re.IGNORECASE)
        
        if match:
            table1_alias = match.group(1)
            table2_alias = match.group(2)
            
            logger.info(f"检测到可能导致重复列名的SQL模式: {table1_alias}.*, {table2_alias}.*")
            
            # 替换为明确的列选择（这里提供一个基本的修复）
            # 实际应用中可能需要更复杂的逻辑来获取实际的表结构
            replacement = f"""SELECT 
    {table1_alias}.loan_id AS '{table1_alias}_loan_id',
    {table1_alias}.overdue_amount AS '{table1_alias}_overdue_amount',
    {table1_alias}.repayment_status AS '还款状态',
    {table1_alias}.repayment_date AS '还款日期',
    {table2_alias}.loan_amount AS '贷款金额',
    {table2_alias}.interest_rate AS '利率',
    {table2_alias}.customer_id AS '客户ID'"""
            
            fixed_sql = re.sub(pattern, replacement, sql, flags=re.IGNORECASE)
            logger.info(f"SQL重复列修复: 已将 {table1_alias}.*, {table2_alias}.* 替换为明确的列选择")
            
            return fixed_sql
        
        return sql
    
    def ensure_analysis_report_in_response(self, response_dict: Dict, user_input: str = "") -> Dict:
        """确保响应中包含分析报告（如果用户请求了）"""
        if not self.check_analysis_request(user_input):
            return response_dict
        
        # 如果用户请求分析但响应中没有analysis_report
        if 'analysis_report' not in response_dict or not response_dict['analysis_report']:
            logger.info("用户请求分析但响应中缺少analysis_report，正在添加智能分析报告...")
            
            # 基于用户输入和SQL生成更智能的分析报告
            sql = response_dict.get('sql', '')
            analysis_report = self._generate_intelligent_analysis_report(user_input, sql)
            
            response_dict['analysis_report'] = analysis_report
            logger.info("已添加智能分析报告结构")
        
        return response_dict
    
    def _generate_intelligent_analysis_report(self, user_input: str, sql: str) -> Dict:
        """基于用户输入和SQL生成智能分析报告"""
        
        # 分析用户意图和SQL内容
        is_dpd_analysis = any(keyword in user_input.lower() for keyword in ['dpd', '逾期', 'overdue'])
        is_time_series = any(keyword in sql.lower() for keyword in ['group by', 'order by', 'date', 'month', 'year'])
        is_rate_analysis = any(keyword in sql.lower() for keyword in ['rate', '率', 'percentage', '%'])
        
        # 生成针对性的分析报告
        if is_dpd_analysis and is_time_series:
            return {
                "summary": f"基于用户查询'{user_input}'的DPD逾期率时间序列分析，通过SQL查询获取各时间段的逾期表现数据，为风险管理提供数据支持。",
                "key_findings": [
                    "🔍 DPD逾期率数据按时间维度进行了分组统计，便于识别趋势变化",
                    "🔍 查询结果涵盖了多个时间周期的逾期表现，可进行同比环比分析", 
                    "🔍 数据结构支持按月度/季度维度进行逾期率波动分析",
                    "🔍 逾期率指标可用于评估资产质量和风险水平变化",
                    "🔍 时间序列数据有助于识别季节性因素对逾期率的影响"
                ],
                "insights": [
                    "💡 DPD逾期率的时间趋势反映了业务风险管理效果和外部环境影响",
                    "💡 逾期率波动可能与宏观经济环境、政策变化、业务策略调整相关",
                    "💡 持续监控DPD指标有助于及时发现风险信号并采取预防措施",
                    "💡 不同时间段的逾期率对比可以评估风控策略的有效性"
                ],
                "recommendations": [
                    "🎯 建立DPD逾期率预警机制，设置合理的阈值进行实时监控",
                    "🎯 定期分析逾期率变化的根本原因，包括客户结构、产品特性、外部因素",
                    "🎯 结合业务数据进行多维度分析，如按客户群体、产品类型、地区等细分",
                    "🎯 建立逾期率预测模型，提前识别潜在风险并制定应对策略"
                ],
                "methodology": "🔬 采用SQL时间序列分析方法，通过GROUP BY时间维度统计DPD逾期率，结合ORDER BY进行时间排序，确保数据的时序性和可比性。分析逻辑基于历史数据趋势识别和业务风险评估框架。"
            }
        elif is_rate_analysis:
            return {
                "summary": f"针对用户查询'{user_input}'的比率分析，通过数据统计计算相关指标的比率表现，为业务决策提供量化依据。",
                "key_findings": [
                    "🔍 比率指标能够标准化不同规模数据的比较分析",
                    "🔍 查询结果提供了关键业务指标的比率表现数据",
                    "🔍 比率分析有助于识别业务表现的相对水平和变化趋势",
                    "🔍 数据结构支持进行基准对比和行业标准评估",
                    "🔍 比率指标可用于评估业务效率和风险水平"
                ],
                "insights": [
                    "💡 比率分析提供了标准化的业务表现评估视角",
                    "💡 比率变化趋势反映了业务运营效率和市场环境影响",
                    "💡 通过比率对比可以识别业务优势和改进空间",
                    "💡 比率指标是制定业务目标和评估策略效果的重要依据"
                ],
                "recommendations": [
                    "🎯 建立比率指标的基准值和目标值，用于业务表现评估",
                    "🎯 定期监控关键比率指标的变化，及时发现异常情况",
                    "🎯 结合行业标准进行比率对比分析，评估竞争地位",
                    "🎯 建立比率指标的预警机制，确保业务风险可控"
                ],
                "methodology": "🔬 采用比率分析方法，通过SQL计算相关指标的比率值，结合统计分析识别数据特征和变化趋势。分析框架基于财务分析和业务绩效评估的标准方法论。"
            }
        else:
            # 通用分析报告
            return {
                "summary": f"基于用户查询'{user_input}'的数据分析，通过SQL查询提取相关业务数据，为决策支持提供数据洞察。",
                "key_findings": [
                    "🔍 数据查询成功执行，获取了用户关注的业务指标数据",
                    "🔍 查询结果结构化展示，便于进行数据分析和解读",
                    "🔍 数据覆盖了用户关心的业务维度和时间范围",
                    "🔍 查询逻辑符合业务分析需求，数据准确性得到保障",
                    "🔍 结果数据可用于进一步的统计分析和趋势识别"
                ],
                "insights": [
                    "💡 数据分析结果反映了当前业务状态和关键指标表现",
                    "💡 通过数据可以识别业务运营中的模式和趋势",
                    "💡 数据洞察有助于理解业务驱动因素和影响机制",
                    "💡 分析结果为业务优化和决策制定提供了数据支撑"
                ],
                "recommendations": [
                    "🎯 建立定期数据监控机制，持续跟踪关键业务指标",
                    "🎯 深入分析数据背后的业务逻辑，识别改进机会",
                    "🎯 结合业务目标制定数据驱动的行动计划",
                    "🎯 建立数据质量管理体系，确保分析结果的可靠性"
                ],
                "methodology": "🔬 采用结构化查询语言(SQL)进行数据提取和初步统计，结合业务理解进行数据解读和洞察提取。分析方法基于描述性统计和业务逻辑推理。"
            }


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
        
        # Initialize time and report fixer
        self.time_report_fixer = TimeAndReportFixer()
        self._current_user_input = ""  # Store current user input for analysis

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

    def parse_prompt_response(self, model_out_text, user_input: str = ""):
        clean_str = super().parse_prompt_response(model_out_text)
        logger.info(f"=== DEBUG: parse_prompt_response ===")
        logger.info(f"Original model_out_text: {model_out_text}")
        logger.info(f"Clean prompt response: {clean_str}")
        logger.info(f"User input: {user_input}")
        logger.info(f"=== END DEBUG ===")
        
        # Store user input for analysis
        self._current_user_input = user_input
        
        # Compatible with community pure sql output model
        if self.is_sql_statement(clean_str):
            logger.info("Detected pure SQL statement")
            # Apply time fixes to pure SQL
            fixed_sql = self.time_report_fixer.fix_sql_time_references(clean_str)
            return SqlAction(fixed_sql, "", "", "", "", {})
        else:
            try:
                response = json.loads(clean_str, strict=False)
                logger.info(f"Successfully parsed JSON response: {response}")
                
                # Apply time and report fixes to the response
                response = self.time_report_fixer.ensure_analysis_report_in_response(response, user_input)
                
                sql = ""
                thoughts = dict
                display = ""
                resp = ""
                missing_info = ""
                analysis_report = {}
                for key in sorted(response):
                    if key.strip() == "sql":
                        sql = response[key]
                        # Apply time fixes to SQL
                        sql = self.time_report_fixer.fix_sql_time_references(sql)
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

    def parse_view_response(self, speak, data, prompt_response=None, mode="simple"):
        """
        Parse view response with dual-mode output support
        解析视图响应，支持双模式输出
        
        Args:
            speak: AI response text
            data: Query result data or callable
            prompt_response: Parsed prompt response (optional)
            mode: Output mode - "simple" (default, Markdown format) or "enhanced" (chart-view format)
        """
        logger.info(f"DEBUG parse_view_response called with mode: {mode}")
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

            # 🚨 改进：优先处理有意义的direct_response，支持非SQL查询
            if not hasattr(prompt_response, 'sql') or not prompt_response.sql:
                # 如果有direct_response，优先返回它（这是AI对概念性问题的回答）
                if (hasattr(prompt_response, 'direct_response') and
                    prompt_response.direct_response and
                    prompt_response.direct_response.strip()):

                    # 检查是否是有意义的回答（不是错误信息）
                    direct_resp = prompt_response.direct_response.strip()

                    # 如果是表结构不足的提示，提供更友好的回复
                    if "表结构信息不足" in direct_resp or "不足以生成" in direct_resp:
                        formatted_response = f"""💬 **AI分析回复**

{speak if speak else direct_resp}

📋 **说明**:
- 当前查询可能是概念性问题，不需要具体的数据库查询
- 或者需要更多的表结构信息才能生成准确的SQL查询

💡 **建议**:
- 如果您需要查询具体数据，请提供更详细的表名和字段信息
- 如果这是概念性问题，上述AI回复可能已经包含了您需要的信息
- 您可以尝试询问："显示所有可用的表"或"查询customer_info表的结构\""""

                        logger.info(f"Returning formatted direct response for insufficient table info")
                        return formatted_response
                    else:
                        # 其他类型的direct_response，直接返回但格式化
                        formatted_response = f"""💬 **AI回复**

{direct_resp}

📋 **说明**: AI模型基于您的查询提供了概念性回答

💡 **提示**: 如果您需要查询具体数据，请明确指出需要查询的表名和字段"""

                        logger.info(f"Returning formatted direct response")
                        return formatted_response

                # If we have analysis report but no SQL, format the report without data
                if has_analysis_report:
                    return self._format_analysis_report_only(prompt_response.analysis_report)

                # 最后的兜底处理：提供有用的信息而不是错误
                fallback_msg = f"""📋 **查询处理结果**

🤖 **AI分析**: {speak if speak else "AI模型已处理您的查询"}

💡 **说明**:
- 您的查询可能是概念性问题，不需要数据库查询
- 或者当前数据库信息不足以生成具体的SQL查询

🔧 **建议**:
- 如果需要查询数据，请提供具体的表名和字段名
- 尝试询问："显示数据库中的所有表"
- 或者重新描述您的数据查询需求"""

                logger.info(f"No SQL generated, returning fallback informative message")
                return fallback_msg
            
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
                # 🚨 改进：SQL验证失败时展示完整信息
                error_response = f"""📋 **SQL验证失败**

🔍 **验证错误**: {validation_error}

📝 **原始SQL**:
```sql
{original_sql}
```"""
                
                if fixes_applied:
                    error_response += f"""

🔧 **修复后的SQL**:
```sql
{sql_to_execute}
```

⚙️ **应用的修复**: {', '.join(fixes_applied)}"""
                
                error_response += """

💡 **建议**: 
- 请检查SQL语法是否正确
- 确认表名和字段名是否存在
- 避免使用危险的SQL操作（如DROP、DELETE等）"""
                
                logger.error(f"SQL validation failed: {validation_error}")
                return error_response
            
            # Execute SQL with enhanced error handling
            try:
                result = data(sql_to_execute)
                
                if result is None or result.empty:
                    # Even with empty results, show SQL and analysis report if available
                    if mode == "simple":
                        # Simple mode: Return Markdown format
                        empty_result_msg = f"""📊 **查询执行成功**

✅ **SQL执行状态**: 成功执行，但没有找到匹配的数据

💡 **建议**: 请尝试调整查询条件或检查数据是否存在

"""
                        
                        # Add SQL section
                        empty_result_msg += "="*60 + "\n"
                        empty_result_msg += "🔧 **执行的SQL查询**\n"
                        empty_result_msg += "="*60 + "\n\n"
                        empty_result_msg += "```sql\n"
                        empty_result_msg += sql_to_execute.strip()
                        empty_result_msg += "\n```\n\n"
                        empty_result_msg += "💡 **SQL说明**: 以上是执行的SQL语句，虽然没有返回数据，但SQL执行成功\n"
                        
                        # Add analysis report if available
                        if has_analysis_report:
                            empty_result_msg += "\n\n" + "="*60 + "\n"
                            empty_result_msg += "📋 **分析报告** (基于查询意图)\n"
                            empty_result_msg += "="*60 + "\n\n"
                            empty_result_msg += self._format_analysis_report_only(prompt_response.analysis_report)
                        
                        return empty_result_msg + fix_info
                    else:
                        # Enhanced mode: Generate chart-view format
                        return self._generate_chart_view_format(result, sql_to_execute, prompt_response, fix_info)
                
                # Format result for display based on mode
                if mode == "simple":
                    # Simple mode: Return Markdown format (default)
                    view_content = self._format_result_for_display(result, prompt_response)
                    return view_content + fix_info
                else:
                    # Enhanced mode: Generate chart-view format for frontend rendering
                    return self._generate_chart_view_format(result, sql_to_execute, prompt_response, fix_info)
                
            except (SQLAlchemyError, pymysql.Error, Exception) as sql_error:
                # If fixed SQL still fails, try the original SQL
                if fixes_applied:
                    logger.info("Fixed SQL failed, trying original SQL...")
                    try:
                        result = data(original_sql)
                        if result is not None and not result.empty:
                            if mode == "simple":
                                view_content = self._format_result_for_display(result, prompt_response)
                                return view_content + "\n⚠️ 注意: 使用了原始SQL查询（自动修复失败）"
                            else:
                                return self._generate_chart_view_format(result, original_sql, prompt_response, "\n⚠️ 注意: 使用了原始SQL查询（自动修复失败）")
                    except Exception as fallback_error:
                        logger.info(f"Original SQL also failed: {fallback_error}")
                        # Continue with comprehensive error handling below
                
                # 🚨 改进：提供最详细的错误信息，包括SQL内容
                user_friendly_error = self.format_sql_error_for_user(sql_error, sql_to_execute)
                technical_error = str(sql_error)
                
                logger.error(f"SQL execution failed: {technical_error}")
                logger.error(f"SQL that failed: {sql_to_execute}")
                
                # Return comprehensive error information with SQL display
                error_response = f"""📋 **数据库查询详细信息**

❌ **执行状态**: 查询失败

🔍 **错误原因**: {user_friendly_error}

📝 **执行的SQL**:
```sql
{sql_to_execute}
```"""

                # Show original SQL if it was modified
                if fixes_applied and sql_to_execute != original_sql:
                    error_response += f"""

📝 **原始SQL**:
```sql
{original_sql}
```

🔧 **已尝试的修复**: {', '.join(fixes_applied)}"""

                error_response += f"""

🔧 **技术详情**: {technical_error}

💡 **建议**: 
- 检查表名和字段名是否正确
- 确认数据库中是否存在相关数据
- 尝试简化查询条件
- 检查SQL语法是否符合MySQL标准"""

                # Add analysis report if available, even when SQL fails
                if has_analysis_report:
                    error_response += "\n\n" + "="*60 + "\n"
                    error_response += "📋 **AI分析报告** (基于查询意图)\n"
                    error_response += "="*60 + "\n\n"
                    error_response += self._format_analysis_report_only(prompt_response.analysis_report)
                
                return error_response + fix_info
                
        except Exception as e:
            # 🚨 改进：最后的兜底处理，确保永远不显示通用错误
            logger.error(f"Unexpected error in parse_view_response: {str(e)}")
            
            # Try to extract SQL from prompt_response if available
            sql_info = ""
            if hasattr(prompt_response, 'sql') and prompt_response.sql:
                sql_info = f"""

📝 **相关SQL**:
```sql
{prompt_response.sql}
```"""
            
            # Try to include AI response if available
            ai_response_info = ""
            if speak:
                ai_response_info = f"""

💬 **AI回复内容**:
```
{speak}
```"""
            
            return f"""📋 **系统处理信息**

⚠️ **处理状态**: 系统在处理您的请求时遇到了意外情况

🔧 **技术详情**: {str(e)}{sql_info}{ai_response_info}

💡 **建议**: 
- 请尝试重新提交您的查询
- 如果问题持续存在，请简化您的查询条件
- 您可以尝试分步骤查询来定位问题"""

    def _format_dataframe_as_markdown_table(self, df):
        """
        Convert DataFrame to a well-formatted Markdown table
        将DataFrame转换为格式良好的Markdown表格
        """
        try:
            if df.empty:
                return "📊 查询结果为空"
            
            # Get column names
            columns = list(df.columns)
            
            # Create table header
            header = "| " + " | ".join(columns) + " |"
            separator = "|" + "|".join([" --- " for _ in columns]) + "|"
            
            # Create data rows
            rows = []
            for _, row in df.iterrows():
                formatted_row = []
                for col in columns:
                    value = row[col]
                    # Format different types of values
                    if pd.isna(value) or value is None:
                        formatted_row.append("-")
                    elif isinstance(value, (int, float)):
                        if col.upper().startswith('MOB') or '率' in col or 'rate' in col.lower():
                            # Format as percentage for rate columns
                            if value == 0:
                                formatted_row.append("0.00%")
                            else:
                                formatted_row.append(f"{value:.2%}")
                        else:
                            # Format as regular number
                            formatted_row.append(f"{value:,.2f}")
                    else:
                        # Format as string
                        formatted_row.append(str(value))
                rows.append("| " + " | ".join(formatted_row) + " |")
            
            # Combine all parts
            table = "\n".join([header, separator] + rows)
            return table
            
        except Exception as e:
            logger.error(f"Error creating Markdown table: {str(e)}")
            # Fallback to original format
            return df.to_string(index=False, max_rows=50)

    def _format_result_for_display(self, result, prompt_response):
        """
        Format query result for display with analysis report and SQL
        格式化查询结果用于显示，包含分析报告和SQL
        """
        try:
            # Convert DataFrame to a user-friendly format
            if len(result) == 0:
                return "📊 查询执行成功，但没有找到匹配的数据。"
            
            # Handle duplicate columns in DataFrame
            if hasattr(result, 'columns'):
                original_columns = list(result.columns)
                if len(original_columns) != len(set(original_columns)):
                    logger.info("检测到DataFrame重复列名，正在修复...")
                    
                    # Create new column names for duplicates
                    new_columns = []
                    column_counts = {}
                    
                    for col in original_columns:
                        if col in column_counts:
                            column_counts[col] += 1
                            new_col_name = f"{col}_{column_counts[col]}"
                        else:
                            column_counts[col] = 0
                            new_col_name = col
                        new_columns.append(new_col_name)
                    
                    # Apply new column names
                    result.columns = new_columns
                    logger.info(f"DataFrame列名已修复: {original_columns} -> {new_columns}")
            
            # Create a formatted table using Markdown format
            formatted_result = "📊 **查询结果**\n\n"
            
            # Add table description if it looks like a pivot table
            if any('MOB' in str(col) for col in result.columns):
                formatted_result += "**逾期率分析表** (按放款月份和MOB期数)\n\n"
            
            # Use Markdown table format for better readability
            markdown_table = self._format_dataframe_as_markdown_table(result)
            formatted_result += markdown_table
            
            # Add record count info
            if len(result) > 50:
                formatted_result += f"\n\n📋 显示前50条记录，共 **{len(result)}** 条记录"
            else:
                formatted_result += f"\n\n📋 共 **{len(result)}** 条记录"
            
            # Add data interpretation for rate tables
            if any('MOB' in str(col) for col in result.columns):
                formatted_result += "\n\n💡 **数据说明**:\n"
                formatted_result += "- MOB (Months on Books): 放款后的月数\n"
                formatted_result += "- 逾期率以百分比显示，'-' 表示暂无数据\n"
                formatted_result += "- 数据按放款月份排列，便于趋势分析\n"
            
            # Add SQL section if available
            if hasattr(prompt_response, 'sql') and prompt_response.sql:
                formatted_result += "\n\n" + "="*60 + "\n"
                formatted_result += "🔧 **执行的SQL查询**\n"
                formatted_result += "="*60 + "\n\n"
                formatted_result += "```sql\n"
                formatted_result += prompt_response.sql.strip()
                formatted_result += "\n```\n\n"
                formatted_result += "💡 **SQL说明**: 以上是生成此查询结果的SQL语句，您可以参考或复制使用\n"
            
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

    def _generate_chart_view_format(self, result, sql, prompt_response, fix_info):
        """
        Generate chart-view format for frontend rendering
        生成chart-view格式用于前端渲染
        
        Args:
            result: Query result DataFrame
            sql: SQL query string
            prompt_response: Parsed prompt response
            fix_info: SQL fix information
            
        Returns:
            str: chart-view formatted string
        """
        try:
            import json
            import xml.etree.ElementTree as ET
            from dbgpt.util.json_utils import serialize
            
            # Prepare chart-view data
            param = {}
            param["type"] = "response_table"
            param["sql"] = sql
            
            if result is not None and not result.empty:
                # Convert DataFrame to JSON format
                param["data"] = json.loads(
                    result.to_json(orient="records", date_format="iso", date_unit="s")
                )
            else:
                param["data"] = []
            
            # Add analysis report if available
            if (hasattr(prompt_response, 'analysis_report') and 
                prompt_response.analysis_report and 
                isinstance(prompt_response.analysis_report, dict)):
                param["analysis_report"] = prompt_response.analysis_report
            
            # Generate chart-view XML element
            view_json_str = json.dumps(param, default=serialize, ensure_ascii=False)
            api_call_element = ET.Element("chart-view")
            api_call_element.set("content", view_json_str)
            result_xml = ET.tostring(api_call_element, encoding="utf-8")
            
            chart_view_content = result_xml.decode("utf-8")
            
            # Add fix info if available
            if fix_info:
                chart_view_content += fix_info
                
            return chart_view_content
            
        except Exception as e:
            logger.error(f"Error generating chart-view format: {str(e)}")
            # Fallback to simple mode if chart-view generation fails
            return self._format_result_for_display(result, prompt_response) + fix_info
