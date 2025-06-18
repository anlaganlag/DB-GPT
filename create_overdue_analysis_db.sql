-- Create overdue analysis tables in test database
-- Based on the project documentation and configuration

USE test;

-- Customer information table
CREATE TABLE IF NOT EXISTS `customer_info` (
    `customer_id` VARCHAR(50),
    `customer_name` VARCHAR(100),
    `age` INT,
    `gender` VARCHAR(10),
    `education` VARCHAR(50),
    `occupation` VARCHAR(100),
    `monthly_income` DECIMAL(15,2),
    `credit_score` INT,
    `province` VARCHAR(50),
    `city` VARCHAR(50),
    `created_at` DATETIME
) DISTRIBUTED BY HASH(`customer_id`) BUCKETS 1
PROPERTIES ("replication_num" = "1");

-- Loan information table
CREATE TABLE IF NOT EXISTS `loan_info` (
    `loan_id` VARCHAR(50),
    `customer_id` VARCHAR(50),
    `loan_amount` DECIMAL(15,2),
    `loan_date` DATE,
    `loan_term` INT,
    `interest_rate` DECIMAL(5,4),
    `product_type` VARCHAR(50),
    `status` VARCHAR(20),
    `created_at` DATETIME
) DISTRIBUTED BY HASH(`loan_id`) BUCKETS 1
PROPERTIES ("replication_num" = "1");

-- Lending details table (repayment details)
CREATE TABLE IF NOT EXISTS `lending_details` (
    `id` INT,
    `loan_id` VARCHAR(50),
    `loan_date` DATE,
    `loan_amount` DECIMAL(15,2),
    `interest_rate` DECIMAL(5,4),
    `customer_id` VARCHAR(50),
    `period_number` INT,
    `due_date` DATE,
    `principal_amount` DECIMAL(15,2),
    `interest_amount` DECIMAL(15,2),
    `paid_principal` DECIMAL(15,2),
    `paid_interest` DECIMAL(15,2),
    `remaining_principal` DECIMAL(15,2),
    `payment_date` DATE,
    `dpd_days` INT,
    `status` VARCHAR(20),
    `created_at` DATETIME
) DISTRIBUTED BY HASH(`loan_id`) BUCKETS 1
PROPERTIES ("replication_num" = "1");

-- Overdue rate statistics table
CREATE TABLE IF NOT EXISTS `overdue_rate_stats` (
    `id` INT,
    `stat_date` DATE,
    `loan_month` VARCHAR(7),
    `mob` INTEGER,
    `total_loans` INTEGER,
    `total_amount` DECIMAL(15, 2),
    `overdue_loans` INTEGER,
    `overdue_amount` DECIMAL(15, 2),
    `overdue_rate` DECIMAL(8, 4),
    `dpd_threshold` INTEGER,
    `created_at` DATETIME
) DISTRIBUTED BY HASH(`loan_month`) BUCKETS 1
PROPERTIES ("replication_num" = "1");

-- Risk factor analysis table
CREATE TABLE IF NOT EXISTS `risk_factor_analysis` (
    `id` INT,
    `analysis_date` DATE,
    `factor_type` VARCHAR(50),
    `factor_value` VARCHAR(100),
    `total_loans` INTEGER,
    `overdue_loans` INTEGER,
    `overdue_rate` DECIMAL(8, 4),
    `avg_loan_amount` DECIMAL(15, 2),
    `created_at` DATETIME
) DISTRIBUTED BY HASH(`factor_type`) BUCKETS 1
PROPERTIES ("replication_num" = "1");
