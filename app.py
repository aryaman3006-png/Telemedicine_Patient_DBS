from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func
from sqlalchemy.orm import Session
# OR if you are using Flask-SQLAlchemy's built-in session (which is simpler for this case):
from flask_sqlalchemy import SQLAlchemy
# TOP OF app.py
from sqlalchemy.orm import Session
from sqlalchemy import text as db_text 
from sqlalchemy.orm import Session
from sqlalchemy import text as db_text
# ... (other imports)
# ... other imports
# If you don't have SQLAlchemy objects imported, you can stick to the db.session syntax for raw execution

# --- 1. INITIALIZE FLASK AND DB CONFIGURATION ---
app = Flask(__name__)

# ---!!! CRITICAL: REPLACE 'your_password' WITH YOUR ACTUAL MYSQL PASSWORD !!!---
# Ensure your MySQL password is correct and URL-encoded if it has special characters.
# Your password 'Aadhya@02' becomes 'Aadhya%4002'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Aadhya%4002@localhost/Telemedicine'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)

db = SQLAlchemy(app)


# --- 2. DATABASE MODELS (Matching the FULL Telemedicine Schema) ---

# Association table: Has (Patient <-> Disease)
# This is a many-to-many relationship with an extra field 'Description_'
class Has(db.Model):
    __tablename__ = 'Has'
    Patient_ID = db.Column(db.Integer, db.ForeignKey('Patient.Patient_ID'), primary_key=True)
    Disease_ID = db.Column(db.Integer, db.ForeignKey('Disease.Disease_ID'), primary_key=True)
    Description_ = db.Column(db.String(20))
    
    patient = db.relationship('Patient', back_populates='diagnoses')
    disease = db.relationship('Disease', back_populates='patients_diagnosed')

# Association table: Involves (Patient <-> Doctor <-> Medicine)
# This is a ternary relationship, modeled as a class
class Involves(db.Model):
    __tablename__ = 'Involves'
    Patient_ID = db.Column(db.Integer, db.ForeignKey('Patient.Patient_ID'), primary_key=True)
    Doctor_ID = db.Column(db.Integer, db.ForeignKey('Doctor.Doctor_ID'), primary_key=True)
    Medicine_ID = db.Column(db.Integer, db.ForeignKey('Medicine.Medicine_ID'), primary_key=True)
    
    patient = db.relationship('Patient', backref='involved_medicines')
    doctor = db.relationship('Doctor', backref='involved_prescriptions')
    medicine = db.relationship('Medicine', backref='involved_patients')

class Department(db.Model):
    __tablename__ = 'Department'
    Department_ID = db.Column(db.Integer, primary_key=True)
    Name_ = db.Column(db.String(100), nullable=False)
    Location = db.Column(db.String(100))
    
    doctors = db.relationship('Doctor', back_populates='department')
    logs = db.relationship('Consultant_Log', back_populates='department')

class Disease(db.Model):
    __tablename__ = 'Disease'
    Disease_ID = db.Column(db.Integer, primary_key=True)
    Category = db.Column(db.String(50))
    Name_ = db.Column(db.String(100))
    
    
    __tablename__ = 'Disease'
    # This relationship is for the 'Has' table (many-to-many)
    patients_diagnosed = db.relationship('Has', back_populates='disease')
    
    # This is for the 1-to-many 'primary_disease' relationship
    primary_patients = db.relationship('Patient', back_populates='primary_disease', foreign_keys='Patient.Disease_ID')

class Doctor(db.Model):
    __tablename__ = 'Doctor'
    Doctor_ID = db.Column(db.Integer, primary_key=True)
    Fname = db.Column(db.String(50), nullable=False)
    Lname = db.Column(db.String(50), nullable=False)
    Specialization = db.Column(db.String(100))
    Email = db.Column(db.String(100))
    Phone = db.Column(db.String(15))
    Department_ID = db.Column(db.Integer, db.ForeignKey('Department.Department_ID'))
    Head_ID = db.Column(db.Integer, db.ForeignKey('Doctor.Doctor_ID'))
    
    department = db.relationship('Department', back_populates='doctors')
    appointments = db.relationship('Appointment', back_populates='doctor')
    
    # Self-referential relationship for Head Doctor
    head = db.relationship('Doctor', remote_side=[Doctor_ID], backref='subordinates')

