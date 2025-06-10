# DB-GPT SQL列错误修复指南

## 问题描述
当用户询问"帮我分析逾期率"等业务问题时，DB-GPT现在会智能分析缺少的信息并主动引导用户，而不是简单拒绝。

## 改进内容

### 1. 智能需求分析
DB-GPT现在会：
- 分析用户的具体业务目标
- 识别当前表结构中缺少的关键字段
- 主动提示需要的额外信息
- 建议可能的解决方案

### 2. 常见业务场景处理

#### 逾期率分析场景
**用户问题**: "帮我分析逾期率"

**AI智能响应示例**:
```json
{
    "thoughts": "用户想要分析逾期率，这是一个金融业务分析需求。我需要分析当前表结构是否支持这个分析。",
    "direct_response": "我理解您想要分析逾期率。基于当前的表结构，我发现缺少以下关键信息来进行逾期率分析：\n\n**缺少的关键字段：**\n1. 逾期相关字段：如 `overdue_days`（逾期天数）、`is_overdue`（是否逾期）\n2. 日期字段：如 `due_date`（到期日期）、`payment_date`（还款日期）\n3. 金额字段：如 `overdue_amount`（逾期金额）、`principal_amount`（本金金额）\n\n**建议的解决方案：**\n1. 如果您有专门的逾期分析数据库，请切换到该数据库\n2. 如果当前表结构可以推算逾期信息，请告诉我：\n   - 如何定义逾期（如：超过30天未还款）\n   - 哪个字段表示还款状态\n   - 哪个字段表示订单/贷款日期\n3. 我可以先帮您分析现有的订单状态分布作为替代\n\n**您可以尝试这样问：**\n- \"查询orders表中status为'pending'的订单，这些可能是逾期订单\"\n- \"统计orders表中不同status的订单数量和金额分布\"\n- \"分析orders表中订单从创建到现在的天数分布\"",
    "sql": "",
    "display_type": "response_table",
    "missing_info": "需要逾期相关字段（overdue_days, is_overdue）、日期字段（due_date, payment_date）、金额字段（overdue_amount, principal_amount）来进行准确的逾期率分析"
}
```

#### 销售分析场景
**用户问题**: "分析销售趋势"

**AI智能响应示例**:
```json
{
    "thoughts": "用户想要分析销售趋势，需要时间序列数据和销售金额数据。",
    "direct_response": "我理解您想要分析销售趋势。基于当前表结构，我可以帮您分析订单趋势：\n\n**可用的分析维度：**\n1. 订单金额趋势：基于 `total_amount` 字段\n2. 订单数量趋势：基于订单记录数\n3. 时间维度：基于 `order_date` 字段\n\n**建议的具体查询：**\n- \"按月统计orders表的订单数量和总金额\"\n- \"查询最近30天的订单趋势\"\n- \"分析不同status的订单金额分布\"\n\n**如果需要更详细的销售分析，请提供：**\n- 产品销售明细（product_sales表）\n- 客户分类信息\n- 地区销售数据",
    "sql": "",
    "display_type": "response_line_chart",
    "missing_info": "当前表结构支持基础订单趋势分析，如需详细销售分析需要产品销售明细表"
}
```

### 3. 用户指导模板

#### 如何更好地描述需求

**✅ 推荐的问法**:
```
具体业务场景 + 明确的数据需求 + 期望的分析维度

示例：
- "基于orders表，按月统计订单金额趋势，显示最近6个月的数据"
- "分析customers表中不同地区的客户分布情况"
- "查询products表中库存不足（stock_quantity < 10）的产品信息"
```

**❌ 避免的问法**:
```
- "帮我分析一下"
- "看看数据情况"
- "做个报表"
```

#### 逐步引导流程

**第一步：明确业务目标**
```
请告诉我：
1. 您想要分析什么业务指标？
2. 分析的时间范围是什么？
3. 需要按什么维度分组？
```

**第二步：确认数据来源**
```
请确认：
1. 数据在哪个表中？
2. 关键字段的名称是什么？
3. 是否需要关联多个表？
```

