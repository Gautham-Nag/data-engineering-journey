# Lakehouse vs Warehouse

## Use Lakehouse when
- Data comes from files (CSV, JSON, Parquet)
- You need Spark notebooks
- You want ML or feature engineering
- You want Direct Lake access for Power BI

## Use Warehouse when
- Data is already relational
- Workload is SQL-heavy
- You want fastest report queries
- You need strict governance and constraints

## Do NOT use Lakehouse when
- Only analysts are querying
- No Spark or ML usage
- Schema is fixed and relational

## Do NOT use Warehouse when
- Data is semi-structured
- Transformations require Spark
- ML training or scoring is required

## Mental model
Lakehouse = workshop (build + experiment)  
Warehouse = showroom (fast, clean reporting)

## Exam signal
If the question mentions **Spark, ML, files, or Direct Lake** → Lakehouse  
If the question mentions **performance, SQL, reporting** → Warehouse
