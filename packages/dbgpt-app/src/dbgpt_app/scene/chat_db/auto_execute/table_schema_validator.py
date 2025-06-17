#!/usr/bin/env python3
"""
表结构验证器和字段映射管理器
用于防止SQL字段引用错误，加强表结构理解，提供验证机制
"""

import logging
import re
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass
from collections import defaultdict
import sqlparse
from sqlparse.sql import IdentifierList, Identifier
from sqlparse.tokens import Keyword, Name

logger = logging.getLogger(__name__)

@dataclass
class TableField:
    """表字段信息"""
    table_name: str
    field_name: str
    field_type: str
    is_nullable: bool
    is_key: bool
    default_value: Optional[str] = None

@dataclass
class TableAlias:
    """表别名信息"""
    alias: str
    table_name: str
    schema_name: Optional[str] = None

class TableSchemaValidator:
    """表结构验证器"""
    
    def __init__(self, database_connector):
        self.db_connector = database_connector
        self.table_schemas: Dict[str, List[TableField]] = {}
        self.field_mappings: Dict[str, Set[str]] = defaultdict(set)  # field_name -> {table1, table2, ...}
        self.cached_schemas = False
        
    async def load_table_schemas(self, schema_name: str = "orange") -> None:
        """加载所有表的结构信息"""
        try:
            # 获取所有表名
            tables_query = f"SHOW TABLES FROM {schema_name}"
            tables_result = await self.db_connector.run_to_list(tables_query)
            
            logger.info(f"Found {len(tables_result)} tables in schema {schema_name}")
            
            for table_row in tables_result:
                table_name = table_row[0]
                await self._load_single_table_schema(schema_name, table_name)
                
            self.cached_schemas = True
            logger.info(f"Successfully loaded schemas for {len(self.table_schemas)} tables")
            
        except Exception as e:
            logger.error(f"Failed to load table schemas: {e}")
            raise
    
    async def _load_single_table_schema(self, schema_name: str, table_name: str) -> None:
        """加载单个表的结构信息"""
        try:
            full_table_name = f"{schema_name}.{table_name}"
            describe_query = f"DESCRIBE {full_table_name}"
            columns_result = await self.db_connector.run_to_list(describe_query)
            
            table_fields = []
            for col_row in columns_result:
                field = TableField(
                    table_name=full_table_name,
                    field_name=col_row[0],  # Field
                    field_type=col_row[1],  # Type
                    is_nullable=col_row[2] == 'YES',  # Null
                    is_key=col_row[3] in ('PRI', 'UNI', 'MUL'),  # Key
                    default_value=col_row[4] if len(col_row) > 4 else None  # Default
                )
                table_fields.append(field)
                
                # 建立字段映射
                self.field_mappings[field.field_name].add(full_table_name)
            
            self.table_schemas[full_table_name] = table_fields
            logger.debug(f"Loaded schema for table {full_table_name}: {len(table_fields)} fields")
            
        except Exception as e:
            logger.error(f"Failed to load schema for table {table_name}: {e}")
    
    def validate_field_reference(self, field_name: str, table_alias: str, 
                                table_aliases: Dict[str, str]) -> Tuple[bool, str]:
        """
        验证字段引用是否正确
        
        Args:
            field_name: 字段名
            table_alias: 表别名
            table_aliases: 别名到表名的映射 {alias: table_name}
            
        Returns:
            (is_valid, error_message)
        """
        if not self.cached_schemas:
            return False, "Table schemas not loaded"
        
        # 获取实际表名
        actual_table = table_aliases.get(table_alias)
        if not actual_table:
            return False, f"Unknown table alias: {table_alias}"
        
        # 检查字段是否存在于指定表中
        table_fields = self.table_schemas.get(actual_table, [])
        field_exists = any(field.field_name == field_name for field in table_fields)
        
        if not field_exists:
            # 提供修复建议
            suggestion = self._get_field_suggestion(field_name, table_aliases)
            return False, f"Field '{field_name}' does not exist in table '{actual_table}' (alias: {table_alias}). {suggestion}"
        
        return True, ""
    
    def _get_field_suggestion(self, field_name: str, table_aliases: Dict[str, str]) -> str:
        """获取字段修复建议"""
        # 查找该字段在哪些表中存在
        tables_with_field = self.field_mappings.get(field_name, set())
        
        if not tables_with_field:
            return f"Field '{field_name}' does not exist in any loaded table."
        
        # 查找在当前查询中可用的表
        available_tables = set(table_aliases.values())
        matching_tables = tables_with_field.intersection(available_tables)
        
        if matching_tables:
            # 找到对应的别名
            suggestions = []
            for table in matching_tables:
                for alias, table_name in table_aliases.items():
                    if table_name == table:
                        suggestions.append(f"{alias}.{field_name}")
            
            if suggestions:
                return f"Suggestion: Use {' or '.join(suggestions)} instead."
        
        return f"Field '{field_name}' is available in: {', '.join(tables_with_field)}"
    
    def parse_sql_tables_and_aliases(self, sql: str) -> Dict[str, str]:
        """
        解析SQL中的表和别名
        
        Returns:
            Dict[alias, full_table_name]
        """
        table_aliases = {}
        
        try:
            parsed = sqlparse.parse(sql)[0]
            
            # 查找FROM和JOIN子句
            from_seen = False
            join_seen = False
            
            for token in parsed.flatten():
                if token.ttype is Keyword and token.value.upper() in ('FROM', 'JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'INNER JOIN', 'OUTER JOIN'):
                    from_seen = True
                    continue
                    
                if from_seen and token.ttype is None and token.value.strip():
                    # 解析表名和别名
                    parts = token.value.strip().split()
                    if len(parts) >= 2:
                        table_name = parts[0]
                        alias = parts[1]
                        table_aliases[alias] = table_name
                    elif len(parts) == 1 and '.' in parts[0]:
                        # 处理 schema.table 格式
                        table_name = parts[0]
                        # 使用表名作为别名（如果没有显式别名）
                        simple_name = table_name.split('.')[-1]
                        table_aliases[simple_name] = table_name
                    
                    from_seen = False
        
        except Exception as e:
            logger.warning(f"Failed to parse SQL tables and aliases: {e}")
        
        return table_aliases
    
    def validate_sql_fields(self, sql: str) -> Tuple[bool, List[str]]:
        """
        验证SQL中的所有字段引用
        
        Returns:
            (is_valid, error_messages)
        """
        if not self.cached_schemas:
            return False, ["Table schemas not loaded"]
        
        errors = []
        
        try:
            # 解析表别名
            table_aliases = self.parse_sql_tables_and_aliases(sql)
            
            # 查找所有字段引用
            field_references = self._extract_field_references(sql)
            
            for table_alias, field_name in field_references:
                is_valid, error_msg = self.validate_field_reference(
                    field_name, table_alias, table_aliases
                )
                if not is_valid:
                    errors.append(error_msg)
        
        except Exception as e:
            errors.append(f"SQL validation failed: {e}")
        
        return len(errors) == 0, errors
    
    def _extract_field_references(self, sql: str) -> List[Tuple[str, str]]:
        """
        提取SQL中的字段引用
        
        Returns:
            List[(table_alias, field_name)]
        """
        field_references = []
        
        # 使用正则表达式查找 alias.field 模式
        pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\.\s*([a-zA-Z_][a-zA-Z0-9_]*)\b'
        matches = re.findall(pattern, sql)
        
        for table_alias, field_name in matches:
            # 过滤掉一些常见的非字段引用
            if table_alias.upper() not in ('DATE_FORMAT', 'DATE_SUB', 'YEAR', 'MONTH'):
                field_references.append((table_alias, field_name))
        
        return field_references
    
    def suggest_sql_fix(self, sql: str, errors: List[str]) -> str:
        """
        基于错误信息建议SQL修复
        
        Args:
            sql: 原始SQL
            errors: 错误信息列表
            
        Returns:
            修复后的SQL建议
        """
        fixed_sql = sql
        
        try:
            table_aliases = self.parse_sql_tables_and_aliases(sql)
            
            for error in errors:
                if "does not exist in table" in error and "Suggestion:" in error:
                    # 提取建议的修复
                    suggestion_match = re.search(r"Suggestion: Use (.*?) instead", error)
                    if suggestion_match:
                        suggested_fix = suggestion_match.group(1)
                        
                        # 提取错误的字段引用
                        field_match = re.search(r"Field '(.+?)' does not exist in table '(.+?)' \(alias: (.+?)\)", error)
                        if field_match:
                            field_name = field_match.group(1)
                            table_name = field_match.group(2)
                            alias = field_match.group(3)
                            
                            # 替换错误的引用
                            wrong_reference = f"{alias}.{field_name}"
                            fixed_sql = fixed_sql.replace(wrong_reference, suggested_fix)
            
        except Exception as e:
            logger.error(f"Failed to suggest SQL fix: {e}")
        
        return fixed_sql
    
    def get_table_info_summary(self) -> str:
        """获取表结构信息摘要，用于增强prompt"""
        if not self.cached_schemas:
            return "Table schemas not loaded"
        
        summary = []
        summary.append("=== DATABASE SCHEMA INFORMATION ===")
        
        for table_name, fields in self.table_schemas.items():
            summary.append(f"\nTable: {table_name}")
            summary.append("Fields:")
            
            for field in fields[:10]:  # 限制显示字段数量
                key_info = " (KEY)" if field.is_key else ""
                null_info = " (NULL)" if field.is_nullable else " (NOT NULL)"
                summary.append(f"  - {field.field_name}: {field.field_type}{key_info}{null_info}")
            
            if len(fields) > 10:
                summary.append(f"  ... and {len(fields) - 10} more fields")
        
        summary.append("\n=== FIELD MAPPING SUMMARY ===")
        
        # 显示重要字段的分布
        important_fields = ['strategy', 'output_level', 'product_id', 'due_bill_no']
        for field_name in important_fields:
            tables = self.field_mappings.get(field_name, set())
            if tables:
                summary.append(f"{field_name}: {', '.join(tables)}")
        
        return "\n".join(summary) 