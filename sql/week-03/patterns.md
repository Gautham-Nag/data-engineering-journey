Canonical Patterns (Filtering + Aggregations)

-- 1) Filtering: IN over OR chains
SELECT *
FROM students
WHERE location IN ('BANGALORE','HYDERABAD','PUNE');

-- 2) LIKE patterns
-- Starts with J
SELECT *
FROM employees
WHERE first_name LIKE 'J%';

-- Exactly 4 characters
SELECT *
FROM employees
WHERE first_name LIKE '____';

-- Contains 'son'
SELECT *
FROM employees
WHERE first_name LIKE '%son%';

-- Literal % search (escape)
SELECT *
FROM employees
WHERE email LIKE '%\%%';

-- 3) REGEXP patterns
-- Starts with A/B/C/D
SELECT *
FROM employees
WHERE first_name REGEXP '^[ABCD]';

-- Ends with A/B/C/D
SELECT *
FROM employees
WHERE first_name REGEXP '[ABCD]$';

-- 2nd char is vowel
SELECT *
FROM employees
WHERE first_name REGEXP '^.[aeiou]';

-- 4) COUNT differences
SELECT COUNT(*) AS total_rows FROM employees;
SELECT COUNT(manager_id) AS rows_with_manager FROM employees;

-- 5) ORDER BY derived column
SELECT *,
       salary * 1.1 AS revised_salary
FROM employees
ORDER BY revised_salary DESC
LIMIT 5;

-- 6) DISTINCT + ORDER BY safe pattern (use aggregation if you want “best per distinct key”)
SELECT source_of_joining, MAX(years_of_exp) AS max_exp
FROM students
GROUP BY source_of_joining
ORDER BY max_exp DESC;

-- 7) Basic aggregation across full table
SELECT COUNT(*) AS total_orders,
       SUM(amount) AS total_sales,
       MAX(amount) AS max_order_amount,
       MIN(amount) AS min_order_amount,
       AVG(amount) AS avg_order_value
FROM sales;

-- 8) GROUP BY category
SELECT category, SUM(amount) AS total_sales
FROM sales
GROUP BY category;

-- 9) Top 3 products by quantity sold
SELECT product, SUM(quantity) AS total_quantity
FROM sales
GROUP BY product
ORDER BY total_quantity DESC
LIMIT 3;

-- 10) Monthly sales by customer where order count >= 8 (HAVING)
SELECT DATE_FORMAT(sale_date, '%Y-%m') AS sale_month,
       customer_id,
       SUM(amount) AS total_sales,
       COUNT(*) AS num_orders
FROM sales
GROUP BY sale_month, customer_id
HAVING num_orders >= 8;

-- 11) Weekday-only premium customers (aggregate filter)
SELECT customer_id, SUM(amount) AS total_sales
FROM sales
WHERE DAYOFWEEK(sale_date) BETWEEN 2 AND 6
GROUP BY customer_id
HAVING total_sales > 7000;
