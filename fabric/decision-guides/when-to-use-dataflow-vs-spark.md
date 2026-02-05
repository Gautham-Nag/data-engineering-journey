# Dataflow vs Spark

## Use Dataflow when
- Source is SaaS or relational (CRM, SQL, Excel)
- Transformations are simple and repeatable
- Low-code ingestion is preferred
- Analysts or analytics engineers own the pipeline

## Use Spark when
- Data volume is large
- Data is semi-structured or unstructured
- Complex transformations are required
- ML training or feature engineering is needed

## Do NOT use Dataflow when
- Logic is complex or iterative
- Performance tuning is required
- ML or advanced processing is involved

## Do NOT use Spark when
- Simple ingestion and cleansing is enough
- Low-code tools are sufficient
- Business users maintain pipelines

## Mental model
Dataflow = conveyor belt (simple, repeatable moves)  
Spark = factory (custom, heavy processing)

## Exam signal
If the question mentions **low-code, Power Query, ingestion** → Dataflow  
If the question mentions **big data, ML, complex logic** → Spark
