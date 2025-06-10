#!/usr/bin/env python3
"""
装饰器应用示例 - 展示如何在实际代码中应用 @safe_dataframe_decorator

这个文件展示了具体的修改步骤和代码示例
"""

# ============================================================================
# 步骤1：在文件顶部添加导入（在现有导入之后）
# ============================================================================

# 现有的导入保持不变
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

# 🔥 新增：导入装饰器
from simple_decorator_fix import safe_dataframe_decorator

CFG = Config()

# ============================================================================
# 步骤2：在类中应用装饰器（只需添加一行）
# ============================================================================

class DbChatOutputParser(BaseOutputParser):
    def __init__(self, is_stream_out: bool = False, connector=None, **kwargs):
        # ... 现有代码保持不变 ...
        super().__init__(is_stream_out=is_stream_out, **kwargs)
        self._sql_validator = None
        self._connector = connector
        
        if connector:
            self._initialize_sql_validator()
        self.sql_fixer = create_sql_fixer()

    # ... 其他方法保持不变 ...

    # 🔥 关键修改：只需在方法前添加装饰器
    @safe_dataframe_decorator  # ← 只需添加这一行！
    def parse_view_response(self, speak, data, prompt_response=None):
        """
        Parse view response with enhanced error handling and SQL fixing
        解析视图响应，增强错误处理和SQL修复
        
        Args:
            speak: AI response text
            data: Query result data or callable
            prompt_response: Parsed prompt response (optional)
        """
        # 🔥 重要：以下所有代码保持完全不变！
        logger.info(f"DEBUG parse_view_response called with speak: {speak}")
        logger.info(f"DEBUG parse_view_response called with data type: {type(data)}")
        logger.info(f"DEBUG parse_view_response called with prompt_response type: {type(prompt_response)}")
        
        if hasattr(prompt_response, 'direct_response'):
            logger.info(f"DEBUG prompt_response.direct_response: {prompt_response.direct_response}")
        if hasattr(prompt_response, 'sql'):
            logger.info(f"DEBUG prompt_response.sql: {prompt_response.sql}")
        
        try:
            # Check if we have analysis report
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
                        pass
                
                # Enhanced SQL error handling
                user_friendly_error = self.format_sql_error_for_user(sql_error, sql_to_execute)
                technical_error = str(sql_error)
                
                logger.error(f"SQL execution failed: {technical_error}")
                logger.error(f"SQL that failed: {sql_to_execute}")
                
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
            logger.error(f"Unexpected error in parse_view_response: {str(e)}")
            return f"❌ 系统错误: {str(e)}"

    # ... 其他方法保持不变 ...

# ============================================================================
# 总结：只需要做两个修改
# ============================================================================

print("""
🎯 装饰器应用总结

只需要做两个简单修改：

1. 在文件顶部添加导入：
   from simple_decorator_fix import safe_dataframe_decorator

2. 在 parse_view_response 方法前添加装饰器：
   @safe_dataframe_decorator
   def parse_view_response(self, speak, data, prompt_response=None):

✅ 完成！无需其他任何修改！

装饰器会自动：
- 检测和修复SQL中的重复列名
- 处理DataFrame的重复列名
- 提供详细的修复日志
- 确保向后兼容性

🚀 立即生效，彻底解决 "DataFrame columns must be unique" 错误！
""") 