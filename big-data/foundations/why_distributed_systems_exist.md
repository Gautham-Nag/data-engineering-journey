# Why Distributed Data Systems Exist

Traditional databases work well when data fits on a single machine
and failures are rare. As data volume, velocity, and complexity grow,
these assumptions break down.

## The core problem
Single-machine systems face hard limits:
- Finite memory and CPU
- Expensive vertical scaling
- Fragile recovery when failures occur

As data grows, failures are no longer exceptional — they are expected.

## Why distribution is necessary
Distributed systems solve these limits by:
- Splitting data into partitions
- Processing data in parallel across machines
- Accepting node failures as normal behavior

This allows systems to scale horizontally and remain resilient.

## Why moving computation to data matters
Data movement is expensive and failure-prone.
By executing computation close to where data is stored,
distributed systems minimize network overhead and improve reliability.

## Fault tolerance by design
Modern distributed engines do not rely on mutable shared state.
Instead, they use:
- Immutable data
- Recorded computation steps (lineage)

When failures occur, lost data is safely recomputed rather than repaired.

## The engineering trade-off
Distributed systems trade simplicity for:
- Scalability
- Fault tolerance
- Predictable performance at scale

This trade-off is necessary for modern analytics workloads.

Understanding these constraints explains why systems like Spark,
Databricks, and Fabric Lakehouse exist.
