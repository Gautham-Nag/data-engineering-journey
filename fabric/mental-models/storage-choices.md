# Fabric Storage Choices

| Need | Choose | Reason |
|----|------|-------|
| Spark engineering | Lakehouse | File + Delta |
| BI performance | Warehouse | SQL engine |
| Analysts only | Warehouse | Lowest friction |

Rule:
Engineers → Lakehouse  
Analysts → Warehouse