class Patient(db.Model):
    __tablename__ = 'Patient'
    Patient_ID = db.Column(db.Integer, primary_key=True)
    Fname = db.Column(db.String(50), nullable=False)
    Lname = db.Column(db.String(50), nullable=False)
    DOB = db.Column(db.Date)
    Emergency_Contact = db.Column(db.String(15))
    Street = db.Column(db.String(100))
    City = db.Column(db.String(50))
    State = db.Column(db.String(50))
    Zip = db.Column(db.String(10))
    Disease_ID = db.Column(db.Integer, db.ForeignKey('Disease.Disease_ID')) # Primary disease
    
    # Relationships
    primary_disease = db.relationship('Disease', back_populates='primary_patients', foreign_keys=[Disease_ID])
    appointments = db.relationship('Appointment', back_populates='patient', cascade="all, delete-orphan")
    phones = db.relationship('Phone', back_populates='patient', cascade="all, delete-orphan")
    logs = db.relationship('Consultant_Log', back_populates='patient', cascade="all, delete-orphan")
    prescriptions = db.relationship('Prescription', back_populates='patient', cascade="all, delete-orphan")
    
    # This relationship is for the 'Has' table (many-to-many)
    diagnoses = db.relationship('Has', back_populates='patient', cascade="all, delete-orphan")

class Phone(db.Model):
    __tablename__ = 'Phone'
    Patient_ID = db.Column(db.Integer, db.ForeignKey('Patient.Patient_ID'), primary_key=True)
    Phone_no = db.Column(db.String(15), primary_key=True) # Changed to String for safety
    
    patient = db.relationship('Patient', back_populates='phones')

class Appointment(db.Model):
    __tablename__ = 'Appointment'
    Appointment_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Date_Time = db.Column(db.DateTime, nullable=False)
    current_Status = db.Column(db.String(50), default='Scheduled')
    Patient_ID = db.Column(db.Integer, db.ForeignKey('Patient.Patient_ID'), nullable=False)
    Doctor_ID = db.Column(db.Integer, db.ForeignKey('Doctor.Doctor_ID'), nullable=False)
    
    patient = db.relationship('Patient', back_populates='appointments')
    doctor = db.relationship('Doctor', back_populates='appointments')

class Medicine(db.Model):
    __tablename__ = 'Medicine'
    Medicine_ID = db.Column(db.Integer, primary_key=True)
    Name_ = db.Column(db.String(100))
    Dosage = db.Column(db.String(50))
    Expiry_Date = db.Column(db.Date)
    Manufacturer = db.Column(db.String(100))

class Prescription(db.Model):
    __tablename__ = 'Prescription'
    PrescriptionID = db.Column(db.Integer, primary_key=True)
    Date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    Instruction = db.Column(db.Text)
    Patient_ID = db.Column(db.Integer, db.ForeignKey('Patient.Patient_ID'), nullable=False)
    
    patient = db.relationship('Patient', back_populates='prescriptions')

class Consultant_Log(db.Model):
    __tablename__ = 'Consultant_Log'
    Log_ID = db.Column(db.Integer, primary_key=True)
    Date_Time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    Type_ = db.Column(db.String(50))
    Notes = db.Column(db.Text)
    Patient_ID = db.Column(db.Integer, db.ForeignKey('Patient.Patient_ID'), nullable=False)
    Department_ID = db.Column(db.Integer, db.ForeignKey('Department.Department_ID'))
    
    patient = db.relationship('Patient', back_populates='logs')
    department = db.relationship('Department', back_populates='logs')
    # --- Model for SQL Aggregate VIEW ---
# Note: We use __bind_key__ and __table_args__ to tell SQLAlchemy this is a VIEW
class View_Doctor_Appointment_Counts(db.Model):
    __tablename__ = 'View_Doctor_Appointment_Counts'
    __bind_key__ = None
    __table_args__ = {'extend_existing': True}
    
    # Define columns exactly as they appear in the VIEW's SELECT statement
    Doctor_ID = db.Column(db.Integer, primary_key=True) # Must have a primary key for SQLAlchemy
    Fname = db.Column(db.String(50))
    Lname = db.Column(db.String(50))
    Specialization = db.Column(db.String(100))
    Total_Appointments = db.Column(db.Integer)
    # --- Model for SQL JOIN Stored Procedure Results ---
    
