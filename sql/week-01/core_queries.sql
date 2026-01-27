-- View prescriptions table structure
DESCRIBE Prescriptions;

-- List drugs by descending price
SELECT * FROM Drugs
ORDER BY Price DESC;

-- Delete prescriptions for Ibuprofen
DELETE FROM Prescriptions
WHERE DrugName = 'Ibuprofen';

-- Find patients prescribed Paracetamol
SELECT PatientID
FROM Prescriptions
WHERE DrugName = 'Paracetamol';

-- Oldest patient
SELECT *
FROM Patients
ORDER BY DOB ASC
LIMIT 1;

-- Doctors who prescribed Metformin
SELECT DISTINCT DoctorName
FROM Prescriptions
WHERE DrugName = 'Metformin';
