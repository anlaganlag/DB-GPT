#!/usr/bin/env python3
"""
SQL验证和修复中间件
在SQL执行前进行字段引用验证，提供自动修复建议
"""

import logging
import json
import re
from typing import Dict, List, Optional, Tuple, Any
from .table_schema_validator import TableSchemaValidator
from .enhanced_prompt_manager import EnhancedPromptManager

logger = logging.getLogger(__name__)

class SQLValidationMiddleware:
    """SQL验证和修复中间件"""
    
    def __init__(self, schema_validator: TableSchemaValidator, prompt_manager: EnhancedPromptManager):
        self.schema_validator = schema_validator
        self.prompt_manager = prompt_manager
        self.validation_enabled = True
        
    def enable_validation(self):
        """启用SQL验证"""
        self.validation_enabled = True
        logger.info("SQL validation enabled")
        
    def disable_validation(self):
        """禁用SQL验证"""
        self.validation_enabled = False
        logger.info("SQL validation disabled")
    
    async def validate_and_fix_sql(self, sql: str, llm_client=None) -> Tuple[str, bool, List[str], Dict[str, Any]]:
        """
        验证并修复SQL查询
        
        Args:
            sql: 待验证的SQL查询
            llm_client: LLM客户端，用于智能修复
            
        Returns:
            (fixed_sql, is_valid, validation_errors, fix_metadata)
        """
        
        if not self.validation_enabled or not self.schema_validator.cached_schemas:
            return sql, True, [], {"validation_skipped": True}
        
        fix_metadata = {
            "original_sql": sql,
            "validation_enabled": True,
            "validation_errors": [],
            "fixes_applied": [],
            "fix_method": "none"
        }
        
        try:
            # 1. 基础SQL验证
            is_valid, validation_errors = self.schema_validator.validate_sql_fields(sql)
            fix_metadata["validation_errors"] = validation_errors
            
            if is_valid:
                logger.info("SQL validation passed")
                return sql, True, [], fix_metadata
            
            logger.warning(f"SQL validation failed with {len(validation_errors)} errors")
            
            # 2. 尝试自动修复
            fixed_sql = sql
            
            # 方法1: 基于规则的修复
            rule_fixed_sql = self.schema_validator.suggest_sql_fix(sql, validation_errors)
            if rule_fixed_sql != sql:
                fix_metadata["fix_method"] = "rule_based"
                fix_metadata["fixes_applied"].append("Applied rule-based field reference corrections")
                fixed_sql = rule_fixed_sql
                
                # 验证修复结果
                is_fixed_valid, fixed_errors = self.schema_validator.validate_sql_fields(fixed_sql)
                if is_fixed_valid:
                    logger.info("SQL successfully fixed using rule-based approach")
                    return fixed_sql, True, [], fix_metadata
                else:
                    logger.warning("Rule-based fix didn't resolve all issues")
            
            # 方法2: LLM智能修复（如果提供了LLM客户端）
            if llm_client:
                try:
                    llm_fixed_sql = await self._llm_fix_sql(sql, validation_errors, llm_client)
                    if llm_fixed_sql and llm_fixed_sql != sql:
                        fix_metadata["fix_method"] = "llm_based"
                        fix_metadata["fixes_applied"].append("Applied LLM-based intelligent fixes")
                        
                        # 验证LLM修复结果
                        is_llm_fixed_valid, llm_fixed_errors = self.schema_validator.validate_sql_fields(llm_fixed_sql)
                        if is_llm_fixed_valid:
                            logger.info("SQL successfully fixed using LLM approach")
                            return llm_fixed_sql, True, [], fix_metadata
                        else:
                            logger.warning("LLM-based fix didn't resolve all issues")
                            fixed_sql = llm_fixed_sql  # 使用LLM修复的版本，即使不完美
                
                except Exception as e:
                    logger.error(f"LLM-based SQL fix failed: {e}")
            
            # 3. 如果所有修复方法都失败，返回最佳尝试结果
            logger.error("All SQL fix attempts failed, returning best attempt")
            return fixed_sql, False, validation_errors, fix_metadata
            
        except Exception as e:
            logger.error(f"SQL validation middleware error: {e}")
            fix_metadata["error"] = str(e)
            return sql, False, [f"Validation error: {e}"], fix_metadata
    
    async def _llm_fix_sql(self, sql: str, validation_errors: List[str], llm_client) -> Optional[str]:
        """
        使用LLM智能修复SQL
        
        Args:
            sql: 原始SQL
            validation_errors: 验证错误列表
            llm_client: LLM客户端
            
        Returns:
            修复后的SQL，如果修复失败返回None
        """
        try:
            # 生成修复prompt
            fix_prompt = self.prompt_manager.get_sql_validation_prompt(sql, validation_errors)
            
            # 调用LLM进行修复
            response = await llm_client.generate(fix_prompt)
            
            # 解析LLM响应
            fixed_sql = self._parse_llm_fix_response(response)
            
            if fixed_sql:
                logger.info("LLM successfully generated SQL fix")
                return fixed_sql
            else:
                logger.warning("Failed to parse LLM fix response")
                return None
                
        except Exception as e:
            logger.error(f"LLM SQL fix error: {e}")
            return None
    
    def _parse_llm_fix_response(self, response: str) -> Optional[str]:
        """
        解析LLM修复响应，提取修复后的SQL
        
        Args:
            response: LLM响应文本
            
        Returns:
            修复后的SQL，如果解析失败返回None
        """
        try:
            # 尝试解析JSON响应
            if response.strip().startswith('{'):
                json_response = json.loads(response)
                return json_response.get('fixed_sql')
            
            # 尝试从文本中提取SQL
            # 查找SQL代码块
            sql_pattern = r'```sql\s*(.*?)\s*```'
            sql_match = re.search(sql_pattern, response, re.DOTALL | re.IGNORECASE)
            if sql_match:
                return sql_match.group(1).strip()
            
            # 查找固定SQL字段
            fixed_sql_pattern = r'"fixed_sql"\s*:\s*"([^"]*)"'
            fixed_sql_match = re.search(fixed_sql_pattern, response)
            if fixed_sql_match:
                return fixed_sql_match.group(1)
            
            logger.warning("Could not parse LLM fix response format")
            return None
            
        except Exception as e:
            logger.error(f"Error parsing LLM fix response: {e}")
            return None
    
    def get_validation_report(self, fix_metadata: Dict[str, Any]) -> str:
        """
        生成验证报告
        
        Args:
            fix_metadata: 修复元数据
            
        Returns:
            格式化的验证报告
        """
        if fix_metadata.get("validation_skipped"):
            return "SQL validation was skipped (validation disabled or schemas not loaded)"
        
        report = []
        report.append("=== SQL VALIDATION REPORT ===")
        
        if fix_metadata.get("validation_errors"):
            report.append(f"\n❌ Validation Errors Found ({len(fix_metadata['validation_errors'])}):")
            for i, error in enumerate(fix_metadata["validation_errors"], 1):
                report.append(f"  {i}. {error}")
        else:
            report.append("\n✅ No validation errors found")
        
        if fix_metadata.get("fixes_applied"):
            report.append(f"\n🔧 Fixes Applied ({fix_metadata.get('fix_method', 'unknown')} method):")
            for i, fix in enumerate(fix_metadata["fixes_applied"], 1):
                report.append(f"  {i}. {fix}")
        
        if fix_metadata.get("error"):
            report.append(f"\n⚠️ Validation Error: {fix_metadata['error']}")
        
        return "\n".join(report)
    
    def create_enhanced_error_message(self, original_error: str, validation_errors: List[str], 
                                    fix_metadata: Dict[str, Any]) -> str:
        """
        创建增强的错误消息，包含验证信息和修复建议
        
        Args:
            original_error: 原始数据库错误
            validation_errors: 验证错误列表
            fix_metadata: 修复元数据
            
        Returns:
            增强的错误消息
        """
        enhanced_message = []
        
        enhanced_message.append("🔍 **SQL EXECUTION ERROR ANALYSIS**")
        enhanced_message.append(f"\n**Original Database Error:**")
        enhanced_message.append(f"```\n{original_error}\n```")
        
        if validation_errors:
            enhanced_message.append(f"\n**Validation Issues Detected:**")
            for i, error in enumerate(validation_errors, 1):
                enhanced_message.append(f"{i}. {error}")
        
        if fix_metadata.get("fixes_applied"):
            enhanced_message.append(f"\n**Attempted Fixes:**")
            for fix in fix_metadata["fixes_applied"]:
                enhanced_message.append(f"- {fix}")
        
        enhanced_message.append(f"\n**Recommendation:**")
        if validation_errors:
            enhanced_message.append("The SQL query contains field reference errors. Please check:")
            enhanced_message.append("1. Ensure all fields exist in the referenced tables")
            enhanced_message.append("2. Use correct table aliases for field references")
            enhanced_message.append("3. Verify JOIN conditions reference existing fields")
        else:
            enhanced_message.append("The SQL syntax appears correct based on schema validation.")
            enhanced_message.append("This may be a runtime error or data-related issue.")
        
        return "\n".join(enhanced_message) 