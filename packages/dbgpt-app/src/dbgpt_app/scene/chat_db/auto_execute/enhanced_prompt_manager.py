#!/usr/bin/env python3
"""
增强的Prompt模板管理器
集成表结构信息，提供智能的SQL生成指导
"""

import logging
from typing import Dict, List, Optional, Any
from .table_schema_validator import TableSchemaValidator

logger = logging.getLogger(__name__)

class EnhancedPromptManager:
    """增强的Prompt模板管理器"""
    
    def __init__(self, schema_validator: TableSchemaValidator):
        self.schema_validator = schema_validator
        
    def get_enhanced_sql_prompt(self, user_query: str, database_name: str = "orange") -> str:
        """
        获取增强的SQL生成prompt，包含表结构信息和字段映射指导
        """
        
        # 获取表结构摘要
        schema_info = self.schema_validator.get_table_info_summary()
        
        # 构建增强的prompt
        enhanced_prompt = f"""
You are an expert SQL analyst working with a financial lending database. You must generate accurate SQL queries based on the user's request.

{schema_info}

=== CRITICAL FIELD REFERENCE RULES ===
1. ALWAYS use correct table aliases when referencing fields
2. The 'strategy' field exists ONLY in 'orange.t_ws_entrance_credit' table (use alias t1.strategy)
3. The 'output_level' field exists ONLY in 'orange.t_model_inputparams_extend2' table (use alias t1.output_level)
4. The 'product_id' field exists in 'orange.lending_details' table (use alias b.product_id)
5. NEVER reference fields that don't exist in the specified table

=== COMMON FIELD MAPPING ERRORS TO AVOID ===
❌ WRONG: b.strategy (strategy field does not exist in lending_details table)
✅ CORRECT: t1.strategy (strategy field exists in t_ws_entrance_credit, accessed via LEFT JOIN as t1)

❌ WRONG: b.output_level (output_level field does not exist in lending_details table)  
✅ CORRECT: t1.output_level (output_level field exists in t_model_inputparams_extend2, accessed via LEFT JOIN as t1)

=== SQL GENERATION GUIDELINES ===
1. Always validate field references against the table schema above
2. Use proper table aliases consistently throughout the query
3. When joining tables, ensure the JOIN conditions are correct
4. For GROUP BY clauses, use the same field references as in SELECT
5. Test your field references mentally against the schema before finalizing

=== USER QUERY ===
{user_query}

=== RESPONSE FORMAT ===
Please provide your response in the following JSON format:
{{
    "thoughts": "Your analysis of the user's request and SQL strategy",
    "direct_response": "A brief explanation of what the SQL will do",
    "sql": "Your complete SQL query with correct field references",
    "display_type": "Table",
    "missing_info": "",
    "analysis_report": {{
        "summary": "Summary of the analysis",
        "key_findings": ["List of key findings"],
        "insights": ["Business insights"],
        "recommendations": ["Actionable recommendations"],
        "methodology": "Description of the analysis methodology"
    }}
}}

IMPORTANT: Before finalizing your SQL, double-check each field reference against the schema information provided above. Ensure all field references use the correct table alias.
"""
        
        return enhanced_prompt
    
    def get_sql_validation_prompt(self, sql: str, validation_errors: List[str]) -> str:
        """
        获取SQL验证和修复的prompt
        """
        
        errors_text = "\n".join([f"- {error}" for error in validation_errors])
        
        validation_prompt = f"""
The following SQL query has validation errors that need to be fixed:

=== ORIGINAL SQL ===
{sql}

=== VALIDATION ERRORS ===
{errors_text}

=== INSTRUCTIONS ===
Please fix the SQL query by correcting the field references based on the validation errors above.
Each error message includes a suggestion for the correct field reference.

=== RESPONSE FORMAT ===
Please provide your response in JSON format:
{{
    "fixed_sql": "The corrected SQL query",
    "changes_made": ["List of specific changes made"],
    "explanation": "Brief explanation of the fixes applied"
}}

Focus on correcting the field references while maintaining the original query logic and structure.
"""
        
        return validation_prompt
    
    def get_table_analysis_prompt(self, table_name: str) -> str:
        """
        获取表分析的prompt
        """
        
        table_fields = self.schema_validator.table_schemas.get(table_name, [])
        
        if not table_fields:
            return f"Table {table_name} not found in schema cache."
        
        fields_info = []
        for field in table_fields:
            key_info = " (KEY)" if field.is_key else ""
            null_info = " (NULL)" if field.is_nullable else " (NOT NULL)"
            fields_info.append(f"  - {field.field_name}: {field.field_type}{key_info}{null_info}")
        
        analysis_prompt = f"""
=== TABLE ANALYSIS: {table_name} ===

Fields in this table:
{chr(10).join(fields_info)}

This table contains {len(table_fields)} fields total.

Key fields (primary/unique keys):
{chr(10).join([f"  - {field.field_name}" for field in table_fields if field.is_key])}

When writing SQL queries involving this table:
1. Use appropriate table alias for clarity
2. Reference fields correctly with the alias
3. Consider NULL constraints when writing WHERE conditions
4. Use key fields for efficient JOIN operations
"""
        
        return analysis_prompt
    
    def get_field_mapping_guide(self, field_name: str) -> str:
        """
        获取特定字段的映射指导
        """
        
        tables_with_field = self.schema_validator.field_mappings.get(field_name, set())
        
        if not tables_with_field:
            return f"Field '{field_name}' does not exist in any loaded table."
        
        guide = f"""
=== FIELD MAPPING GUIDE: {field_name} ===

This field exists in the following tables:
{chr(10).join([f"  - {table}" for table in tables_with_field])}

Usage examples:
"""
        
        # 生成使用示例
        for i, table in enumerate(tables_with_field):
            alias = chr(ord('a') + i)  # a, b, c, etc.
            table_simple = table.split('.')[-1]
            guide += f"""
  Table: {table} (alias: {alias})
  Reference: {alias}.{field_name}
  Example: SELECT {alias}.{field_name} FROM {table} {alias}
"""
        
        return guide
    
    def enhance_existing_prompt(self, original_prompt: str) -> str:
        """
        增强现有的prompt，添加表结构信息
        """
        
        schema_info = self.schema_validator.get_table_info_summary()
        
        enhanced = f"""
{original_prompt}

=== ENHANCED WITH SCHEMA INFORMATION ===
{schema_info}

=== FIELD REFERENCE VALIDATION RULES ===
Before generating any SQL:
1. Check if each field exists in the referenced table
2. Use correct table aliases for field references  
3. Verify JOIN conditions reference existing fields
4. Ensure GROUP BY fields match SELECT field references

Remember: Field references like 'table_alias.field_name' must be validated against the actual table schema.
"""
        
        return enhanced 