class DetailedAppointmentResult(db.Model):
    __tablename__ = 'GetDetailedAppointments' # Not a real table name, just a placeholder
    __bind_key__ = None
    __table_args__ = {'extend_existing': True}
    
    # Define columns exactly as aliased in the SQL procedure's SELECT statement
    Appointment_ID = db.Column(db.Integer, primary_key=True) 
    Date_Time = db.Column(db.DateTime)
    Patient_Fname = db.Column(db.String(50))
    Patient_Lname = db.Column(db.String(50))
    Doctor_Fname = db.Column(db.String(50))
    Doctor_Lname = db.Column(db.String(50))
    Appointment_ID: int
    Date_Time: str
    Patient_Fname: str
    Patient_Lname: str
    Doctor_Fname: str
    Doctor_Lname: str
    # --- Model for SQL Nested Query Stored Procedure Results ---
class DoctorByDiseaseResult(db.Model):
    __tablename__ = 'FindDoctorsByDisease' # Placeholder
    __bind_key__ = None
    __table_args__ = {'extend_existing': True}

    # Define columns exactly as selected in the SQL procedure
    Doctor_ID = db.Column(db.Integer, primary_key=True)
    Fname = db.Column(db.String(50))
    Lname = db.Column(db.String(50))
    Specialization = db.Column(db.String(100))

# --- 3. HELPER FUNCTION (Seeding Initial Data) ---
def initialize_database():
    """Populates basic data if tables are empty."""
    db.create_all()

    if Disease.query.count() == 0:
        db.session.add_all([
            Disease(Disease_ID=1, Category='Chronic', Name_='Diabetes'),
            Disease(Disease_ID=2, Category='Acute', Name_='Common Cold'),
            Disease(Disease_ID=3, Category='Cardio', Name_='Hypertension')
        ])

    if Department.query.count() == 0:
        db.session.add_all([
            Department(Department_ID=101, Name_='Cardiology', Location='Main Hospital'),
            Department(Department_ID=102, Name_='Pediatrics', Location='Children Wing'),
            Department(Department_ID=103, Name_='General Practice', Location='Clinic A')
        ])

    if Doctor.query.count() == 0:
        # We must commit Departments first to use their IDs
        db.session.commit()
        db.session.add_all([
            Doctor(Doctor_ID=1, Fname='Alice', Lname='Smith', Specialization='Heart Specialist', Email='alice@hospital.com', Phone='555-0101', Department_ID=101),
            Doctor(Doctor_ID=2, Fname='Bob', Lname='Jones', Specialization='Child Health', Email='bob@hospital.com', Phone='555-0102', Department_ID=102),
            Doctor(Doctor_ID=3, Fname='Carla', Lname='Diaz', Specialization='General Practitioner', Email='carla@hospital.com', Phone='555-0103', Department_ID=103, Head_ID=1)
        ])

    if Medicine.query.count() == 0:
        db.session.add_all([
            Medicine(Medicine_ID=1, Name_='Metformin', Dosage='500mg', Expiry_Date=datetime.strptime('2025-12-31', '%Y-%m-%d').date(), Manufacturer='PharmaCo'),
            Medicine(Medicine_ID=2, Name_='Lisinopril', Dosage='10mg', Expiry_Date=datetime.strptime('2026-06-30', '%Y-%m-%d').date(), Manufacturer='MediLife'),
            Medicine(Medicine_ID=3, Name_='Amoxicillin', Dosage='250mg', Expiry_Date=datetime.strptime('2024-10-01', '%Y-%m-%d').date(), Manufacturer='HealthWell')
        ])
    
    db.session.commit()
    print("Database seeding checked and complete.")


# --- 4. MAIN APPLICATION ROUTES ---

@app.route('/')
def dashboard():
    """Renders the main dashboard."""
    # Fetch recent appointments
    appointments = Appointment.query.order_by(Appointment.Date_Time.desc()).limit(10).all()
    
    # Fetch data for dashboard dropdowns
    patients = Patient.query.order_by(Patient.Lname).all()
    doctors = Doctor.query.order_by(Doctor.Lname).all()
    
    return render_template('dashboard.html', 
                           appointments=appointments, 
                           patients=patients, 
                           doctors=doctors)

# --- 5. PATIENT CRUD ROUTES ---

