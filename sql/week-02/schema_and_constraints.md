# Schema Design & Constraints – Week 02

## Why constraints matter
Constraints enforce correctness at the database level and prevent
invalid data from entering the system.

## Constraints used
- PRIMARY KEY – uniquely identifies records
- FOREIGN KEY – enforces relationships between tables
- NOT NULL – ensures mandatory attributes are present
- UNIQUE – prevents duplicate values (e.g., email)
- CHECK – restricts allowed values (e.g., gender, price)

## Observations
- Without constraints, data validation shifts to application code
- CHECK constraints prevent silent logical errors
- Foreign keys make relationships explicit and enforceable

Well-designed schemas reduce downstream data cleaning.
