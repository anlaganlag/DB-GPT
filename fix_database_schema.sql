-- Fix for missing order_date column in orders table
-- Run this SQL script on your database to add the missing column

-- Option 1: Add order_date column with current timestamp as default
ALTER TABLE orders ADD COLUMN order_date DATETIME DEFAULT CURRENT_TIMESTAMP;

-- Option 2: If you have a created_at or similar column, you can rename it
-- ALTER TABLE orders CHANGE COLUMN created_at order_date DATETIME;

-- Option 3: If you want to populate existing records with sample dates
-- UPDATE orders SET order_date = DATE_SUB(NOW(), INTERVAL FLOOR(RAND() * 365) DAY) WHERE order_date IS NULL;

-- Verify the change
DESCRIBE orders; 