# Cascading Effects in Relational Databases

## What is ON DELETE CASCADE
ON DELETE CASCADE automatically removes dependent records
when a parent record is deleted.

## Why it exists
- Prevents orphan records
- Maintains referential integrity

## Risks
- Accidental deletes can remove large amounts of data
- Cascades should be used only when the relationship is truly dependent

## Engineering takeaway
Cascading behavior must be a conscious design decision.
In analytics systems, deletes are often restricted or soft-deleted instead.