@app.route('/patients')
def manage_patients():
    """Displays all patients and a form to add new ones."""
    patients = Patient.query.order_by(Patient.Lname).all()
    diseases = Disease.query.order_by(Disease.Name_).all()
    return render_template('manage_patients.html', patients=patients, diseases=diseases)

@app.route('/patient/add', methods=['POST'])
def add_patient():
    """Handles adding a new patient."""
    try:
        dob = datetime.strptime(request.form['dob'], '%Y-%m-%d').date()
        disease_id = request.form.get('disease_id') # Get may return None
        
        new_patient = Patient(
            Patient_ID=int(request.form['patient_id']),
            Fname=request.form['fname'],
            Lname=request.form['lname'],
            DOB=dob,
            Emergency_Contact=request.form.get('emergency_contact'),
            Street=request.form.get('street'),
            City=request.form.get('city'),
            State=request.form.get('state'),
            Zip=request.form.get('zip'),
            Disease_ID=int(disease_id) if disease_id else None
        )
        db.session.add(new_patient)
        db.session.commit()
        flash(f"Patient {new_patient.Fname} {new_patient.Lname} successfully registered!", 'success')
    except IntegrityError:
        db.session.rollback()
        flash(f"Error: Patient ID {request.form['patient_id']} already exists.", 'danger')
    except Exception as e:
        db.session.rollback()
        print(f"Error adding patient: {e}")
        flash(f"Error adding patient: {e}", 'danger')
    
    return redirect(url_for('manage_patients'))

@app.route('/patient/<int:patient_id>')
def patient_detail(patient_id):
    """Shows a detailed view of a single patient and forms for related items."""
    patient = Patient.query.get_or_404(patient_id)
    departments = Department.query.all()
    diseases = Disease.query.all()
    
    # Get IDs of diseases patient already has
    diagnosed_disease_ids = {d.Disease_ID for d in patient.diagnoses}
    
    # Filter out diseases patient already has for the dropdown
    available_diseases = [d for d in diseases if d.Disease_ID not in diagnosed_disease_ids]
    
    return render_template('patient_detail.html', 
                           patient=patient, 
                           departments=departments, 
                           diseases=available_diseases)

@app.route('/patient/<int:patient_id>/delete', methods=['POST'])
def delete_patient(patient_id):
    """Deletes a patient."""
    try:
        patient = Patient.query.get_or_404(patient_id)
        db.session.delete(patient)
        db.session.commit()
        flash(f'Patient {patient.Fname} {patient.Lname} (ID: {patient.Patient_ID}) has been deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting patient: {e}', 'danger')
    return redirect(url_for('manage_patients'))

@app.route('/patient/<int:patient_id>/add_phone', methods=['POST'])
def add_phone(patient_id):
    """Adds a phone number to a patient."""
    patient = Patient.query.get_or_404(patient_id)
    phone_no = request.form['phone_no']
    
    # Check if phone number already exists for this patient
    existing_phone = Phone.query.filter_by(Patient_ID=patient_id, Phone_no=phone_no).first()
    if existing_phone:
        flash(f'Phone number {phone_no} already on file for this patient.', 'warning')
        return redirect(url_for('patient_detail', patient_id=patient_id))
        
    try:
        new_phone = Phone(Patient_ID=patient_id, Phone_no=phone_no)
        db.session.add(new_phone)
        db.session.commit()
        flash('Phone number added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding phone number: {e}', 'danger')
        
    return redirect(url_for('patient_detail', patient_id=patient_id))

@app.route('/patient/<int:patient_id>/add_log', methods=['POST'])
def add_log(patient_id):
    """Adds a consultant log entry for a patient."""
    patient = Patient.query.get_or_404(patient_id)
    try:
        new_log = Consultant_Log(
            Patient_ID=patient_id,
            Date_Time=datetime.now(),
            Type_=request.form['type'],
            Notes=request.form['notes'],
            Department_ID=int(request.form['department_id'])
        )
        db.session.add(new_log)
        db.session.commit()
        flash('Consultant log added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding log: {e}', 'danger')
        
    return redirect(url_for('patient_detail', patient_id=patient_id))

