# Pipeline vs Dataflow vs Notebook

## Use Pipeline when
- You need orchestration and scheduling
- Multiple steps must run in sequence
- You want to trigger Dataflows, Notebooks, or Copy activities
- Control flow (if/else, retries) is required

## Use Dataflow when
- Data ingestion and transformation is simple
- Power Query (low-code) is sufficient
- Analysts or analytics engineers maintain logic
- Source is SaaS, SQL, or files

## Use Notebook when
- Transformations are complex
- Spark processing is required
- ML training or scoring is needed
- You need full programming control

## Do NOT use Pipeline when
- You need heavy data transformation
- You need row-level logic or joins

## Do NOT use Dataflow when
- Logic is complex or iterative
- Performance tuning is required
- ML or advanced processing is needed

## Do NOT use Notebook when
- Simple ingestion and cleansing is enough
- Low-code tools are preferred
- Business users own the pipeline

## Mental model
Pipeline = conductor (controls the flow)  
Dataflow = cleaner (simple transformations)  
Notebook = engine (heavy processing)

## Exam signal
If the question mentions **orchestration, scheduling, sequence** → Pipeline  
If the question mentions **Power Query, low-code ingestion** → Dataflow  
If the question mentions **Spark, ML, complex logic** → Notebook
