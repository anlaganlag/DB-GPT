# DB-GPT数据库字段异常分析与解决方案

## 异常概述

在DB-GPT系统运行过程中，发现了数据库字段引用异常的问题。本文档详细分析了异常原因并提供了相应的解决方案。

## 异常详情

### 错误信息
```pymysql.err.OperationalError) (1054, "errCode = 2, detailMessage = Unknown column 'overdue_amount' in 'table list'")
```

### 问题SQL
```sql
SELECT 
    (SUM(CASE WHEN project_id = 'project_A' AND DATE_FORMAT(loan_active_date, '%Y-%m') = '2025-06' AND overdue_amount > 0 THEN overdue_amount ELSE 0 END) / 
     SUM(CASE WHEN project_id = 'project_A' AND DATE_FORMAT(loan_active_date, '%Y-%m') = '2025-06' THEN loan_init_principal ELSE 0 END)) * 100 AS '项目A逾期率',
    (SUM(CASE WHEN project_id != 'project_A' AND DATE_FORMAT(loan_active_date, '%Y-%m') = '2025-06' AND overdue_amount > 0 THEN overdue_amount ELSE 0 END) / 
     SUM(CASE WHEN project_id != 'project_A' AND DATE_FORMAT(loan_active_date, '%Y-%m') = '2025-06' THEN loan_init_principal ELSE 0 END)) * 100 AS '其他项目逾期率' 
FROM loan_info
```

## 问题分析

### 1. 根本原因
- **字段不存在错误**：SQL查询中引用了 `overdue_amount` 字段，但在 `loan_info` 表中实际不存在这个字段
- **字段映射问题**：`loan_init_principal` 字段可能也不存在于实际表结构中
- **LLM生成错误**：AI根据假设的字段结构生成了SQL，但与实际数据库结构不匹配

### 2. 影响范围
- 查询执行失败
- 用户体验下降
- 业务分析中断

## 解决方案

### 1. 改进表结构信息传递

#### 目标
确保LLM获得准确完整的表结构信息

#### 实施方案
- **完整字段列表**：提供所有可用的字段名
- **字段类型说明**：包含字段数据类型信息
- **字段含义注释**：添加业务含义说明
- **示例数据**：提供字段的示例值

#### 代码示例
```python
def get_enhanced_table_info(table_name):
    return {
        'table_name': table_name,
        'fields': [
            {
                'name': 'project_id', 
                'type': 'VARCHAR(50)', 
                'description': '项目标识符',
                'example': 'project_001'
            },
            {
                'name': 'loan_active_date', 
                'type': 'DATE', 
                'description': '放款激活日期',
                'example': '2024-01-15'
            },
            # 更多字段...
        ]
    }
```

### 2. 增强字段映射逻辑

#### 业务概念到字段映射表
| 业务概念 | 实际字段名 | 计算方式 |
|---------|-----------|---------|
| 逾期金额 | `remain_principal` | 剩余本金作为逾期金额 |
| 初始本金 | `loan_init_principal` | 如不存在，使用相关字段 |
| 逾期状态 | `dpd_days` | 通过逾期天数判断 |

#### 实施代码
```python
FIELD_MAPPING = {
    'overdue_amount': {
        'alternatives': ['remain_principal', 'overdue_principal'],
        'calculation': 'CASE WHEN dpd_days > 0 THEN remain_principal ELSE 0 END'
    },
    'loan_init_principal': {
        'alternatives': ['initial_amount', 'loan_amount'],
        'calculation': 'loan_amount'
    }
}
```

### 3. 添加字段验证机制

#### 验证流程
1. **SQL解析**：提取SQL中引用的所有字段
2. **字段检查**：对比实际表结构
3. **错误提示**：列出缺失字段
4. **建议替代**：提供可能的替代字段

