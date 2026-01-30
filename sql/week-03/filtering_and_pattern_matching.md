# Filtering & Pattern Matching

## 1) Filtering is about *correctness* first
Core operators:
- `AND` — both conditions must be true
- `OR` — either condition can be true
- `NOT` — negates a condition
- `IN (...)` — readable alternative to multiple ORs
- `BETWEEN a AND b` — inclusive range (be careful with dates/times)

### Good pattern: prefer IN over OR chains
```sql
WHERE location IN ('BANGALORE','HYDERABAD','PUNE')
