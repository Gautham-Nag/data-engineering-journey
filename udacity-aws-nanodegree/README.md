# AWS Data Engineering Nanodegree — Project Portfolio

[![Udacity](https://img.shields.io/badge/Udacity-Data%20Engineering%20with%20AWS-02B3E4?style=flat&logo=udacity)](https://www.udacity.com/certificate/e/d858f7be-a5f2-11f1-b3da-6356633ccbdb)
[![AWS](https://img.shields.io/badge/AWS-Certified%20Data%20Engineer%20Associate-FF9900?style=flat&logo=amazonaws)](https://aws.amazon.com/verification)
[![Certificate](https://img.shields.io/badge/Certificate-Verified-green)](https://www.udacity.com/certificate/e/d858f7be-a5f2-11f1-b3da-6356633ccbdb)

This repository contains the four project submissions completed as part of the **Udacity Data Engineering with AWS Nanodegree** (completed September 2026). The program covers the full data engineering lifecycle on AWS — from data modeling and warehouse design to lakehouse architecture and pipeline orchestration.

---

## 📋 Program Overview

| Domain | Technologies Covered |
|--------|---------------------|
| Data Modeling | PostgreSQL, MongoDB, Neo4j, 3NF, Star Schema, SCD Type 2 |
| Data Warehousing | Amazon Redshift, DISTKEY/SORTKEY, Materialized Views |
| Lakehouse Architecture | Apache Iceberg, AWS Glue, S3, S3 Tables, Amazon Athena |
| Pipeline Orchestration | Apache Airflow, DAGs, Asset-triggered pipelines |

---

## 🗂️ Projects

### Project 1 — Data Modeling for ACME (TechMart E-Commerce Platform)

**Objective:** Design and implement a multi-paradigm data model for a B2B e-commerce platform across three database types.

**What was built:**
- **Relational model (PostgreSQL)** — 3NF schema with 6 tables (`categories`, `customers`, `products`, `purchases`, `purchase_items`, `user_ratings`) covering a full e-commerce transaction model with primary/foreign key constraints, customer lifetime value queries, and product catalog analytics
- **Document model (MongoDB)** — Three collections using a deliberate embedding vs referencing strategy: `customers` (embedding recent purchases), `products` (flexible schema with type-specific attributes — `specs{}` for electronics, `author/isbn` for books), and `purchases` (referencing for unbounded growth)
- **Graph model (Neo4j)** — Cypher-based adjacency list modeling customer-product relationships for recommendation graph traversal

**Key concepts demonstrated:**
- 3NF normalization with transitive dependency elimination
- Document embedding vs referencing design decisions with rationale
- Graph traversal for product recommendation queries
- Multi-paradigm data access patterns for the same underlying domain

**Tech stack:** Python, SQLite (PostgreSQL-compatible DDL), custom PyMongo-compatible API, Neo4j Cypher logic

---

### Project 2 — Multi-Source E-Commerce Analytics Warehouse in Redshift

**Objective:** Build a production-grade star schema data warehouse in Amazon Redshift ingesting from three heterogeneous source systems.

**What was built:**
- **Star schema** — 3 fact tables × 12 dimension tables sourced from PostgreSQL, Cassandra, and Neo4j
- **Fact tables:** `dw_fact_orders` (order transactions), `dw_fact_events` (clickstream events), `dw_fact_graph_edges` (product graph relationships)
- **Dimension tables:** `dw_dim_customer` (SCD Type 2), `dw_dim_product` (SCD Type 2), `dw_dim_date` (calendar spine), plus 9 lookup dimensions (channel, device, browser, OS, referrer, campaign, shipping, payment, A/B variant)
- **Materialized view:** `dw_mv_daily_revenue` for pre-aggregated revenue reporting

**Distribution and sort key strategy:**
| Table | DISTKEY | SORTKEY | Rationale |
|-------|---------|---------|-----------|
| `dw_fact_orders` | `customer_sk` | `order_date_key` | Co-located with `dim_customer`, eliminates shuffle |
| `dw_fact_events` | `customer_sk` | `event_date_key` | Co-located with `dim_customer`, eliminates shuffle |
| `dw_fact_graph_edges` | `to_product_sk` | `event_date_key` | Product recommendation queries dominate |
| `dw_dim_date` | DISTSTYLE ALL | `date_key` | Broadcast — zero shuffle on any date join |
| Lookup dims | DISTSTYLE ALL | — | < 100 rows each, broadcasting costs nothing |
| Staging tables | DISTSTYLE EVEN | — | Prevents hot-node skew during INSERT |

**Performance findings:**
- Full scan (fact_orders JOIN dim_date GROUP BY month): 2.74s
- Materialized view (pre-aggregated): 2.79s
- Zone-map pruning on sort keys enables block-level skipping without full scans

**Tech stack:** Amazon Redshift, SQL, SCD Type 2, ANALYZE, materialized views

---

### Project 3 — AWS Data Lakehouse Pipeline for Sparkify (Airflow + Glue + S3)

**Objective:** Build a fully orchestrated data lakehouse pipeline for a music streaming platform using Apache Airflow, AWS Glue, and S3.

**Architecture:**

```
S3 Landing Zone
    │
    ▼
Airflow DAG: raw/
    └── AWS Glue: raw ingestion script → S3 Raw Layer
            │
            ▼
    Airflow DAG: transactions/
        └── AWS Glue: transformation script + SQL → S3 Transactions Layer
                │
                ▼
        Airflow DAG: analytics/
            └── AWS Glue: analytics script + SQL → S3 Analytics Layer
```

**What was built:**
- **Raw DAG** — Asset-triggered ingestion pipeline capturing S3 landing keys, running parallel Glue jobs, validating raw data (log and song checks), and notifying completion
- **Transactions DAG** — Asset-triggered transformation pipeline building 6 curated tables (`artists`, `songs`, `song_versions`, `users`, `user_levels`, `events`) with PK integrity checks and null validation
- **Analytics DAG** — Asset-triggered analytics layer building 4 fact tables (`artist_facts`, `song_facts`, `session_facts`, `user_facts`) with data quality gates before promotion
- **CloudFormation template** — Full IaC for AWS resource provisioning

**Key patterns implemented:**
- Asset-triggered DAG chaining (raw → transactions → analytics)
- Parallel task mapping with `map_index` for concurrent Glue job execution
- Data quality gates (not-empty checks, PK uniqueness, FK integrity) before layer promotion
- Retry logic with multi-attempt logging for resilient pipeline execution

**Tech stack:** Apache Airflow 2.x, AWS Glue (PySpark), Amazon S3, AWS CloudFormation, PostgreSQL (Airflow metadata)

---

### Project 4 — Exastore Data Lakehouse on AWS (Apache Iceberg + Medallion Architecture)

**Objective:** Build a medallion-architecture data lakehouse using Apache Iceberg, AWS Glue, S3 Tables, and Athena — processing CDC and clickstream data through Bronze → Silver → Gold layers.

**Architecture:**

```
CDC JSON (S3)       ──→  Glue: CDC Bronze    ──→  S3 Iceberg (orders, users, products)
Clickstream JSON (S3) ──→  Glue: Events Bronze ──→  S3 Iceberg (events)
                           Glue: Silver Layer   ──→  S3 Tables  (order_details, enriched_events, product_performance)
                           Glue: Gold Layer     ──→  S3 Tables  (customer_analytics, realtime_metrics)
```

**What was built:**

| Layer | Storage | Tables | Technique |
|-------|---------|--------|-----------|
| Bronze | S3 + Glue Catalog Iceberg | `orders`, `users`, `products`, `events` | CDC MERGE INTO, append-only INSERT |
| Silver | S3 Tables (managed Iceberg) | `order_details`, `enriched_events`, `product_performance` | JOINs, window functions, aggregations |
| Gold | S3 Tables (managed Iceberg) | `customer_analytics`, `realtime_metrics` | Monthly/hourly business aggregations |

**Key Iceberg features explored:**
- `MERGE INTO` for CDC upsert operations at the Bronze layer
- Snapshot isolation and time-travel queries for historical data access
- S3 Tables (managed Iceberg) for Silver and Gold layers
- Athena SQL validation queries across all medallion layers

**Data sources processed:**
- CDC data: 12 months × 3 tables (orders, products, users) in partitioned JSON
- Supplemental CDC data for late-arriving records
- Clickstream events batch in JSON

**Tech stack:** Apache Iceberg, AWS Glue (PySpark), Amazon S3, S3 Tables, Amazon Athena, AWS CloudFormation

---

## 🏆 Certification

This Nanodegree served as the foundation for the **AWS Certified Data Engineer – Associate (DEA-C01)** certification, cleared with a score of **872/1000** with Meets Competencies across all four domains:

- Domain 1: Data Ingestion and Transformation (34%)
- Domain 2: Data Store Management (26%)
- Domain 3: Data Operations and Support (22%)
- Domain 4: Data Security and Governance (18%)

**Verify Nanodegree:** https://www.udacity.com/certificate/e/d858f7be-a5f2-11f1-b3da-6356633ccbdb
** Verify AWS Certified Data Engineer - Associate (DEA-C01) ** https://www.credly.com/badges/3ac1a894-590d-4b4e-a10e-cb74bad54319/public_url

---

## 👤 About

**Gautham Nagaraj Naidu**  
Data Engineer — Accenture India, DSCOE  
Currently architecting the myRMG DCSO Analytics Platform on Microsoft Fabric (F16) for HR Operations.

*Specialisation: Data Engineering · Microsoft Fabric · Databricks · AWS · GenAI & Agentic AI*