**第三步：定义计算逻辑**
```
请说明：
1. 如何计算目标指标？
2. 是否有特殊的筛选条件？
3. 期望的输出格式是什么？
```

### 4. 常见缺失信息类型

#### 时间相关分析
**缺失信息**:
- 日期字段（创建时间、更新时间、到期时间）
- 时间格式说明
- 分析时间范围

**解决方案**:
```sql
-- 如果有created_at字段，可以分析时间趋势
SELECT 
    DATE_FORMAT(created_at, '%Y-%m') as month,
    COUNT(*) as order_count,
    SUM(total_amount) as total_amount
FROM orders 
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
GROUP BY DATE_FORMAT(created_at, '%Y-%m')
ORDER BY month;
```

#### 业务状态分析
**缺失信息**:
- 状态字段的具体含义
- 业务流程定义
- 异常状态识别

**解决方案**:
```sql
-- 先分析现有状态分布
SELECT 
    status,
    COUNT(*) as count,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() as percentage
FROM orders 
GROUP BY status
ORDER BY count DESC;
```

#### 金额相关分析
**缺失信息**:
- 金额字段类型（总金额、净金额、税额）
- 币种信息
- 计算规则

**解决方案**:
```sql
-- 分析金额分布
SELECT 
    CASE 
        WHEN total_amount < 100 THEN '小额订单'
        WHEN total_amount < 1000 THEN '中等订单'
        ELSE '大额订单'
    END as amount_range,
    COUNT(*) as order_count,
    SUM(total_amount) as total_amount
FROM orders 
GROUP BY 
    CASE 
        WHEN total_amount < 100 THEN '小额订单'
        WHEN total_amount < 1000 THEN '中等订单'
        ELSE '大额订单'
    END;
```

### 5. 智能建议系统

#### 基于表结构的自动建议
```python
def suggest_analysis_based_on_schema(table_info):
    suggestions = []
    
    # 检查时间字段
    if 'created_at' in table_info or 'order_date' in table_info:
        suggestions.append("时间趋势分析：按日/月/年统计数据变化")
    
    # 检查金额字段
    if 'total_amount' in table_info or 'amount' in table_info:
        suggestions.append("金额分析：统计总金额、平均金额、金额分布")
    
    # 检查状态字段
    if 'status' in table_info:
        suggestions.append("状态分析：统计不同状态的数量和占比")
    
    # 检查分类字段
    if 'category_id' in table_info or 'type' in table_info:
        suggestions.append("分类分析：按类别统计数据分布")
    
    return suggestions
```

### 6. 错误恢复机制

#### 当信息仍然不足时
```json
{
    "thoughts": "即使经过引导，用户提供的信息仍然不足以生成准确的SQL",
    "direct_response": "感谢您提供的信息。为了给您最准确的分析，我还需要以下具体信息：\n\n**必需信息：**\n1. [具体缺失的字段名]\n2. [业务规则定义]\n3. [计算逻辑说明]\n\n**或者，我可以为您提供以下替代分析：**\n- [基于现有数据的分析选项1]\n- [基于现有数据的分析选项2]\n\n请选择一个替代方案，或提供缺失的信息。",
    "sql": "",
    "display_type": "response_table",
    "missing_info": "具体列出仍然缺失的关键信息"
}
```

### 7. 最佳实践

#### 用户教育
1. **提供示例查询**：展示正确的问法
2. **解释业务逻辑**：说明分析的前提条件
3. **给出替代方案**：当无法满足需求时提供其他选择

#### 系统优化
1. **智能字段映射**：自动识别可能的业务字段
2. **历史查询学习**：基于用户历史查询优化建议
3. **业务模板库**：预定义常见业务分析模板

## 使用效果

### 改进前
```
用户：帮我分析逾期率
AI：提供的表结构信息不足以生成 sql 查询。
```

### 改进后
```
用户：帮我分析逾期率
AI：我理解您想要分析逾期率。基于当前的表结构，我发现缺少以下关键信息...
[详细的指导和建议]
```

这样的改进大大提升了用户体验，将简单的拒绝转变为积极的引导和帮助。 