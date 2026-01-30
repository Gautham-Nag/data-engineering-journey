# Week 03 — Filtering, Pattern Matching & Aggregations

This week focuses on writing **correct filters** and **correct aggregations** — the part of SQL where most production bugs happen.

## What I worked on
- Filtering with `AND`, `OR`, `NOT`, `IN`, `BETWEEN`
- Pattern matching using `LIKE` and `REGEXP`
- `COUNT(*)` vs `COUNT(column)` and how `NULL` changes results
- `ORDER BY`, `DISTINCT` pitfalls, and SQL execution order
- Aggregations using `SUM`, `AVG`, `MIN`, `MAX`, `COUNT`
- `GROUP BY` rules and filtering groups using `HAVING`

## Files
- `filtering_and_pattern_matching.md` — LIKE vs REGEXP, escaping, and reliable filtering
- `execution_order_and_alias_rules.md` — why aliases fail in WHERE, DISTINCT+ORDER BY pitfalls
- `aggregation_group_by_having.md` — GROUP BY rules, WHERE vs HAVING, common mistakes
- `week-03_patterns.sql` — canonical patterns I can reuse in real work

## Goal
Move from “writing queries that run” to “writing queries that are correct, scalable, and predictable.”
