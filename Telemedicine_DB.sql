DROP DATABASE IF EXISTS Telemedicine;
CREATE DATABASE Telemedicine;
USE Telemedicine;

CREATE TABLE Disease (
    Disease_ID INT PRIMARY KEY,
    Category VARCHAR(50),
    Name_ VARCHAR(100)
);

CREATE TABLE Department (
    Department_ID INT PRIMARY KEY,
    Name_ VARCHAR(100),
    Location VARCHAR(100)
);

CREATE TABLE Patient (
    Patient_ID INT PRIMARY KEY,
    Fname VARCHAR(50),
    Lname VARCHAR(50),
    DOB DATE,
    Emergency_Contact VARCHAR(15),
    Street VARCHAR(100),
    City VARCHAR(50),
    State VARCHAR(50),
    Zip VARCHAR(10),
    Disease_ID INT
);

CREATE TABLE Phone (
    Patient_ID INT,
    Phone_no INT,
    PRIMARY KEY (Patient_ID, Phone_no)
);

CREATE TABLE Consultant_Log (
    Log_ID INT PRIMARY KEY,
    Date_Time DATETIME,
    Type_ VARCHAR(50),
    Notes TEXT,
    Patient_ID INT,
    Department_ID INT
);

CREATE TABLE Doctor (
    Doctor_ID INT PRIMARY KEY,
    Fname VARCHAR(50),
    Lname VARCHAR(50),
    Specialization VARCHAR(100),
    Email VARCHAR(100),
    Phone VARCHAR(15),
    Department_ID INT,
    Head_ID INT
);

CREATE TABLE Appointment (
    Appointment_ID INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    Date_Time DATETIME,
    current_Status VARCHAR(50),
    Patient_ID INT,
    Doctor_ID INT
);

CREATE TABLE Medicine (
    Medicine_ID INT PRIMARY KEY,
    Name_ VARCHAR(100),
    Dosage VARCHAR(50),
    Expiry_Date DATE,
    Manufacturer VARCHAR(100)
);

CREATE TABLE Prescription (
    PrescriptionID INT PRIMARY KEY,
    Date DATE,
    Instruction TEXT,
    Patient_ID INT
);

CREATE TABLE Involves (
    Patient_ID INT,
    Doctor_ID INT,
    Medicine_ID INT,
    PRIMARY KEY (Patient_ID, Doctor_ID, Medicine_ID)
);

CREATE TABLE Has (
    Patient_ID INT,
    Disease_ID INT,
    Description_ VARCHAR(20),
    PRIMARY KEY(Disease_ID, Patient_ID)
);

-- Add foreign keys
ALTER TABLE Patient
    ADD CONSTRAINT fk_patient_disease FOREIGN KEY (Disease_ID) REFERENCES Disease(Disease_ID);
ALTER TABLE Consultant_Log
    ADD CONSTRAINT fk_cl_patient FOREIGN KEY (Patient_ID) REFERENCES Patient(Patient_ID),
    ADD CONSTRAINT fk_cl_department FOREIGN KEY (Department_ID) REFERENCES Department(Department_ID);
ALTER TABLE Doctor
    ADD CONSTRAINT fk_doctor_department FOREIGN KEY (Department_ID) REFERENCES Department(Department_ID),
    ADD CONSTRAINT fk_head FOREIGN KEY (Head_ID) REFERENCES Doctor(Doctor_ID);
ALTER TABLE Appointment
    ADD CONSTRAINT fk_appointment_patient FOREIGN KEY (Patient_ID) REFERENCES Patient(Patient_ID),
    ADD CONSTRAINT fk_appointment_doctor FOREIGN KEY (Doctor_ID) REFERENCES Doctor(Doctor_ID);
ALTER TABLE Prescription
    ADD CONSTRAINT fk_prescription_patient FOREIGN KEY (Patient_ID) REFERENCES Patient(Patient_ID);
ALTER TABLE Involves
    ADD CONSTRAINT fk_involves_patient FOREIGN KEY (Patient_ID) REFERENCES Patient(Patient_ID),
    ADD CONSTRAINT fk_involves_doctor FOREIGN KEY (Doctor_ID) REFERENCES Doctor(Doctor_ID),
    ADD CONSTRAINT fk_involves_medicine FOREIGN KEY (Medicine_ID) REFERENCES Medicine(Medicine_ID);
