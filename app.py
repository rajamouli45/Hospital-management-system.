from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from datetime import date, datetime, timedelta
from decimal import Decimal
from flask_mysql_connector import MySQL

app = Flask(__name__)
app.secret_key = "super_secret_key"
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=4)

# ----------------- DATABASE CONFIGURATION -----------------
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'mouli2365'
app.config['MYSQL_DATABASE'] = 'hospital1'

mysql = MySQL(app)

# ----------------- ADMIN CREDENTIALS (Single Admin) -----------------
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# ----------------- LOGIN OPTIONS -----------------
@app.route('/')
def home_page():
    return render_template('home_page.html')


@app.route('/loginas')
def login_as():
    return render_template('loginas.html')

# ----------------- LOGIN PAGES -----------------
@app.route('/adminlogin')
def admin_login_page():
    return render_template('admin_login.html')

@app.route('/doctorlogin')
def doctor_login_page():
    return render_template('doctor_login.html')

@app.route('/patientlogin')
def patient_login_page():
    return render_template('patient_login.html')

@app.route('/add_patient')
def add_patient_page():
    return render_template('add_patient.html')

# ----------------- ADMIN LOGIN -----------------
@app.route('/admin_login', methods=['POST'])
def admin_login():
    username = request.form.get('adminId')
    password = request.form.get('password')

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session['admin_logged_in'] = True
        session['admin_name'] = "Administrator"
        flash("Admin login successful!", "success")
        return redirect(url_for('admin_home'))
    else:
        flash("Invalid admin credentials!", "danger")
        return redirect(url_for('admin_login_page'))

@app.route('/admin_home')
def admin_home():
    if not session.get('admin_logged_in'):
        flash("Please log in as admin first.", "warning")
        return redirect(url_for('admin_login_page'))
    return render_template('admin_home.html', admin_name=session.get('admin_name', 'Admin'))

# ----------------- DOCTOR LOGIN -----------------
@app.route('/doctor_login', methods=['POST'])
def doctor_login():
    doctor_id = request.form.get('doctorId')
    password = request.form.get('password')

    cur = mysql.connection.cursor(dictionary=True)
    cur.execute("SELECT * FROM DOCTOR WHERE DoctorID = %s", (doctor_id,))
    doctor = cur.fetchone()
    cur.close()

    if doctor and doctor['Password'] == password:
        session['doctor_id'] = doctor['DoctorID']
        session['doctor_name'] = doctor['Name']
        flash(f"Welcome Dr. {doctor['Name']}!", "success")
        # ✅ Redirect to doctor details page after successful login
        return redirect(url_for('doctor_profile'))

    flash("Invalid doctor credentials", "danger")
    return redirect(url_for('doctor_login_page'))

# ----------------- PATIENT LOGIN -----------------
@app.route('/patient_login', methods=['POST'])
def patient_login():
    patient_id = request.form.get('patientId')
    password = request.form.get('password')

    cur = mysql.connection.cursor(dictionary=True)
    cur.execute("SELECT * FROM PATIENT WHERE PatientID = %s", (patient_id,))
    patient = cur.fetchone()
    cur.close()

    if patient and patient['Password'] == password:
        session['patient_id'] = patient['PatientID']
        session['patient_name'] = patient['Name']
        return redirect(url_for('user_home'))
    flash("Invalid patient credentials", "danger")
    return redirect(url_for('patient_login_page'))

@app.route('/user_home')
def user_home():
    if 'patient_id' not in session:
        flash("Please log in as patient first.", "warning")
        return redirect(url_for('patient_login_page'))
    return render_template('user_home.html', patient_name=session.get('patient_name', 'Patient'))

