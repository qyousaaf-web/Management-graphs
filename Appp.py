import streamlit as st
import sqlite3
import pandas as pd
import re
from datetime import datetime

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Hospital Management System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= CUSTOM CSS =================
st.markdown("""
<style>
    .main-header {
        font-size: 48px;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 30px;
    }
    .section-header {
        font-size: 28px;
        color: #1565c0;
        margin-top: 40px;
    }
    .form-box {
        background-color: #f8f9fa;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin-bottom: 30px;
    }
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 12px;
    }
    .delete-btn > button {
        background-color: #f44336;
    }
    .search-box {
        background-color: #f0f8ff;
        padding: 20px;
        border-radius: 12px;
        border-left: 6px solid #2196F3;
        margin-bottom: 30px;
    }
</style>
""", unsafe_allow_html=True)

# ================= DATABASE =================
DB = "hospital.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS Patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            cnic TEXT UNIQUE,
            phone TEXT
        );
        CREATE TABLE IF NOT EXISTS Doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            cnic TEXT UNIQUE,
            department TEXT
        );
        CREATE TABLE IF NOT EXISTS Appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient TEXT,
            patient_cnic TEXT,
            doctor TEXT,
            doctor_cnic TEXT,
            date TEXT,
            time TEXT,
            status TEXT
        );
        CREATE TABLE IF NOT EXISTS MedicalRecords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient TEXT,
            patient_cnic TEXT,
            doctor TEXT,
            diagnosis TEXT,
            treatment TEXT,
            prescription TEXT,
            date TEXT
        );
        CREATE TABLE IF NOT EXISTS Billings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient TEXT,
            patient_cnic TEXT,
            amount REAL,
            details TEXT,
            status TEXT
        );
    ''')
    conn.commit()
    conn.close()

init_db()

# ================= HELPERS =================
def query(sql, params=()):
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df

def execute(sql, params=()):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(sql, params)
    conn.commit()
    conn.close()

# ================= SIDEBAR =================
st.sidebar.markdown("<h2 style='color:#1E88E5;'>🏥 Hospital System</h2>", unsafe_allow_html=True)
menu = st.sidebar.radio("Navigate", ["Dashboard", "Patients", "Doctors", "Appointments", "Medical Records", "Billings"])

# ================= DASHBOARD =================
if menu == "Dashboard":
    st.markdown('<div class="main-header">🏥 Hospital Dashboard</div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Patients", len(query("SELECT * FROM Patients")))
    col2.metric("Doctors", len(query("SELECT * FROM Doctors")))
    col3.metric("Appointments", len(query("SELECT * FROM Appointments")))
    col4.metric("Bills", len(query("SELECT * FROM Billings")))
    st.success("Dashboard loaded successfully!")

# ================= PATIENTS =================
elif menu == "Patients":
    st.markdown('<div class="main-header">👥 Patients Management</div>', unsafe_allow_html=True)

    # Search
    st.markdown('<div class="search-box">', unsafe_allow_html=True)
    st.subheader("🔍 Search Patient")
    search = st.text_input("Enter Name, CNIC, or Phone")
    if st.button("Search Patient", type="primary"):
        if search:
            patients_df = query("SELECT * FROM Patients WHERE name LIKE ? OR cnic LIKE ? OR phone LIKE ?", 
                                (f"%{search}%", f"%{search}%", f"%{search}%"))
        else:
            patients_df = query("SELECT * FROM Patients")
    else:
        patients_df = query("SELECT * FROM Patients")
    st.markdown('</div>', unsafe_allow_html=True)

    st.subheader("All Patients")
    st.dataframe(patients_df, use_container_width=True)

    # Add Patient
    st.markdown('<div class="form-box">', unsafe_allow_html=True)
    st.markdown('<h3 class="section-header">➕ Add New Patient</h3>', unsafe_allow_html=True)
    with st.form("add_patient_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name *")
            cnic = st.text_input("CNIC (xxxxx-xxxxxxx-x) *")
        with col2:
            phone = st.text_input("Phone Number *")
        submitted = st.form_submit_button("Add Patient", type="primary")
        if submitted:
            if name and cnic and phone:
                try:
                    execute("INSERT INTO Patients (name, cnic, phone) VALUES (?, ?, ?)", (name, cnic, phone))
                    st.success("Patient added successfully!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("CNIC already exists!")
            else:
                st.error("All fields are required!")

    # Update/Delete Patient
    st.markdown('<h3 class="section-header">✏️ Update or Delete Patient</h3>', unsafe_allow_html=True)
    patient_ids = query("SELECT id FROM Patients")["id"].tolist()
    if patient_ids:
        selected_id = st.selectbox("Select Patient ID", patient_ids)
        pat = query("SELECT * FROM Patients WHERE id = ?", (selected_id,)).iloc[0]
        with st.form("update_patient_form"):
            col1, col2 = st.columns(2)
            with col1:
                upd_name = st.text_input("Name", value=pat["name"])
                upd_cnic = st.text_input("CNIC", value=pat["cnic"])
            with col2:
                upd_phone = st.text_input("Phone", value=pat["phone"])
            col_u, col_d = st.columns(2)
            update = col_u.form_submit_button("Update Patient")
            delete = col_d.form_submit_button("Delete Patient", type="secondary")
            if update:
                execute("UPDATE Patients SET name=?, cnic=?, phone=? WHERE id=?", (upd_name, upd_cnic, upd_phone, selected_id))
                st.success("Patient updated!")
                st.rerun()
            if delete:
                execute("DELETE FROM Patients WHERE id=?", (selected_id,))
                st.success("Patient deleted!")
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ================= DOCTORS =================
elif menu == "Doctors":
    st.markdown('<div class="main-header">👨‍⚕️ Doctors Management</div>', unsafe_allow_html=True)

    # Search
    st.markdown('<div class="search-box">', unsafe_allow_html=True)
    st.subheader("🔍 Search Doctor")
    search = st.text_input("Enter Name or CNIC")
    if st.button("Search Doctor", type="primary"):
        if search:
            doctors_df = query("SELECT * FROM Doctors WHERE name LIKE ? OR cnic LIKE ?", (f"%{search}%", f"%{search}%"))
        else:
            doctors_df = query("SELECT * FROM Doctors")
    else:
        doctors_df = query("SELECT * FROM Doctors")
    st.markdown('</div>', unsafe_allow_html=True)

    st.subheader("All Doctors")
    st.dataframe(doctors_df, use_container_width=True)

    # Add Doctor
    st.markdown('<div class="form-box">', unsafe_allow_html=True)
    st.markdown('<h3 class="section-header">➕ Add New Doctor</h3>', unsafe_allow_html=True)
    with st.form("add_doctor_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name *")
            cnic = st.text_input("CNIC *")
        with col2:
            dept = st.text_input("Department *")
        submitted = st.form_submit_button("Add Doctor", type="primary")
        if submitted:
            if name and cnic and dept:
                try:
                    execute("INSERT INTO Doctors (name, cnic, department) VALUES (?, ?, ?)", (name, cnic, dept))
                    st.success("Doctor added!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("CNIC already exists!")
            else:
                st.error("All fields required!")

    # Update/Delete Doctor
    st.markdown('<h3 class="section-header">✏️ Update or Delete Doctor</h3>', unsafe_allow_html=True)
    doctor_ids = query("SELECT id FROM Doctors")["id"].tolist()
    if doctor_ids:
        selected_id = st.selectbox("Select Doctor ID", doctor_ids)
        doc = query("SELECT * FROM Doctors WHERE id = ?", (selected_id,)).iloc[0]
        with st.form("update_doctor_form"):
            col1, col2 = st.columns(2)
            with col1:
                upd_name = st.text_input("Name", value=doc["name"])
                upd_cnic = st.text_input("CNIC", value=doc["cnic"])
            with col2:
                upd_dept = st.text_input("Department", value=doc["department"])
            col_u, col_d = st.columns(2)
            update = col_u.form_submit_button("Update Doctor")
            delete = col_d.form_submit_button("Delete Doctor", type="secondary")
            if update:
                execute("UPDATE Doctors SET name=?, cnic=?, department=? WHERE id=?", (upd_name, upd_cnic, upd_dept, selected_id))
                st.success("Doctor updated!")
                st.rerun()
            if delete:
                execute("DELETE FROM Doctors WHERE id=?", (selected_id,))
                st.success("Doctor deleted!")
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ================= APPOINTMENTS =================
elif menu == "Appointments":
    st.markdown('<div class="main-header">🗓️ Appointments Management</div>', unsafe_allow_html=True)

    # Search
    st.markdown('<div class="search-box">', unsafe_allow_html=True)
    st.subheader("🔍 Search Appointment")
    search_cnic = st.text_input("Patient CNIC")
    search_date = st.date_input("Date", value=None)
    search_btn = st.button("Search Appointment", type="primary")
    st.markdown('</div>', unsafe_allow_html=True)

    sql = "SELECT * FROM Appointments"
    params = ()
    if search_btn:
        conditions = []
        if search_cnic:
            conditions.append("patient_cnic LIKE ?")
            params += (f"%{search_cnic}%",)
        if search_date:
            conditions.append("date = ?")
            params += (str(search_date),)
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

    appointments_df = query(sql, params)
    st.subheader("All Appointments")
    st.dataframe(appointments_df, use_container_width=True)

    # Add Appointment
    st.markdown('<div class="form-box">', unsafe_allow_html=True)
    st.markdown('<h3 class="section-header">➕ Schedule Appointment</h3>', unsafe_allow_html=True)
    with st.form("add_appointment_form"):
        col1, col2 = st.columns(2)
        with col1:
            patient_cnic = st.text_input("Patient CNIC *")
            doctor_cnic = st.text_input("Doctor CNIC *")
        with col2:
            date = st.date_input("Date *")
            time = st.time_input("Time *")
        status = st.selectbox("Status", ["Scheduled", "Confirmed", "Cancelled"])

        submitted = st.form_submit_button("Schedule Appointment", type="primary")
        if submitted:
            if patient_cnic and doctor_cnic:
                pat = query("SELECT name FROM Patients WHERE cnic=?", (patient_cnic,))
                doc = query("SELECT name FROM Doctors WHERE cnic=?", (doctor_cnic,))
                if not pat.empty and not doc.empty:
                    execute("INSERT INTO Appointments (patient, patient_cnic, doctor, doctor_cnic, date, time, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (pat.iloc[0]["name"], patient_cnic, doc.iloc[0]["name"], doctor_cnic, str(date), str(time), status))
                    st.success("Appointment scheduled!")
                    st.rerun()
                else:
                    st.error("Invalid CNIC!")
            else:
                st.error("Both CNICs required!")

    # Update/Delete Appointment
    st.markdown('<h3 class="section-header">✏️ Update or Delete Appointment</h3>', unsafe_allow_html=True)
    appt_ids = query("SELECT id FROM Appointments")["id"].tolist()
    if appt_ids:
        selected_id = st.selectbox("Select Appointment ID", appt_ids)
        appt = query("SELECT * FROM Appointments WHERE id = ?", (selected_id,)).iloc[0]
        with st.form("update_appointment_form"):
            col1, col2 = st.columns(2)
            with col1:
                patient_cnic = st.text_input("Patient CNIC", value=appt["patient_cnic"])
                doctor_cnic = st.text_input("Doctor CNIC", value=appt["doctor_cnic"])
            with col2:
                date = st.date_input("Date", value=pd.to_datetime(appt["date"]))
                time = st.time_input("Time", value=pd.to_datetime(appt["time"]).time())
            status = st.selectbox("Status", ["Scheduled", "Confirmed", "Cancelled"], index=["Scheduled", "Confirmed", "Cancelled"].index(appt["status"]))

            col_u, col_d = st.columns(2)
            update = col_u.form_submit_button("Update Appointment")
            delete = col_d.form_submit_button("Delete Appointment", type="secondary")

            if update:
                pat = query("SELECT name FROM Patients WHERE cnic=?", (patient_cnic,))
                doc = query("SELECT name FROM Doctors WHERE cnic=?", (doctor_cnic,))
                if not pat.empty and not doc.empty:
                    execute("UPDATE Appointments SET patient=?, patient_cnic=?, doctor=?, doctor_cnic=?, date=?, time=?, status=? WHERE id=?",
                            (pat.iloc[0]["name"], patient_cnic, doc.iloc[0]["name"], doctor_cnic, str(date), str(time), status, selected_id))
                    st.success("Updated!")
                    st.rerun()

            if delete:
                execute("DELETE FROM Appointments WHERE id=?", (selected_id,))
                st.success("Deleted!")
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ================= MEDICAL RECORDS =================
elif menu == "Medical Records":
    st.markdown('<div class="main-header">📋 Medical Records</div>', unsafe_allow_html=True)

    # Search
    st.markdown('<div class="search-box">', unsafe_allow_html=True)
    st.subheader("🔍 Search by Patient CNIC")
    search_cnic = st.text_input("Patient CNIC")
    if st.button("Search Records", type="primary"):
        if search_cnic:
            records_df = query("SELECT * FROM MedicalRecords WHERE patient_cnic = ?", (search_cnic,))
        else:
            records_df = query("SELECT * FROM MedicalRecords")
    else:
        records_df = query("SELECT * FROM MedicalRecords")
    st.markdown('</div>', unsafe_allow_html=True)

    st.subheader("All Records")
    st.dataframe(records_df, use_container_width=True)

    # Add Record
    st.markdown('<div class="form-box">', unsafe_allow_html=True)
    st.markdown('<h3 class="section-header">➕ Add Medical Record</h3>', unsafe_allow_html=True)
    with st.form("add_record_form"):
        col1, col2 = st.columns(2)
        with col1:
            patient_cnic = st.text_input("Patient CNIC *")
            doctor = st.text_input("Doctor Name *")
        with col2:
            date = st.date_input("Date *")
        diagnosis = st.text_area("Diagnosis *")
        treatment = st.text_area("Treatment")
        prescription = st.text_area("Prescription")

        submitted = st.form_submit_button("Save Record", type="primary")
        if submitted:
            if patient_cnic and doctor and diagnosis:
                pat = query("SELECT name FROM Patients WHERE cnic=?", (patient_cnic,))
                if not pat.empty:
                    execute("INSERT INTO MedicalRecords (patient, patient_cnic, doctor, diagnosis, treatment, prescription, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (pat.iloc[0]["name"], patient_cnic, doctor, diagnosis, treatment, prescription, str(date)))
                    st.success("Record added!")
                    st.rerun()
                else:
                    st.error("Patient not found!")
            else:
                st.error("Required fields missing!")

    # Update/Delete Record
    st.markdown('<h3 class="section-header">✏️ Update or Delete Record</h3>', unsafe_allow_html=True)
    record_ids = query("SELECT id FROM MedicalRecords")["id"].tolist()
    if record_ids:
        selected_id = st.selectbox("Select Record ID", record_ids)
        rec = query("SELECT * FROM MedicalRecords WHERE id = ?", (selected_id,)).iloc[0]
        with st.form("update_record_form"):
            col1, col2 = st.columns(2)
            with col1:
                patient_cnic = st.text_input("Patient CNIC", value=rec["patient_cnic"])
                doctor = st.text_input("Doctor Name", value=rec["doctor"])
            with col2:
                date = st.date_input("Date", value=pd.to_datetime(rec["date"]))
            diagnosis = st.text_area("Diagnosis", value=rec["diagnosis"])
            treatment = st.text_area("Treatment", value=rec["treatment"])
            prescription = st.text_area("Prescription", value=rec["prescription"])

            col_u, col_d = st.columns(2)
            update = col_u.form_submit_button("Update Record")
            delete = col_d.form_submit_button("Delete Record", type="secondary")

            if update:
                pat = query("SELECT name FROM Patients WHERE cnic=?", (patient_cnic,))
                if not pat.empty:
                    execute("UPDATE MedicalRecords SET patient=?, patient_cnic=?, doctor=?, diagnosis=?, treatment=?, prescription=?, date=? WHERE id=?",
                            (pat.iloc[0]["name"], patient_cnic, doctor, diagnosis, treatment, prescription, str(date), selected_id))
                    st.success("Updated!")
                    st.rerun()

            if delete:
                execute("DELETE FROM MedicalRecords WHERE id=?", (selected_id,))
                st.success("Deleted!")
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ================= BILLINGS =================
elif menu == "Billings":
    st.markdown('<div class="main-header">💰 Billing Management</div>', unsafe_allow_html=True)

    # Search
    st.markdown('<div class="search-box">', unsafe_allow_html=True)
    st.subheader("🔍 Search Bill")
    search_cnic = st.text_input("Patient CNIC")
    search_btn = st.button("Search Bill", type="primary")
    st.markdown('</div>', unsafe_allow_html=True)

    if search_btn and search_cnic:
        bills_df = query("SELECT * FROM Billings WHERE patient_cnic = ?", (search_cnic,))
    else:
        bills_df = query("SELECT * FROM Billings")

    st.subheader("All Bills")
    st.dataframe(bills_df, use_container_width=True)

    # Add Bill
    st.markdown('<div class="form-box">', unsafe_allow_html=True)
    st.markdown('<h3 class="section-header">➕ Create New Bill</h3>', unsafe_allow_html=True)
    with st.form("add_bill_form"):
        col1, col2 = st.columns(2)
        with col1:
            patient_cnic = st.text_input("Patient CNIC *")
            amount = st.number_input("Amount", min_value=0.0)
        with col2:
            details = st.text_area("Details")
            status = st.selectbox("Status", ["Pending", "Paid"])

        submitted = st.form_submit_button("Create Bill", type="primary")
        if submitted:
            if patient_cnic:
                pat = query("SELECT name FROM Patients WHERE cnic=?", (patient_cnic,))
                if not pat.empty:
                    execute("INSERT INTO Billings (patient, patient_cnic, amount, details, status) VALUES (?, ?, ?, ?, ?)",
                            (pat.iloc[0]["name"], patient_cnic, amount, details, status))
                    st.success("Bill created!")
                    st.rerun()
                else:
                    st.error("Patient not found!")
            else:
                st.error("Patient CNIC required!")

    # Update/Delete Bill
    st.markdown('<h3 class="section-header">✏️ Update or Delete Bill</h3>', unsafe_allow_html=True)
    bill_ids = query("SELECT id FROM Billings")["id"].tolist()
    if bill_ids:
        selected_id = st.selectbox("Select Bill ID", bill_ids)
        bill = query("SELECT * FROM Billings WHERE id = ?", (selected_id,)).iloc[0]
        with st.form("update_bill_form"):
            col1, col2 = st.columns(2)
            with col1:
                patient_cnic = st.text_input("Patient CNIC", value=bill["patient_cnic"])
                amount = st.number_input("Amount", value=float(bill["amount"]))
            with col2:
                details = st.text_area("Details", value=bill["details"])
                status = st.selectbox("Status", ["Pending", "Paid"], index=["Pending", "Paid"].index(bill["status"]))

            col_u, col_d = st.columns(2)
            update = col_u.form_submit_button("Update Bill")
            delete = col_d.form_submit_button("Delete Bill", type="secondary")

            if update:
                pat = query("SELECT name FROM Patients WHERE cnic=?", (patient_cnic,))
                if not pat.empty:
                    execute("UPDATE Billings SET patient=?, patient_cnic=?, amount=?, details=?, status=? WHERE id=?",
                            (pat.iloc[0]["name"], patient_cnic, amount, details, status, selected_id))
                    st.success("Bill updated!")
                    st.rerun()

            if delete:
                execute("DELETE FROM Billings WHERE id=?", (selected_id,))
                st.success("Bill deleted!")
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ================= FOOTER =================
st.markdown("---")
st.markdown("<center>© 2025 Hospital Management System • Built with ❤️ using Streamlit</center>", unsafe_allow_html=True)
