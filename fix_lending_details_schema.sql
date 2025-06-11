-- 修复lending_details表结构，添加AI查询常用的字段
-- Fix lending_details table schema by adding commonly used fields for AI queries

USE overdue_analysis;

-- 添加loan_date字段（从loan_info表复制）
ALTER TABLE lending_details 
ADD COLUMN loan_date DATE AFTER loan_id,
ADD INDEX idx_loan_date (loan_date);

-- 添加loan_amount字段（从loan_info表复制）
ALTER TABLE lending_details 
ADD COLUMN loan_amount DECIMAL(15,2) AFTER loan_date;

-- 添加interest_rate字段（从loan_info表复制）
ALTER TABLE lending_details 
ADD COLUMN interest_rate DECIMAL(5,4) AFTER loan_amount;

-- 添加customer_id字段（从loan_info表复制）
ALTER TABLE lending_details 
ADD COLUMN customer_id VARCHAR(50) AFTER interest_rate,
ADD INDEX idx_customer_id (customer_id);

-- 更新数据：从loan_info表复制相关字段的值
UPDATE lending_details ld 
JOIN loan_info li ON ld.loan_id = li.loan_id 
SET 
    ld.loan_date = li.loan_date,
    ld.loan_amount = li.loan_amount,
    ld.interest_rate = li.interest_rate,
    ld.customer_id = li.customer_id;

-- 验证数据更新
SELECT 
    COUNT(*) as total_records,
    COUNT(loan_date) as records_with_loan_date,
    COUNT(loan_amount) as records_with_loan_amount,
    MIN(loan_date) as earliest_loan_date,
    MAX(loan_date) as latest_loan_date
FROM lending_details;

-- 显示更新后的表结构
DESCRIBE lending_details; 