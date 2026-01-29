# Spark Execution Model

Apache Spark is designed to process large-scale data reliably and efficiently
across a cluster. Understanding its execution model is critical to reasoning
about performance, scalability, and fault tolerance.

Rather than executing code line by line, Spark converts user logic into an
execution plan that can run in parallel across machines.

## Why an execution model matters
Most performance and correctness issues in Spark do not come from syntax errors,
but from misunderstanding how Spark executes work.

A clear execution model allows engineers to:
- Predict when shuffles occur
- Understand parallelism limits
- Reason about failures and recomputation
- Debug slow or unstable jobs without guessing

## Core execution entities

Spark separates planning from execution using distinct components:

- **Driver**  
  The driver runs the application logic, builds the execution plan (DAG),
  and coordinates work across the cluster.

- **Executors**  
  Executors are long-lived processes that run tasks, store intermediate data,
  and perform computation in parallel.

- **Partitions**  
  Data is divided into partitions. A partition is the smallest unit of data
  processed independently.

- **Tasks**  
  A task processes exactly one partition and is the smallest schedulable unit
  of execution, running on an executor core.

## From code to execution

When Spark code is written, transformations such as filters, projections,
and aggregations do not execute immediately.

Instead, Spark follows a planning pipeline:
- Transformations build a **logical plan**
- The logical plan is optimized by Spark
- A **physical plan** is generated that defines how computation will run

Actual execution begins only when an action is invoked.

## Stages, tasks, and shuffles

Spark divides execution into **stages**, each consisting of multiple tasks.

The key distinction is between:
- **Narrow transformations**, where data can be processed without moving
  between executors
- **Wide transformations**, where data must be redistributed across the cluster

A **shuffle** occurs when Spark needs to move data across executors to satisfy
a wide transformation. Shuffle boundaries define stage boundaries.

Because shuffles involve network transfer, disk I/O, and serialization,
they are the most expensive operations in Spark.

## Conceptual execution walkthrough

Consider a workload that:
1. Filters records
2. Groups data by a key
3. Sorts results
4. Writes output

The filter operation is a narrow transformation and executes within a single
stage. The group-by operation requires a shuffle to bring identical keys
together, creating a new stage. A global sort introduces another shuffle and
another stage.

Each stage runs multiple tasks in parallel, one task per partition.

## Fault tolerance and lineage

Spark assumes failures are normal in distributed systems.

Instead of relying on mutable shared state, Spark uses:
- Immutable data
- Recorded transformation lineage

If an executor fails, Spark reschedules the lost tasks on other executors and
recomputes the missing partitions using lineage information. This allows Spark
to recover from failures without manual intervention or data repair.

## Common misconceptions

- Spark executes code immediately as it is written
- Adding more cores always makes jobs faster
- Caching data automatically improves performance

Understanding the execution model helps avoid these assumptions and reason
about Spark behavior correctly.

Spark’s execution model reflects deliberate engineering trade-offs that favor
scalability, fault tolerance, and predictable execution at scale.
