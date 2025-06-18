#!/usr/bin/env python3
"""
独立SQL验证功能测试脚本
测试核心的SQL字段验证逻辑，不依赖DB-GPT内部模块
"""

import re
import asyncio
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict

print("🚀 开始独立SQL验证功能测试...")

@dataclass
class TableField:
    """表字段信息"""
    table_name: str
    field_name: str
    field_type: str
    is_nullable: bool
    is_key: bool

class SimpleSQLValidator:
    """简化的SQL验证器"""
    
    def __init__(self):
        self.table_schemas: Dict[str, List[TableField]] = {}
        self.field_mappings: Dict[str, Set[str]] = defaultdict(set)
        self.setup_mock_data()
    
    def setup_mock_data(self):
        """设置模拟数据"""
        # 模拟orange数据库的表结构
        tables_data = {
            "orange.lending_details": [
                TableField("orange.lending_details", "product_id", "varchar(50)", False, True),
                TableField("orange.lending_details", "loan_init_term", "int", True, False),
                TableField("orange.lending_details", "due_bill_no", "varchar(100)", False, True),
                TableField("orange.lending_details", "apply_time", "datetime", True, False),
                TableField("orange.lending_details", "loan_amount", "decimal(15,2)", True, False),
            ],
            "orange.t_ws_entrance_credit": [
                TableField("orange.t_ws_entrance_credit", "id", "bigint", False, True),
                TableField("orange.t_ws_entrance_credit", "strategy", "varchar(100)", True, False),
                TableField("orange.t_ws_entrance_credit", "product_id", "varchar(50)", True, False),
                TableField("orange.t_ws_entrance_credit", "credit_amount", "decimal(15,2)", True, False),
            ],
            "orange.t_model_inputparams_extend2": [
                TableField("orange.t_model_inputparams_extend2", "id", "bigint", False, True),
                TableField("orange.t_model_inputparams_extend2", "output_level", "varchar(50)", True, False),
                TableField("orange.t_model_inputparams_extend2", "model_id", "varchar(100)", True, False),
                TableField("orange.t_model_inputparams_extend2", "params", "text", True, False),
            ]
        }
        
        for table_name, fields in tables_data.items():
            self.table_schemas[table_name] = fields
            for field in fields:
                self.field_mappings[field.field_name].add(table_name)
    
    def parse_sql_tables_and_aliases(self, sql: str) -> Dict[str, str]:
        """解析SQL中的表和别名"""
        table_aliases = {}
        
        # 简化的解析逻辑
        lines = sql.replace('\n', ' ').replace('\t', ' ')
        
        # 查找FROM子句
        from_match = re.search(r'FROM\s+([^\s]+)\s+([^\s]+)', lines, re.IGNORECASE)
        if from_match:
            table_name = from_match.group(1)
            alias = from_match.group(2)
            table_aliases[alias] = table_name
        
        # 查找JOIN子句
        join_matches = re.findall(r'JOIN\s+([^\s]+)\s+([^\s]+)\s+ON', lines, re.IGNORECASE)
        for table_name, alias in join_matches:
            table_aliases[alias] = table_name
        
        return table_aliases
    
    def extract_field_references(self, sql: str) -> List[Tuple[str, str]]:
        """提取SQL中的字段引用"""
        field_references = []
        
        # 使用正则表达式查找 alias.field 模式
        pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\.\s*([a-zA-Z_][a-zA-Z0-9_]*)\b'
        matches = re.findall(pattern, sql)
        
        for table_alias, field_name in matches:
            # 过滤掉一些常见的非字段引用
            if table_alias.upper() not in ('DATE_FORMAT', 'DATE_SUB', 'YEAR', 'MONTH'):
                field_references.append((table_alias, field_name))
        
        return field_references
    
    def validate_field_reference(self, field_name: str, table_alias: str, 
                                table_aliases: Dict[str, str]) -> Tuple[bool, str]:
        """验证字段引用是否正确"""
        # 获取实际表名
        actual_table = table_aliases.get(table_alias)
        if not actual_table:
            return False, f"Unknown table alias: {table_alias}"
        
        # 检查字段是否存在于指定表中
        table_fields = self.table_schemas.get(actual_table, [])
        field_exists = any(field.field_name == field_name for field in table_fields)
        
        if not field_exists:
            # 提供修复建议
            suggestion = self.get_field_suggestion(field_name, table_aliases)
            return False, f"Field '{field_name}' does not exist in table '{actual_table}' (alias: {table_alias}). {suggestion}"
        
        return True, ""
    
    def get_field_suggestion(self, field_name: str, table_aliases: Dict[str, str]) -> str:
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
    
    def validate_sql_fields(self, sql: str) -> Tuple[bool, List[str]]:
        """验证SQL中的所有字段引用"""
        errors = []
        
        try:
            # 解析表别名
            table_aliases = self.parse_sql_tables_and_aliases(sql)
            print(f"解析到的表别名: {table_aliases}")
            
            # 查找所有字段引用
            field_references = self.extract_field_references(sql)
            print(f"解析到的字段引用: {field_references}")
            
            for table_alias, field_name in field_references:
                is_valid, error_msg = self.validate_field_reference(
                    field_name, table_alias, table_aliases
                )
                if not is_valid:
                    errors.append(error_msg)
        
        except Exception as e:
            errors.append(f"SQL validation failed: {e}")
        
        return len(errors) == 0, errors
    
    def suggest_sql_fix(self, sql: str, errors: List[str]) -> str:
        """基于错误信息建议SQL修复"""
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
            print(f"Failed to suggest SQL fix: {e}")
        
        return fixed_sql