@app.route('/patient/<int:patient_id>/add_prescription', methods=['POST'])
def add_prescription(patient_id):
    """Adds a prescription for a patient."""
    patient = Patient.query.get_or_404(patient_id)
    try:
        new_prescription = Prescription(
            Patient_ID=patient_id,
            Date=datetime.strptime(request.form['date'], '%Y-%m-%d').date(),
            Instruction=request.form['instruction']
        )
        db.session.add(new_prescription)
        db.session.commit()
        
        # This will trigger your SQL trigger 'update_appointment_status_after_prescription'
        
        flash('Prescription added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding prescription: {e}', 'danger')
        
    return redirect(url_for('patient_detail', patient_id=patient_id))

@app.route('/patient/<int:patient_id>/diagnose', methods=['POST'])
def add_diagnosis(patient_id):
    """Adds a 'Has' relationship (diagnoses a patient with a disease)."""
    patient = Patient.query.get_or_404(patient_id)
    try:
        disease_id = int(request.form['disease_id'])
        description = request.form['description']
        
        new_diagnosis = Has(
            Patient_ID=patient_id,
            Disease_ID=disease_id,
            Description_=description
        )
        db.session.add(new_diagnosis)
        db.session.commit()
        flash('Diagnosis added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding diagnosis: {e}', 'danger')
        
    return redirect(url_for('patient_detail', patient_id=patient_id))


# --- 6. APPOINTMENT CRUD ROUTES ---

@app.route('/appointment/schedule', methods=['POST'])
def schedule_appointment():
    """Handles scheduling a new appointment."""
    try:
        patient_id = int(request.form['patient_id'])
        doctor_id = int(request.form['doctor_id'])
        date_time = datetime.strptime(request.form['date_time'], '%Y-%m-%dT%H:%M')
        
        # Call the stored procedure 'ScheduleAppointment'
        db.session.execute(
            db.text("CALL ScheduleAppointment(:pat_id, :doc_id, :dt, @appt_id)"),
            {'pat_id': patient_id, 'doc_id': doctor_id, 'dt': date_time}
        )
        db.session.commit()
        
        flash('Appointment successfully scheduled using stored procedure!', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"Error scheduling appointment: {e}")
        flash(f"Error scheduling appointment: {e}", 'danger')
    
    return redirect(url_for('dashboard'))

@app.route('/appointment/<int:appointment_id>/delete', methods=['POST'])
def delete_appointment(appointment_id):
    """Deletes an appointment."""
    try:
        appt = Appointment.query.get_or_404(appointment_id)
        db.session.delete(appt)
        db.session.commit()
        flash('Appointment successfully deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting appointment: {e}', 'danger')
    return redirect(url_for('dashboard'))

@app.route('/appointment/<int:appointment_id>/update_status', methods=['POST'])
def update_appointment_status(appointment_id):
    """Updates the status of an appointment."""
    try:
        appt = Appointment.query.get_or_404(appointment_id)
        new_status = request.form['status']
        appt.current_Status = new_status
        db.session.commit()
        flash('Appointment status updated.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating status: {e}', 'danger')
    return redirect(url_for('dashboard'))


# --- 7. DOCTOR CRUD ROUTES ---

@app.route('/doctors')
def manage_doctors():
    """Displays all doctors and a form to add new ones."""
    doctors = Doctor.query.order_by(Doctor.Lname).all()
    departments = Department.query.order_by(Department.Name_).all()
    # For the 'Head_ID' dropdown, we list all doctors
    all_doctors = Doctor.query.order_by(Doctor.Lname).all() 
    return render_template('manage_doctors.html', 
                           doctors=doctors, 
                           departments=departments, 
                           all_doctors=all_doctors)

@app.route('/doctor/add', methods=['POST'])
def add_doctor():
    """Handles adding a new doctor."""
    try:
        dept_id = int(request.form['department_id'])
        head_id = request.form.get('head_id')
        
        new_doctor = Doctor(
            Doctor_ID=int(request.form['doctor_id']),
            Fname=request.form['fname'],
            Lname=request.form['lname'],
            Specialization=request.form.get('specialization'),
            Email=request.form.get('email'),
            Phone=request.form.get('phone'),
            Department_ID=dept_id,
            Head_ID=int(head_id) if head_id else None
        )
        db.session.add(new_doctor)
        db.session.commit()
        flash(f"Doctor {new_doctor.Fname} {new_doctor.Lname} added successfully!", 'success')
    except IntegrityError:
        db.session.rollback()
        flash(f"Error: Doctor ID {request.form['doctor_id']} already exists.", 'danger')
    except Exception as e:
        db.session.rollback()
        print(f"Error adding doctor: {e}")
        flash(f"Error adding doctor: {e}", 'danger')
    
    return redirect(url_for('manage_doctors'))