# ----------------- ADD PATIENT -----------------
@app.route('/add_patient_record', methods=['POST'])
def add_patient_record():
    try:
        name = request.form.get('patientName')
        gender = request.form.get('gender')
        dob = request.form.get('dob')
        phone = request.form.get('phone')
        email = request.form.get('email')
        blood = request.form.get('bloodGroup')
        adm_date = request.form.get('admissionDate')
        emergency = request.form.get('emergencyContact')

        # ⭐ Auto Patient ID
        patient_id = generate_patient_id()

        # ⭐ If logged in doctor adds → assign HIS ID
        if "doctor_id" in session:
            doctor_id = session["doctor_id"]
        else:
            doctor_id = request.form.get('doctorId')  # Admin manually chooses doctor

        cur = mysql.connection.cursor()
        query = """
            INSERT INTO PATIENT
            (PatientID, Name, Gender, DOB, Phone, Email, BloodGroup,
             AdmissionDate, EmergencyContact, doctor_DoctorID, Password)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """
        
        cur.execute(query, (patient_id, name, gender, dob, phone, email, blood,
                            adm_date, emergency, doctor_id, "1234"))   # default password
        
        mysql.connection.commit()
        cur.close()

        flash(f"Patient {name} added successfully with ID {patient_id}", "success")
        return redirect(url_for('patient_details'))

    except Exception as e:
        flash(str(e), "danger")
        return redirect(url_for('add_patient_page'))
    
# ----------------- ADD DOCTOR -----------------

@app.route('/add_doctor')
def add_doctor_page():
    return render_template('add_doctor.html')


@app.route('/add_doctor_record', methods=['POST'])
def add_doctor_record():
    try:
        name = request.form.get('name')
        gender = request.form.get('gender')
        phone = request.form.get('phone')
        email = request.form.get('email')
        qualification = request.form.get('qualification')
        specialization = request.form.get('specialization')
        joining = request.form.get('joiningDate')
        dept = request.form.get('dept')

        doc_id = generate_doctor_id()

        cur = mysql.connection.cursor()
        query = """
           INSERT INTO DOCTOR
           (DoctorID, Name, Gender, Phone, Email, Qualification, Specialization,
            JoiningDate, dept_DepartmentID, Password)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """

        cur.execute(query, (doc_id, name, gender, phone, email, qualification,
                            specialization, joining, dept, "pass123"))
        mysql.connection.commit()
        cur.close()

        flash(f"Doctor {name} added successfully with ID {doc_id}", "success")
        return redirect(url_for('doctor_details'))

    except Exception as e:
        flash(str(e), "danger")
        return redirect(url_for('add_doctor_page'))



# ----------------- LOGOUT -----------------
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('login_as'))

# ----------------- EXISTING ROUTES -----------------

# ---------- PATIENT ----------
@app.route('/patients')
def patient_details():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM PATIENT")
    patients = cur.fetchall()
    cur.close()
    return render_template('patient_details.html', patients=patients)

# ---------- DOCTOR ----------
@app.route('/doctors')
def doctor_details():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM DOCTOR")
    doctors = cur.fetchall()
    cur.close()
    return render_template('doctor_details.html', doctors=doctors)

# ---------- STAFF ----------
@app.route('/staff')
def staff_details():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM STAFF")
    staff = cur.fetchall()
    cur.close()
    return render_template('staff_details.html', staff=staff)

# ---------- DEPARTMENT ----------
@app.route('/departments')
def department_details():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM DEPARTMENT")
    departments = cur.fetchall()
    cur.close()
    return render_template('department_details.html', departments=departments)

# ---------- ROOM ----------
@app.route('/rooms')
def room_details():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM ROOM")
    rooms = cur.fetchall()
    cur.close()
    return render_template('room_details.html', rooms=rooms)

# ---------- MEDICINE ----------
@app.route('/medicines')
def medicine_details():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM MEDICINE")
    medicines = cur.fetchall()
    cur.close()
    return render_template('medicine_details.html', medicines=medicines)

# ---------- ADMISSION ----------
@app.route('/admissions')
def admission_details():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM ADMISSION")
    admissions = cur.fetchall()
    cur.close()
    return render_template('admission_details.html', admissions=admissions)

# ---------- APPOINTMENT ----------
@app.route('/appointments')
def appointment_details():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM APPOINTMENT")
    appointments = cur.fetchall()
    cur.close()
    return render_template('appointment_details.html', appointments=appointments)

# ---------- BILL ----------
@app.route('/bills')
def bill_details():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM BILL")
    bills = cur.fetchall()
    cur.close()
    return render_template('bill_details.html', bills=bills)

# ---------- PRESCRIPTION ----------
@app.route('/prescriptions')
def prescription_details():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM PRESCRIPTION")
    prescriptions = cur.fetchall()
    cur.close()
    return render_template('prescription_details.html', prescriptions=prescriptions)

