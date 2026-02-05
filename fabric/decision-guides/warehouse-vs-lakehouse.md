# Warehouse vs Lakehouse

## Use Warehouse when
- Primary users are SQL / Power BI analysts
- Data is structured and relational
- Row-level security (RLS) is required
- Fast, predictable BI query performance is critical

## Use Lakehouse when
- Data engineers and data scientists are primary users
- Data includes structured + semi-structured files
- Spark, notebooks, and ML are required
- Data arrives in large volumes or raw formats

## Do NOT use Warehouse when
- You need Spark notebooks or ML workloads
- Data is semi-structured or unstructured
- You want to store raw + curated layers together

## Do NOT use Lakehouse when
- Analysts need strict SQL governance
- RLS must be enforced at query time
- BI users should not see raw data

## Mental model
Warehouse = curated tables for reporting  
Lakehouse = raw + refined data for engineering and science

## Exam signal
If the question mentions **T-SQL, RLS, Power BI performance** → Warehouse  
If the question mentions **Spark, notebooks, ML, raw data** → Lakehouse
