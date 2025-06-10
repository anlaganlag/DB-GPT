# 改进的SQL生成Prompt模板

## 核心原则
为了避免"Generate view content failed"错误，AI模型在生成SQL时必须遵循以下原则：

### 1. 字段别名一致性原则
- **禁止在CTE中使用中文别名后在主查询中引用英文字段名**
- 如果在CTE中使用了 `field AS '中文别名'`，在主查询中必须引用 `'中文别名'` 而不是 `field`
- 推荐：在CTE中不使用中文别名，或者在主查询中正确引用中文别名

### 2. 中文字段名处理原则
- 所有包含中文的字段名或别名必须用反引号包围：`` `中文字段名` ``
- 避免在复杂查询中使用中文别名，优先使用英文别名

### 3. SQL结构简化原则
- 优先生成简单的单表查询
- 避免不必要的复杂JOIN操作
- 如果需要多表关联，确保JOIN条件正确且字段引用明确

## 改进的Prompt模板

```
请根据用户选择的数据库和该库的部分可用表结构定义来回答用户问题.

数据库名: {database_name}
表结构定义: {table_definitions}

**重要的SQL生成规则**:
1. 字段别名一致性: 如果在子查询或CTE中使用了别名，在外层查询中必须引用别名而不是原字段名
2. 中文字段处理: 包含中文的字段名必须用反引号包围，如 `中文字段名`
3. 简化优先: 优先生成简单查询，避免不必要的复杂JOIN
4. 验证字段存在性: 确保引用的字段在对应的表中存在
5. 限制结果数量: 除非用户指定，否则始终添加 LIMIT 50

**错误避免指南**:
- ❌ 错误示例: WITH cte AS (SELECT field AS '别名' FROM table) SELECT m.field FROM cte m
- ✅ 正确示例: WITH cte AS (SELECT field AS '别名' FROM table) SELECT m.`别名` FROM cte m
- ❌ 错误示例: SELECT 中文字段 FROM table
- ✅ 正确示例: SELECT `中文字段` FROM table

约束:
1. 请根据用户问题理解用户意图，使用给出表结构定义创建一个语法正确的mysql sql，如果不需要sql，则直接回答用户问题。
2. 除非用户在问题中指定了他希望获得的具体数据行数，否则始终将查询限制为最多 50 个结果。
3. 只能使用表结构信息中提供的表来生成 sql，如果无法根据提供的表结构中生成 sql，请说："提供的表结构信息不足以生成 sql 查询。" 禁止随意捏造信息。
4. 请注意生成SQL时不要弄错表和列的关系
5. 请检查SQL的正确性，并保证正确的情况下优化查询性能
6. 请从如下给出的展示方式种选择最优的一种用以进行数据渲染，将类型名称放入返回要求格式的name参数值种，如果找不到最合适的则使用'Table'作为展示方式

可用数据展示方式:
- response_line_chart: 用于显示比较趋势分析数据
- response_pie_chart: 适用于比例和分布统计场景
- response_table: 适用于多列显示或非数值列的展示
- response_scatter_chart: 适用于探索变量间关系、检测异常值等
- response_bubble_chart: 适用于多变量关系、突出异常值或特殊情况等
- response_donut_chart: 适用于层次结构表示、类别比例显示和突出关键类别等
- response_area_chart: 适用于时间序列数据可视化、多组数据比较、数据变化趋势分析等
- response_heatmap: 适用于时间序列数据、大规模数据集、分类数据分布的可视化分析等

用户问题: {user_question}

请一步步思考并按照以下JSON格式回复：
{
    "thoughts": "思考总结，说明给用户听",
    "direct_response": "如果上下文足够回答用户，直接回复而不需要sql",
    "sql": "要运行的SQL查询",
    "display_type": "数据显示方法"
}

确保返回正确的json并且可以被Python json.loads方法解析.
**特别注意**: 不要在响应中包含 <think> 标签，直接返回JSON格式的响应。
```

## 常见错误模式及修复

### 错误模式1: CTE别名不匹配
```sql
-- 错误的SQL
WITH monthly_data AS (
    SELECT loan_month AS '贷款月份', overdue_rate AS '逾期率' 
    FROM overdue_rate_stats
)
SELECT m.loan_month, m.overdue_rate FROM monthly_data m

-- 修复后的SQL
WITH monthly_data AS (
    SELECT loan_month AS '贷款月份', overdue_rate AS '逾期率' 
    FROM overdue_rate_stats
)
SELECT m.`贷款月份`, m.`逾期率` FROM monthly_data m
```

### 错误模式2: 中文字段名未加引号
```sql
-- 错误的SQL
SELECT 贷款月份, 逾期率 FROM overdue_rate_stats GROUP BY 贷款月份

-- 修复后的SQL
SELECT `贷款月份`, `逾期率` FROM overdue_rate_stats GROUP BY `贷款月份`
```

### 错误模式3: 复杂JOIN中的字段引用错误
```sql
-- 错误的SQL (字段不存在或引用错误)
SELECT m.loan_month FROM monthly_overdue m 
LEFT JOIN lending_details ld ON m.loan_month = ld.loan_month

-- 修复后的SQL (确保字段存在且引用正确)
SELECT m.`贷款月份` FROM monthly_overdue m 
LEFT JOIN lending_details ld ON m.loan_id = ld.loan_id
``` 