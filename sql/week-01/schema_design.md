# Week 01 – Database & Schema Design (Pharma Use Case)

## Database
- Database Name: `pharma_db`
- Use Case: Online pharmacy system

## Tables Designed

### Drugs
- DrugID (INT)
- DrugName (VARCHAR)
- Manufacturer (VARCHAR)
- DrugBenefit (VARCHAR)
- Price (DECIMAL)

**Learning**
- DECIMAL enforces precision
- Values like 3.909 round to 3.91

### Patients
- PatientID (INT)
- Name fields
- DOB (DATE)
- Contact & Address

**Learning**
- Invalid date formats fail inserts
- Correct format: YYYY-MM-DD

### Prescriptions
- PrescriptionID
- PatientID
- DrugName
- DoctorName
- DateIssued
- Dosage