ALTER TABLE Phone 
    ADD CONSTRAINT fk_phone_patient FOREIGN KEY (Patient_ID) REFERENCES Patient(Patient_ID);
ALTER TABLE Has 
    ADD CONSTRAINT fk_has_patient FOREIGN KEY (Patient_ID) REFERENCES Patient(Patient_ID),
    ADD CONSTRAINT fk_has_disease FOREIGN KEY (Disease_ID) REFERENCES Disease(Disease_ID);

-- Function: Get full name of a patient by ID 
DELIMITER $$
CREATE FUNCTION GetPatientFullName(pid INT)
RETURNS VARCHAR(101)
DETERMINISTIC
BEGIN
    DECLARE fullName VARCHAR(101);
    SELECT CONCAT(Fname, ' ', Lname) INTO fullName FROM Patient WHERE Patient_ID = pid;
    RETURN fullName;
END $$
DELIMITER ;

-- Procedure: Schedule an appointment using AUTO_INCREMENT Appointment_ID
DELIMITER $$
CREATE PROCEDURE ScheduleAppointment (
    IN pat_id INT,
    IN doc_id INT,
    IN dt DATETIME,
    OUT appt_id INT
)
BEGIN
    INSERT INTO Appointment (Date_Time, current_Status, Patient_ID, Doctor_ID)
    VALUES (dt, 'Scheduled', pat_id, doc_id);
    SELECT LAST_INSERT_ID() INTO appt_id;
END $$
DELIMITER ;

-- Trigger: Update appointment status when a prescription is added
DELIMITER $$
CREATE TRIGGER update_appointment_status_after_prescription
AFTER INSERT ON Prescription
FOR EACH ROW
BEGIN
    UPDATE Appointment
    SET current_Status = 'Prescribed'
    WHERE Patient_ID = NEW.Patient_ID
      AND DATE(Date_Time) = NEW.Date;
END $$
DELIMITER ;
SELECT * FROM Disease;
INSERT INTO Disease (Disease_ID, Name_) VALUES 
(1, 'Type 2 Diabetes'),
(2, 'Hypertension'),
(3, 'Asthma');

-- OR, if your name column is Disease_Name:
-- INSERT INTO Disease (Disease_ID, Disease_Name) VALUES 
-- (1, 'Type 2 Diabetes'),
-- (2, 'Hypertension'),
-- (3, 'Asthma');

COMMIT; -- Always commit your changes!
SELECT COUNT(*) FROM Disease;
SELECT COUNT(*) FROM Department;
SELECT COUNT(*) FROM Patient;
INSERT INTO Department (Department_ID, Name_) VALUES 
(101, 'Cardiology'), 
(102, 'Pediatrics'), 

(103, 'General Practice');


COMMIT; -- IMPORTANT: Make sure you commit the transaction!
SELECT * FROM Patient ORDER BY Patient_ID DESC LIMIT 3;
SELECT * FROM appointment;
-- 1. VIEW: View_Doctor_Appointment_Counts (AGGREGATE)
-- Calculates the total number of appointments per doctor.
CREATE VIEW View_Doctor_Appointment_Counts AS
SELECT
    D.Doctor_ID,
    D.Fname,
    D.Lname,
    D.Specialization,
    COUNT(A.Appointment_ID) AS Total_Appointments  -- AGGREGATE FUNCTION
FROM Doctor D
LEFT JOIN Appointment A ON D.Doctor_ID = A.Doctor_ID
GROUP BY
    D.Doctor_ID, D.Fname, D.Lname, D.Specialization
ORDER BY
    Total_Appointments DESC;
    
-- 2. PROCEDURE: GetDetailedAppointments (JOIN)
-- Lists all appointments with the full name of the patient and doctor using JOINs.
DELIMITER $$
CREATE PROCEDURE GetDetailedAppointments()
BEGIN
    SELECT
        A.Appointment_ID,
        A.Date_Time,
        P.Fname AS Patient_Fname,
        P.Lname AS Patient_Lname,
        D.Fname AS Doctor_Fname,
        D.Lname AS Doctor_Lname
    FROM Appointment A
    JOIN Patient P ON A.Patient_ID = P.Patient_ID
    JOIN Doctor D ON A.Doctor_ID = D.Doctor_ID
    ORDER BY A.Date_Time DESC;
