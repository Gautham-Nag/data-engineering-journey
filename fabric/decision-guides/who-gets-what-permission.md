# Who Gets What Permission (Fabric)

## Give Workspace Viewer when
- Users only need to view reports
- No report creation is required
- No SQL or external access is needed

## Give Dataset Build permission when
- Users need to create their own reports
- Semantic model must not be edited
- Least privilege is required

## Use Semantic Model RLS when
- You need to restrict rows
- Restriction applies only to Power BI
- SQL users should still see all data

## Use Semantic Model OLS when
- You need to hide columns or tables
- Restriction must apply to:
  - Power BI
  - Analyze in Excel
  - XMLA tools

## Use SQL Endpoint permissions when
- Users connect via SQL tools (SSMS, ADS)
- Read or write access must be controlled
- Power BI permissions are not sufficient

## Use XMLA Read when
- Users run DAX queries
- External tools connect in read-only mode

## Use XMLA Read Write when
- External tools modify semantic models
- Deployment pipelines or Tabular Editor is used

## Mental model
Workspace = who can enter  
Build = who can create reports  
RLS = which rows you see  
OLS = which columns exist  
SQL endpoint = database access  
XMLA = external model access

## Exam signal
Rows → RLS  
Columns → OLS  
SQL tools → SQL endpoint  
Create reports → Build  
External model edit → XMLA Read Write
