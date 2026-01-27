-- Retrieve female patients
SELECT * FROM Patients
WHERE Gender = 'Female';

-- Doctors with more than 10 years of experience
SELECT * FROM Doctors
WHERE ExperienceYears > 10;

-- Drugs priced between a given range
SELECT * FROM Drugs
WHERE Price BETWEEN 100 AND 500;

-- Completed appointments
SELECT * FROM Appointments
WHERE Status = 'Completed';

-- Count of appointments per doctor
SELECT DoctorID, COUNT(*) AS total_appointments
FROM Appointments
GROUP BY DoctorID;