# ---------- PAST APPOINTMENTS ----------
@app.route('/past_appointments')
def past_appointments_page():
    return render_template('past_appointments.html')

@app.route('/get_past_appointments', methods=['POST'])
def get_past_appointments():
    try:
        data = request.get_json()
        patient_id = data.get('patientId', '').strip()
        cur = mysql.connection.cursor()
        query = """
            SELECT AppointmentID, AppointmentDate, AppointmentTime, Reason, Status, ConsultationFee, doctor_DoctorID, patient_PatientID
            FROM APPOINTMENT
            WHERE LOWER(patient_PatientID) = LOWER(%s)
            ORDER BY AppointmentDate DESC;
        """
        cur.execute(query, (patient_id,))
        appointments = cur.fetchall()
        cur.close()

        if not appointments:
            return jsonify({"success": False, "message": "No past appointments found."})

        columns = [
            'appointment_id', 'appointment_date', 'appointment_time',
            'reason', 'status', 'consultation_fee', 'doctor_id', 'patient_id'
        ]
        appointments_list = []
        for row in appointments:
            row_dict = dict(zip(columns, row))
            for key, value in row_dict.items():
                if isinstance(value, (date, datetime, timedelta)):
                    row_dict[key] = str(value)
                elif isinstance(value, Decimal):
                    row_dict[key] = float(value)
            appointments_list.append(row_dict)
        return jsonify({"success": True, "appointments": appointments_list})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)})

# ---------- SYSTEM INSIGHTS ----------
@app.route('/system_insights')
def system_insights_page():
    return render_template('system_insights.html')

@app.route('/system_insights_data')
def system_insights_data():
    try:
        cur = mysql.connection.cursor(dictionary=True)

        # 1️⃣ Department with the Highest Average Staff Salary
        cur.execute("""
            SELECT DeptName
            FROM DEPARTMENT
            WHERE DeptID = (
                SELECT dept_DepartmentID
                FROM STAFF
                GROUP BY dept_DepartmentID
                ORDER BY AVG(Salary) DESC
                LIMIT 1
            );
        """)
        highest_avg_salary_dept = cur.fetchone()

        # 2️⃣ Medicines That Have Low Stock (Below Average)
        cur.execute("""
            SELECT MedicineName, StockQuantity
            FROM MEDICINE
            WHERE StockQuantity < (
                SELECT AVG(StockQuantity)
                FROM MEDICINE
            );
        """)
        low_stock_meds = cur.fetchall()

        # 3️⃣ Departments with Doctors Having High Patient Loads
        cur.execute("""
            SELECT DeptName
            FROM DEPARTMENT
            WHERE DeptID IN (
                SELECT D.dept_DepartmentID
                FROM DOCTOR D
                JOIN PATIENT P ON D.DoctorID = P.doctor_DoctorID
                GROUP BY D.dept_DepartmentID
                HAVING COUNT(P.PatientID) > (
                    SELECT AVG(PatientCount)
                    FROM (
                        SELECT COUNT(PatientID) AS PatientCount
                        FROM PATIENT
                        GROUP BY doctor_DoctorID
                    ) AS AvgPatients
                )
            );
        """)
        high_load_depts = cur.fetchall()

        # 4️⃣ Doctors Who Only Have Scheduled Appointments (No Completed)
        cur.execute("""
            SELECT DoctorID, Name
            FROM DOCTOR
            WHERE DoctorID IN (
                SELECT doctor_DoctorID
                FROM APPOINTMENT
                WHERE Status = 'Scheduled'
            )
            AND DoctorID NOT IN (
                SELECT doctor_DoctorID
                FROM APPOINTMENT
                WHERE Status = 'Completed'
            );
        """)
        scheduled_only_doctors = cur.fetchall()

        cur.close()

        return jsonify({
            "success": True,
            "highest_avg_salary_dept": highest_avg_salary_dept,
            "low_stock_meds": low_stock_meds,
            "high_load_depts": high_load_depts,
            "scheduled_only_doctors": scheduled_only_doctors
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)})

# ---------- BOOK APPOINTMENT ----------
@app.route('/book_appointment_page')
def book_appointment_page():
    return render_template('book_appointment.html')