END $$
DELIMITER ;

-- 3. PROCEDURE: FindDoctorsByDisease (NESTED QUERY)
-- Finds doctors who have treated patients with a specific disease ID using a subquery.
DELIMITER $$
DELIMITER $$
CREATE PROCEDURE FindDoctorsByDisease (IN target_disease_id INT)
BEGIN
    SELECT DISTINCT
        T2.Doctor_ID,
        T2.Fname,
        T2.Lname,
        T2.Specialization
    FROM Appointment T1
    JOIN Doctor T2 ON T1.Doctor_ID = T2.Doctor_ID
    WHERE T1.Patient_ID IN (
        -- Find patients who have this disease, either as primary or secondary
        SELECT Patient_ID FROM Patient WHERE Disease_ID = target_disease_id
        UNION
        SELECT Patient_ID FROM Has WHERE Disease_ID = target_disease_id
    );
END $$
DELIMITER ;

-- Reset Delimiter
DELIMITER ;
-- Use IGNORE to avoid errors if the records already exist
-- 1. Ensure Department exists
INSERT IGNORE INTO Department (Department_ID, Name_, Location) VALUES 
(101, 'Cardiology', 'Main Building');

-- 2. Ensure Disease exists (for patient FK constraint, ID 1 is safe)
INSERT IGNORE INTO Disease (Disease_ID, Name_) VALUES 
(1, 'Common Cold');

-- 3. Insert a Sample Doctor (ID 501)
INSERT IGNORE INTO Doctor (Doctor_ID, Fname, Lname, Specialization, Email, Phone, Department_ID) VALUES
(501, 'Alice', 'Smith', 'Cardiology', 'a.smith@telemed.com', '5551234567', 101);

-- 4. Insert a Sample Patient (ID 1)
INSERT IGNORE INTO Patient (Patient_ID, Fname, Lname, DOB, Emergency_Contact, Street, City, State, Zip, Disease_ID) VALUES
(1, 'John', 'Doe', '1980-01-15', '5559876543', '123 Main St', 'Anytown', 'CA', '12345', 1);

-- 5. Create an Appointment linking them (This is the row the report needs)
-- Note: AUTO_INCREMENT will handle Appointment_ID if you drop the column from the INSERT list.
-- If you strictly need to insert Appointment_ID, check the last inserted ID.
INSERT INTO Appointment (Date_Time, current_Status, Patient_ID, Doctor_ID) VALUES
(NOW(), 'Completed', 1, 501);

COMMIT;
SELECT COUNT(*) FROM Appointment A
JOIN Patient P ON A.Patient_ID = P.Patient_ID
JOIN Doctor D ON A.Doctor_ID = D.Doctor_ID;
-- 1. Ensure the Disease 'Hypertension' exists (Disease_ID = 2)
-- Using INSERT IGNORE to prevent an error if ID 2 is already taken or inserted.

INSERT IGNORE INTO Disease (Disease_ID, Category, Name_) VALUES 
(2, 'Cardiovascular', 'Hypertension');

---

-- 2. Insert the New Patient (Jane Doe)
-- Note: We link the patient to Disease_ID = 2 (Hypertension) directly in the Patient table.

INSERT INTO Patient (
    Patient_ID, 
    Fname, 
    Lname, 
    DOB, 
    Emergency_Contact, 
    Street, 
    City, 
    State, 
    Zip, 
    Disease_ID
)
VALUES (
    4, -- Patient ID
    'Jane', 
    'Doe', 
    '1995-03-20', 
    '5551112222', 
    '456 Oak Ave', 
    'Springfield', 
    'IL', 
    '62704', 
    2  -- Links to Disease_ID 2 (Hypertension)
);

---

-- 3. VERIFY the Insertion
SELECT 
    P.Patient_ID, 
    P.Fname, 
    P.Lname, 
    D.Name_ AS Primary_Disease
FROM Patient P
JOIN Disease D ON P.Disease_ID = D.Disease_ID
WHERE P.Patient_ID = 4;

