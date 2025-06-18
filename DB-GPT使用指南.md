# DB-GPT 逾期率分析操作指南

## ✅ 问题已解决！

通过测试验证，DB-GPT现在可以正常执行SQL查询并生成分析报告。

## 🎯 正确的操作方法

### 方法1：使用API接口（推荐）

#### 基础查询测试
```bash
curl -X POST http://localhost:5670/api/v2/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek",
    "messages": [{"role": "user", "content": "SELECT * FROM loan_info LIMIT 5"}],
    "chat_mode": "chat_data",
    "chat_param": "orange"
  }'
```

#### 逾期率分析查询
```bash
curl -X POST http://localhost:5670/api/v2/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek",
    "messages": [{"role": "user", "content": "SELECT substr(loan_active_date, 1, 7) AS loan_month, product_id, COUNT(*) AS nbr_bills FROM loan_info WHERE loan_active_date >= '\''2024-01-01'\'' GROUP BY substr(loan_active_date, 1, 7), product_id ORDER BY loan_month LIMIT 20"}],
    "chat_mode": "chat_data",
    "chat_param": "orange"
  }'
```

#### 复杂逾期率分析（你的原始查询简化版）
```bash
curl -X POST http://localhost:5670/api/v2/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek",
    "messages": [{"role": "user", "content": "SELECT substr(loan_active_date, 1, 7) AS loan_month, b.product_id, loan_init_term, COUNT(1) AS nbr_bills FROM lending_details b JOIN loan_info c ON b.due_bill_no = c.due_bill_no AND b.project_id = c.project_id WHERE is_lend=1 AND loan_active_date >= '\''2024-01-01'\'' GROUP BY substr(loan_active_date, 1, 7), b.product_id, loan_init_term ORDER BY loan_month LIMIT 50"}],
    "chat_mode": "chat_data",
    "chat_param": "orange"
  }'
```

### 方法2：使用Web界面

1. **打开浏览器访问：** http://localhost:5670
2. **选择正确的聊天模式：** `chat_data`（数据分析模式）
3. **选择数据库：** `orange`
4. **输入SQL查询**

## 📊 测试结果示例

刚才的测试返回了以下数据：

| loan_month | product_id | nbr_bills |
|------------|------------|-----------|
| 2024-01 | product_001 | 23,590 |
| 2024-02 | product_001 | 78,704 |
| 2024-03 | product_001 | 14,238 |
| 2024-06 | product_001 | 1,315,264 |
| 2024-07 | product_001 | 2,337,215 |

## ⚠️ 关键要点

### ✅ 正确配置
- **端口：** 5670
- **聊天模式：** `chat_data`
- **数据库参数：** `orange`
- **API路径：** `/api/v2/chat/completions`

### ❌ 避免的错误
- ~~使用 `chat_with_db_execute` 模式~~
- ~~缺少 `chat_param` 参数~~
- ~~使用错误端口 5000~~

## 🔧 SQL查询建议

### 1. 基础逾期率分析
```sql
SELECT 
  substr(loan_active_date, 1, 7) AS loan_month,
  product_id,
  COUNT(*) AS total_loans,
  SUM(CASE WHEN dpd_days > 0 THEN 1 ELSE 0 END) AS overdue_loans,
  ROUND(SUM(CASE WHEN dpd_days > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS overdue_rate
FROM loan_info 
WHERE loan_active_date >= '2024-01-01'
GROUP BY substr(loan_active_date, 1, 7), product_id
ORDER BY loan_month
LIMIT 50;
```

### 2. 按逾期天数分类
```sql
SELECT 
  substr(loan_active_date, 1, 7) AS loan_month,
  CASE 
    WHEN dpd_days = 0 THEN '正常'
    WHEN dpd_days BETWEEN 1 AND 30 THEN '1-30天'
    WHEN dpd_days BETWEEN 31 AND 90 THEN '31-90天'
    ELSE '90天以上'
  END AS overdue_category,
  COUNT(*) AS loan_count
FROM loan_info 
WHERE loan_active_date >= '2024-01-01'
GROUP BY substr(loan_active_date, 1, 7), 
  CASE 
    WHEN dpd_days = 0 THEN '正常'
    WHEN dpd_days BETWEEN 1 AND 30 THEN '1-30天'
    WHEN dpd_days BETWEEN 31 AND 90 THEN '31-90天'
    ELSE '90天以上'
  END
ORDER BY loan_month
LIMIT 50;
```

## 📈 系统功能

现在你可以：
- ✅ 执行复杂SQL查询
- ✅ 获得格式化的表格结果
- ✅ 自动生成分析报告
- ✅ 查看执行的SQL语句
- ✅ 获得业务洞察和建议

## 🎉 下一步操作

1. **测试基础查询** - 确认系统工作正常
2. **执行逾期率分析** - 使用上面的SQL模板
3. **生成报告** - 系统会自动生成分析报告
4. **导出结果** - 可以复制结果用于进一步分析

现在你的DB-GPT系统已经完全正常工作了！ 