@app.route('/doctor/<int:doctor_id>/delete', methods=['POST'])
def delete_doctor(doctor_id):
    """Deletes a doctor."""
    try:
        doctor = Doctor.query.get_or_404(doctor_id)
        db.session.delete(doctor)
        db.session.commit()
        flash(f'Doctor {doctor.Fname} {doctor.Lname} has been deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting doctor: {e}. They may have appointments scheduled.', 'danger')
    return redirect(url_for('manage_doctors'))

# --- 8. DEPARTMENT CRUD ROUTES ---

@app.route('/departments')
def manage_departments():
    """Displays all departments and a form to add new ones."""
    departments = Department.query.order_by(Department.Name_).all()
    return render_template('manage_departments.html', departments=departments)

@app.route('/department/add', methods=['POST'])
def add_department():
    """Handles adding a new department."""
    try:
        new_dept = Department(
            Department_ID=int(request.form['department_id']),
            Name_=request.form['name'],
            Location=request.form.get('location')
        )
        db.session.add(new_dept)
        db.session.commit()
        flash(f"Department '{new_dept.Name_}' added successfully!", 'success')
    except IntegrityError:
        db.session.rollback()
        flash(f"Error: Department ID {request.form['department_id']} already exists.", 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f"Error adding department: {e}", 'danger')
    
    return redirect(url_for('manage_departments'))

