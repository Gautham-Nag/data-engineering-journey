# Direct Lake vs Import

## Use Direct Lake when
- Data is in OneLake / Delta tables
- Near real-time reporting is required
- Large datasets must be queried fast
- You want to avoid refresh delays

## Use Import when
- Data volume is small to medium
- Complex DAX calculations are required
- Data sources are outside OneLake
- Predictable performance is needed

## Do NOT use Direct Lake when
- Data is not Delta format
- Tables are frequently changing schema
- You need full DAX flexibility

## Do NOT use Import when
- Data size is very large
- Refresh windows are tight
- Near real-time data is required

## Mental model
Direct Lake = reading directly from the warehouse  
Import = taking a snapshot into memory

## Exam signal
If the question mentions **OneLake + performance + no refresh** → Direct Lake  
If the question mentions **DAX complexity + small data** → Import
