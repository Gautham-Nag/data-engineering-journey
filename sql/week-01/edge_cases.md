# Week 01 – SQL Edge Cases & Observations

## Decimal precision & rounding
- Using DECIMAL(5,2) enforces precision
- Example: 3.909 becomes 3.91 automatically

## Invalid date inserts
- Dates must be valid and follow YYYY-MM-DD
- Example: '2024-16-09' fails because month 16 is invalid

## String escaping (apostrophes)
- Apostrophes inside strings must be escaped
- Example: 'Willow\'s Street' (varies by SQL engine)

## “Query returns 0 rows” is not always an error
- It can mean the data simply doesn’t exist yet
- Always validate assumptions about the dataset

## Access control basics
- GRANT/REVOKE controls who can read/write data
- This matters for security and compliance in real systems