@app.route('/department/<int:department_id>/delete', methods=['POST'])
def delete_department(department_id):
    """Deletes a department."""
    try:
        dept = Department.query.get_or_404(department_id)
        db.session.delete(dept)
        db.session.commit()
        flash(f"Department '{dept.Name_}' has been deleted.", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting department: {e}. It may have doctors assigned to it.', 'danger')
    return redirect(url_for('manage_departments'))

# --- 9. MEDICINE CRUD ROUTES ---

@app.route('/medicines')
def manage_medicines():
    """Displays all medicines and a form to add new ones."""
    medicines = Medicine.query.order_by(Medicine.Name_).all()
    return render_template('manage_medicines.html', medicines=medicines)

@app.route('/medicine/add', methods=['POST'])
def add_medicine():
    """Handles adding a new medicine."""
    try:
        expiry = datetime.strptime(request.form['expiry_date'], '%Y-%m-%d').date()
        
        new_med = Medicine(
            Medicine_ID=int(request.form['medicine_id']),
            Name_=request.form['name'],
            Dosage=request.form.get('dosage'),
            Expiry_Date=expiry,
            Manufacturer=request.form.get('manufacturer')
        )
        db.session.add(new_med)
        db.session.commit()
        flash(f"Medicine '{new_med.Name_}' added successfully!", 'success')
    except IntegrityError:
        db.session.rollback()
        flash(f"Error: Medicine ID {request.form['medicine_id']} already exists.", 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f"Error adding medicine: {e}", 'danger')
    
    return redirect(url_for('manage_medicines'))

@app.route('/medicine/<int:medicine_id>/delete', methods=['POST'])
def delete_medicine(medicine_id):
    """Deletes a medicine."""
    try:
        med = Medicine.query.get_or_404(medicine_id)
        db.session.delete(med)
        db.session.commit()
        flash(f"Medicine '{med.Name_}' has been deleted.", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting medicine: {e}.', 'danger')
    return redirect(url_for('manage_medicines'))

# --- 10. DISEASE CRUD ROUTES ---

@app.route('/diseases')
def manage_diseases():
    """Displays all diseases and a form to add new ones."""
    diseases = Disease.query.order_by(Disease.Name_).all()
    return render_template('manage_diseases.html', diseases=diseases)

@app.route('/disease/add', methods=['POST'])
def add_disease():
    """Handles adding a new disease."""
    try:
        new_disease = Disease(
            Disease_ID=int(request.form['disease_id']),
            Category=request.form.get('category'),
            Name_=request.form['name']
        )
        db.session.add(new_disease)
        db.session.commit()
        flash(f"Disease '{new_disease.Name_}' added successfully!", 'success')
    except IntegrityError:
        db.session.rollback()
        flash(f"Error: Disease ID {request.form['disease_id']} already exists.", 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f"Error adding disease: {e}", 'danger')
    
    return redirect(url_for('manage_diseases'))

@app.route('/disease/<int:disease_id>/delete', methods=['POST'])
def delete_disease(disease_id):
    """Deletes a disease."""
    try:
        disease = Disease.query.get_or_404(disease_id)
        db.session.delete(disease)
        db.session.commit()
        flash(f"Disease '{disease.Name_}' has been deleted.", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting disease: {e}. It may be assigned to patients.', 'danger')
    return redirect(url_for('manage_diseases'))
@app.route('/doctor_analytics')
def doctor_analytics():
    """Renders a page showing doctor workload using the SQL Aggregate VIEW."""
    
    # Query the VIEW directly. SQLAlchemy treats the view like a read-only table/model.
    workload_data = View_Doctor_Appointment_Counts.query.all()
    
    return render_template('doctor_analytics.html', workload_data=workload_data)
 

from sqlalchemy.orm import Session
from sqlalchemy import text as db_text # Ensure this is imported for db.text

from sqlalchemy.orm import Session
from sqlalchemy import text as db_text # Ensure this import is present

# --- Fixed Flask Route ---
@app.route('/detailed_appointments')
def detailed_appointments():
    """Renders a report of all appointments using the SQL JOIN Procedure."""
    
    detailed_data = [] # Initialize defensively

    try:
        with Session(db.engine) as session:
            # Execute the stored procedure
            result_proxy = session.execute(db_text('CALL GetDetailedAppointments()'))
            
            # 1. CRITICAL: Fetch all rows into a list first (consumes the proxy)
            rows = result_proxy.fetchall()
            
            # 2. FIX: Map the fetched rows by column name, iterating over the 'rows' list
            detailed_data = [
                DetailedAppointmentResult(
                    Appointment_ID=row.Appointment_ID,
                    Date_Time=row.Date_Time,
                    Patient_Fname=row.Patient_Fname,
                    Patient_Lname=row.Patient_Lname,
                    Doctor_Fname=row.Doctor_Fname,
                    Doctor_Lname=row.Doctor_Lname
                )
                for row in rows # <-- CORRECTED: Iterate over 'rows'
            ]
            
    except Exception as e:
        # If the database call fails, flash a message
        # NOTE: Ensure you have 'from flask import flash' if you use this.
        # flash(f"Error running Detailed Appointments Query. Check SQL Procedure. Details: {e}", 'danger')
        print(f"Database execution failed for Detailed Appts: {e}")
        
    return render_template('detailed_appointments.html', detailed_data=detailed_data)

@app.route('/doctors_by_disease/<int:disease_id>')
@app.route('/doctors_by_disease', defaults={'disease_id': 2})
def doctors_by_disease(disease_id):
    """Renders a report of doctors treating a specific disease using the SQL Nested Query Procedure."""
    
    # 1. Initialize variables defensively
    disease_name = f"Unknown Disease (ID: {disease_id})"
    doctors_data = [] # <--- INITIALIZED HERE TO PREVENT NAMERROR

    # Get the disease name from the database (Assuming the Disease Model is defined and works)
    try:
        disease = Disease.query.get(disease_id)
        if disease:
            disease_name = disease.Name_ 
    except Exception as e:
        print(f"Error fetching disease name: {e}") 

    # 2. Database Execution and Mapping wrapped in try/except
    try:
        with Session(db.engine) as session:
            result_proxy = session.execute(
                db_text('CALL FindDoctorsByDisease(:id)'), 
                {'id': disease_id}
            )
            
            # This line will only run if the execution succeeds
            doctors_data = [
                DoctorByDiseaseResult(
                    Doctor_ID=row.Doctor_ID,
                    Fname=row.Fname,
                    Lname=row.Lname,
                    Specialization=row.Specialization
                )
                for row in result_proxy
            ]
            
    except Exception as e:
        # If the database call fails, flash a message instead of crashing
        flash(f"Error running Nested Query: The SQL Procedure might be missing or broken. Details: {e}", 'danger')
        print(f"Database execution failed: {e}") # Print error to console
        
    # The return statement works now because doctors_data and disease_name are always defined
    return render_template('doctors_by_disease.html', 
                           doctors_data=doctors_data,
                           disease_name=disease_name)
   
if __name__ == '__main__':
    with app.app_context():
        initialize_database()
    app.run(debug=True)