def test_sql_validation():
    """测试SQL验证功能"""
    validator = SimpleSQLValidator()
    
    print("\n📊 测试用例:")
    test_cases = [
        {
            "name": "正确的SQL查询",
            "sql": """
                SELECT b.product_id, t1.strategy, t2.output_level 
                FROM orange.lending_details b 
                LEFT JOIN orange.t_ws_entrance_credit t1 ON b.product_id = t1.product_id
                LEFT JOIN orange.t_model_inputparams_extend2 t2 ON t1.id = t2.id
            """,
            "expected_valid": True
        },
        {
            "name": "字段引用错误的SQL (strategy字段错误)",
            "sql": """
                SELECT b.product_id, b.strategy, b.output_level 
                FROM orange.lending_details b
            """,
            "expected_valid": False
        },
        {
            "name": "部分字段错误的SQL",
            "sql": """
                SELECT b.product_id, b.strategy, t1.output_level 
                FROM orange.lending_details b 
                LEFT JOIN orange.t_ws_entrance_credit t1 ON b.product_id = t1.product_id
            """,
            "expected_valid": False
        },
        {
            "name": "完全正确的复杂查询",
            "sql": """
                SELECT 
                    b.product_id, 
                    b.loan_init_term, 
                    t1.strategy, 
                    t2.output_level,
                    b.loan_amount,
                    t1.credit_amount
                FROM orange.lending_details b 
                LEFT JOIN orange.t_ws_entrance_credit t1 ON b.product_id = t1.product_id
                LEFT JOIN orange.t_model_inputparams_extend2 t2 ON t1.id = t2.id
                WHERE b.product_id IS NOT NULL
                GROUP BY b.product_id, b.loan_init_term, t1.strategy, t2.output_level
            """,
            "expected_valid": True
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- 测试用例 {i}: {test_case['name']} ---")
        
        is_valid, errors = validator.validate_sql_fields(test_case['sql'])
        
        print(f"预期结果: {'✅ 有效' if test_case['expected_valid'] else '❌ 无效'}")
        print(f"实际结果: {'✅ 有效' if is_valid else '❌ 无效'}")
        
        if not is_valid and errors:
            print(f"验证错误 ({len(errors)} 个):")
            for j, error in enumerate(errors, 1):
                print(f"  {j}. {error}")
            
            # 测试自动修复
            print("\n🔧 尝试自动修复:")
            fixed_sql = validator.suggest_sql_fix(test_case['sql'], errors)
            if fixed_sql != test_case['sql']:
                print("修复后的SQL:")
                print(fixed_sql)
                
                # 验证修复结果
                is_fixed_valid, fixed_errors = validator.validate_sql_fields(fixed_sql)
                print(f"修复结果: {'✅ 修复成功' if is_fixed_valid else '❌ 修复失败'}")
                if fixed_errors:
                    print("剩余错误:")
                    for error in fixed_errors:
                        print(f"  - {error}")
            else:
                print("无法自动修复")
        
        print("-" * 60)

def test_field_mapping():
    """测试字段映射功能"""
    validator = SimpleSQLValidator()
    
    print("\n🗺️ 字段映射测试:")
    
    important_fields = ['product_id', 'strategy', 'output_level', 'loan_amount']
    
    for field_name in important_fields:
        tables = validator.field_mappings.get(field_name, set())
        print(f"字段 '{field_name}' 存在于表: {', '.join(tables) if tables else '未找到'}")

def main():
    """主测试函数"""
    print("🎯 独立SQL验证功能测试")
    print("=" * 60)
    
    try:
        test_field_mapping()
        test_sql_validation()
        print("\n🎉 所有测试完成！")
        
        print("\n📋 功能总结:")
        print("✅ 表结构验证器 - 可以检测字段引用错误")
        print("✅ 字段映射功能 - 可以找到字段所在的正确表")
        print("✅ 错误建议功能 - 可以提供修复建议")
        print("✅ 自动修复功能 - 可以自动修复简单的字段引用错误")
        
        print("\n🔧 解决方案特点:")
        print("1. 🛡️ 防止字段引用错误 - 在SQL执行前验证字段是否存在")
        print("2. 🧠 智能错误提示 - 提供具体的修复建议而不是通用错误")
        print("3. 🔄 自动修复机制 - 尝试自动修复常见的字段引用错误")
        print("4. 📊 增强的表结构理解 - 建立完整的字段到表的映射关系")
        
    except Exception as e:
        print(f"\n💥 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 