@app.route('/book_appointment', methods=['POST'])
def book_appointment():
    try:
        data = request.get_json()
        appointment_date = data.get("appointment_date")
        appointment_time = data.get("appointment_time")
        reason = data.get("reason")
        status = data.get("status", "Scheduled")
        patient_id = data.get("patient_id")
        doctor_id = data.get("doctor_id")

        if not (appointment_date and appointment_time and reason and patient_id and doctor_id):
            return jsonify({"success": False, "message": "Missing required fields."})

        cur = mysql.connection.cursor()

        # ✅ Generate new AppointmentID (like 'A24004')
        cur.execute("SELECT AppointmentID FROM APPOINTMENT ORDER BY AppointmentID DESC LIMIT 1")
        last_id = cur.fetchone()

        if last_id and last_id[0].startswith('A'):
            new_num = int(last_id[0][1:]) + 1
        else:
            new_num = 24001  # Starting number

        new_appointment_id = f"A{new_num}"

        # ✅ Insert new appointment with generated ID
        query = """
            INSERT INTO APPOINTMENT 
            (AppointmentID, AppointmentDate, AppointmentTime, Reason, Status, doctor_DoctorID, patient_PatientID)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cur.execute(query, (new_appointment_id, appointment_date, appointment_time, reason, status, doctor_id, patient_id))
        mysql.connection.commit()
        cur.close()

        return jsonify({
            "success": True, 
            "message": f"Appointment booked successfully with ID {new_appointment_id}"
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)})


# ---------- PATIENT PROFILE ----------
@app.route('/patient_profile')
def patient_profile():

    if 'patient_id' not in session:
        return redirect("/patientlogin")

    pid = session['patient_id']
    cur = mysql.connection.cursor(dictionary=True)

    # Patient info
    cur.execute("SELECT * FROM PATIENT WHERE PatientID=%s", (pid,))
    patient = cur.fetchone()

    # Prescription info
    cur.execute("""
        SELECT * FROM PRESCRIPTION
        WHERE appointment_AppointmentID IN
            (SELECT AppointmentID FROM APPOINTMENT WHERE patient_PatientID=%s)
    """, (pid,))
    prescriptions = cur.fetchall()

    # Bill info
    cur.execute("SELECT * FROM BILL WHERE patient_PatientID=%s", (pid,))
    bills = cur.fetchall()

    cur.close()

    return render_template(
        "patient_details1.html",
        patient=patient,
        prescriptions=prescriptions,
        bills=bills
    )


# ---------- DOCTOR PROFILE ----------

@app.route('/doctor_profile')
def doctor_profile():
    if 'doctor_id' not in session:
        flash("Please login as doctor first!", "warning")
        return redirect(url_for('doctor_login_page'))

    doctor_id = session['doctor_id']

    cur = mysql.connection.cursor(dictionary=True)

    # Fetch doctor’s own details
    cur.execute("SELECT * FROM DOCTOR WHERE DoctorID = %s", (doctor_id,))
    doctor = cur.fetchone()

    # Fetch all patients assigned to this doctor
    cur.execute("""
        SELECT PatientID, Name, Gender, Phone, Email, BloodGroup, AdmissionDate 
        FROM PATIENT
        WHERE doctor_DoctorID = %s
    """, (doctor_id,))
    patients = cur.fetchall()

    cur.close()

    return render_template("doctor_details1.html", doctor=doctor, patients=patients)

# ---------- GENERATE PATIENT ID----------

def generate_patient_id():
    cur = mysql.connection.cursor()
    cur.execute("SELECT PatientID FROM PATIENT ORDER BY PatientID DESC LIMIT 1")
    last_id = cur.fetchone()
    cur.close()

    if last_id:
        num = int(last_id[0][2:]) + 1   # Skip P2 prefix
    else:
        num = 401                       # First patient => P24001

    return f"P2{num}"

# ----------GENERATE DOCTOR ID ----------

def generate_doctor_id():
    cur = mysql.connection.cursor()
    cur.execute("SELECT DoctorID FROM DOCTOR ORDER BY DoctorID DESC LIMIT 1")
    last_id = cur.fetchone()
    cur.close()

    if last_id:
        num = int(last_id[0][3:]) + 1
    else:
        num = 1
    return f"DOC{num:03d}"


# ----------------- RUN SERVER -----------------
if __name__ == '__main__':
    app.run(debug=True)