#### 实现代码
```python
def validate_sql_fields(sql, table_schema):
    """验证SQL中的字段是否存在"""
    referenced_fields = extract_fields_from_sql(sql)
    available_fields = set(table_schema.get_field_names())
    missing_fields = referenced_fields - available_fields
    
    if missing_fields:
        suggestions = suggest_alternative_fields(missing_fields, available_fields)
        raise FieldValidationError(
            f"Missing fields: {missing_fields}",
            suggestions=suggestions
        )
    
    return True

def suggest_alternative_fields(missing_fields, available_fields):
    """建议替代字段"""
    suggestions = {}
    for missing_field in missing_fields:
        # 基于字段名相似度或业务逻辑映射
        suggestions[missing_field] = find_similar_fields(missing_field, available_fields)
    return suggestions
```

### 4. 改进错误处理

#### 智能错误恢复
```python
def handle_field_error(error, sql, table_schema):
    """处理字段不存在错误"""
    if "Unknown column" in str(error):
        # 提取错误字段名
        missing_field = extract_field_from_error(error)
        
        # 查找替代字段
        alternative = find_alternative_field(missing_field, table_schema)
        
        if alternative:
            # 自动替换并重新执行
            corrected_sql = sql.replace(missing_field, alternative)
            return execute_corrected_sql(corrected_sql)
        else:
            # 提供用户友好的错误信息
            return generate_helpful_error_message(missing_field, table_schema)
```

### 5. 增强Prompt模板

#### 新增规则
在prompt模板中添加以下约束：

```markdown
**字段使用约束：**
1. 只能使用表结构定义中明确存在的字段
2. 禁止假设或创造不存在的字段名
3. 如需计算衍生指标，必须基于现有字段构建

**逾期率计算指导：**
- 逾期金额：使用 `remain_principal` 字段结合 `dpd_days > 0` 条件
- 总放款金额：使用实际存在的本金字段
- 逾期率公式：(逾期金额 / 总放款金额) * 100

**字段映射参考：**
- 项目ID: `project_id`
- 放款日期: `loan_active_date` 
- 剩余本金: `remain_principal`
- 逾期天数: `dpd_days`
```

### 6. 实时表结构同步

#### 同步机制
```python
class TableSchemaManager:
    def __init__(self, database_connector):
        self.db = database_connector
        self.schema_cache = {}
        self.last_update = {}
    
    def get_current_schema(self, table_name):
        """获取最新的表结构"""
        if self.need_refresh(table_name):
            self.refresh_schema(table_name)
        return self.schema_cache[table_name]
    
    def refresh_schema(self, table_name):
        """刷新表结构缓存"""
        schema = self.db.get_table_schema(table_name)
        self.schema_cache[table_name] = schema
        self.last_update[table_name] = datetime.now()
    
    def need_refresh(self, table_name):
        """判断是否需要刷新"""
        if table_name not in self.last_update:
            return True
        return (datetime.now() - self.last_update[table_name]).seconds > 3600
```

## 预防措施

### 1. 定期表结构审查
- 每周检查表结构变更
- 及时更新字段映射表
- 验证prompt模板的准确性

### 2. 测试用例完善
```python
def test_field_validation():
    """测试字段验证功能"""
    test_cases = [
        {
            'sql': "SELECT overdue_amount FROM loan_info",
            'expected_error': "Unknown column 'overdue_amount'",
            'expected_suggestion': "remain_principal"
        },
        # 更多测试用例...
    ]
    
    for case in test_cases:
        result = validate_sql_fields(case['sql'], table_schema)
        assert result.error == case['expected_error']
        assert case['expected_suggestion'] in result.suggestions
```

### 3. 监控和告警
- 监控字段错误频率
- 设置异常告警阈值
- 自动生成错误报告

## 总结

通过实施上述解决方案，可以有效避免数据库字段异常问题：

1. **提高准确性**：确保LLM获得正确的表结构信息
2. **增强容错性**：通过字段映射和验证机制减少错误
3. **改善体验**：提供智能错误恢复和友好的错误提示
4. **保证稳定性**：通过实时同步和监控确保系统稳定运行

这些措施将显著提升DB-GPT系统的可靠性和用户体验。 