-- Always commit your changes if you are using transactions
COMMIT;
INSERT INTO Patient (
    Patient_ID,        -- Assuming you still require manual ID entry
    Fname,
    Lname,
    DOB,
    Emergency_Contact, -- Must be explicitly listed
    Street,            -- Must be explicitly listed
    City,              -- Must be explicitly listed
    State,             -- Must be explicitly listed
    Zip,               -- Must be explicitly listed
    Disease_ID
)
VALUES (
    4,                 -- Example Patient ID
    'Jane',
    'Doe',
    '1995-03-20',
    NULL,              -- Use NULL if Emergency_Contact is optional/unknown
    '',                -- Use '' or NULL for address fields if unknown
    '',
    '',
    '',
    2                  -- Disease ID for Hypertension
);

COMMIT;
-- Assuming Disease_ID 2 is 'Hypertension'

INSERT INTO Disease (Disease_ID, Category, Name_) VALUES
(1, 'Endocrine', 'Type 2 Diabetes'),
(2, 'Cardiovascular', 'Hypertension'),
(3, 'Respiratory', 'Asthma');

INSERT INTO Department (Department_ID, Name_, Location) VALUES
(101, 'Cardiology', 'Main Building'),
(102, 'Pediatrics', 'Childrens Wing'),
(103, 'General Practice', 'Family Clinic');

-- Insert Doctors for FK constraints
INSERT INTO Doctor (Doctor_ID, Fname, Lname, Specialization, Email, Phone, Department_ID) VALUES
(501, 'Alice', 'Smith', 'Cardiology', 'a.smith@telemed.com', '5551234567', 101),
(502, 'Bob', 'Jones', 'Pediatrics', 'b.jones@telemed.com', '5557654321', 102);

-- Insert sample patients (IDs 1-4)
INSERT INTO Patient (Patient_ID, Fname, Lname, DOB, Emergency_Contact, Street, City, State, Zip, Disease_ID) VALUES
(1, 'John', 'Doe', '1980-01-15', '5559876543', '123 Main St', 'Anytown', 'CA', '12345', 1), -- Diabetes
(2, 'Mary', 'Jane', '1990-05-20', '5551112222', '44 River Rd', 'Bigtown', 'NY', '10001', 2),  -- Hypertension
(3, 'Chris', 'Evans', '2000-11-01', '5553334444', '99 Hill Ave', 'Smallville', 'TX', '77001', 3), -- Asthma
(4, 'Jane', 'Doe', '1995-03-20', '5551112222', '456 Oak Ave', 'Springfield', 'IL', '62704', 2); -- Hypertension (Your previously inserted Jane)

-- ---------------------------------
-- 5. Insert 10 More Patients with Hypertension (IDs 5-14)
-- ---------------------------------

INSERT INTO Patient (
    Patient_ID, Fname, Lname, DOB, Emergency_Contact, Street, City, State, Zip, Disease_ID
)
VALUES
(5, 'Robert', 'Davis', '1975-11-10', '555-101-202', '10 Elm St', 'Seattle', 'WA', '98101', 2),
(6, 'Emily', 'White', '1968-04-25', '555-303-404', '25 Oak Lane', 'Boston', 'MA', '02108', 2),
(7, 'Michael', 'Brown', '1982-08-15', '555-505-606', '50 Pine Blvd', 'Miami', 'FL', '33101', 2),
(8, 'Jessica', 'Green', '1990-02-02', '555-707-808', '75 Birch Rd', 'Denver', 'CO', '80202', 2),
(9, 'William', 'Clark', '1955-12-30', '555-909-101', '100 Cedar Dr', 'Chicago', 'IL', '60601', 2),
(10, 'Olivia', 'Rodriguez', '1988-06-18', '555-212-323', '200 Maple Ave', 'Phoenix', 'AZ', '85001', 2),
(11, 'Daniel', 'Martinez', '1979-01-05', '555-434-545', '350 Walnut Ct', 'Dallas', 'TX', '75201', 2),
(12, 'Sophia', 'Lee', '1962-10-28', '555-656-767', '400 Poplar Wy', 'San Diego', 'CA', '92101', 2),
(13, 'James', 'Wilson', '1993-07-12', '555-878-989', '550 Spruce Pk', 'Atlanta', 'GA', '30303', 2),
(14, 'Ava', 'Taylor', '1985-03-01', '555-090-191', '600 Willow Ln', 'Portland', 'OR', '97204', 2);

COMMIT;
