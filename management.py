# app.py - Hospital Management System with Full CRUD for Medical History
import streamlit as st
import sqlite3
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import re
from datetime import datetime

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Hospital Management System", page_icon="🏥", layout="wide")

# Set seaborn theme
sns.set_theme(style="whitegrid")

# Custom styling
st.markdown("""
<style>
    .main-header { font-size: 48px; font-weight: bold; color: #1E88E5; text-align: center; margin-bottom: 30px; }
    .metric-card { background-color: #f0f2f6; padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    .stButton>button { background-color: #4CAF50; color: white; font-weight: bold; border-radius: 8px; }
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
            name TEXT,
            cnic TEXT UNIQUE,
            phone TEXT
        );
        CREATE TABLE IF NOT EXISTS Doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            cnic TEXT UNIQUE,
            department TEXT
        );
        CREATE TABLE IF NOT EXISTS MedicalHistory (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_cnic TEXT,
            patient_name TEXT,
            doctor_name TEXT,
            diagnosis TEXT,
            treatment TEXT,
            prescription TEXT,
            visit_date TEXT,
            FOREIGN KEY(patient_cnic) REFERENCES Patients(cnic)
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

def valid_cnic(cnic):
    return re.match(r"^\d{5}-\d{7}-\d$", cnic) is not None

# ================= SIDEBAR =================
st.sidebar.markdown("<h2 style='color:#1E88E5;'>🏥 Hospital System</h2>", unsafe_allow_html=True)
menu = st.sidebar.selectbox("Navigate", ["Dashboard", "Patients", "Doctors", "Medical History"])

# ================= MEDICAL HISTORY - FULL CRUD =================
if menu == "Medical History":
    st.header("🩺 Patient Medical History")

    # Search by Patient CNIC
    search_cnic = st.text_input("🔍 Search Patient by CNIC", placeholder="xxxxx-xxxxxxx-x")
    history_df = pd.DataFrame()
    if search_cnic:
        history_df = query("SELECT * FROM MedicalHistory WHERE patient_cnic = ?", (search_cnic,))
        if history_df.empty:
            st.warning("No medical history found for this CNIC.")
        else:
            st.success(f"Found {len(history_df)} record(s) for patient: {history_df['patient_name'].iloc[0]}")

    # View All History Records for this patient
    if not history_df.empty:
        st.subheader("📋 Medical History Records")
        st.dataframe(history_df, use_container_width=True)

        # Analytics for this patient
        st.subheader("📊 Patient Visit Analytics")
        history_df['visit_date'] = pd.to_datetime(history_df['visit_date'], errors='coerce')
        visits = history_df.groupby(history_df['visit_date'].dt.to_period("M")).size().reset_index(name="Visits")
        visits['visit_date'] = visits['visit_date'].dt.to_timestamp()

        fig, ax = plt.subplots(figsize=(10, 5))
        sns.lineplot(data=visits, x="visit_date", y="Visits", marker="o", ax=ax, color="#1E88E5")
        ax.set_title("Monthly Visit Trend for This Patient")
        st.pyplot(fig)

        diag_counts = history_df['diagnosis'].value_counts().head(10)
        if not diag_counts.empty:
            fig2, ax2 = plt.subplots(figsize=(10, 5))
            sns.barplot(x=diag_counts.values, y=diag_counts.index, palette="viridis", ax=ax2)
            ax2.set_title("Most Frequent Diagnoses")
            st.pyplot(fig2)

    # Add New Record
    st.markdown("### ➕ Add New Medical Record")
    with st.form("add_history_form"):
        col1, col2 = st.columns(2)
        with col1:
            patient_cnic = st.text_input("Patient CNIC *", placeholder="xxxxx-xxxxxxx-x")
            doctor_name = st.text_input("Doctor Name *")
        with col2:
            visit_date = st.date_input("Visit Date *", value=datetime.today())

        diagnosis = st.text_area("Diagnosis *", height=120)
        treatment = st.text_area("Treatment", height=100)
        prescription = st.text_area("Prescription", height=100)

        submitted = st.form_submit_button("Save Record", type="primary")
        if submitted:
            if patient_cnic and doctor_name and diagnosis.strip():
                pat_row = query("SELECT name FROM Patients WHERE cnic = ?", (patient_cnic,))
                if not pat_row.empty:
                    patient_name = pat_row["name"].iloc[0]
                    execute("INSERT INTO MedicalHistory (patient_cnic, patient_name, doctor_name, diagnosis, treatment, prescription, visit_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (patient_cnic, patient_name, doctor_name, diagnosis, treatment, prescription, str(visit_date)))
                    st.success("Medical record added successfully!")
                    st.rerun()
                else:
                    st.error("Patient CNIC not found in database!")
            else:
                st.error("Patient CNIC, Doctor Name, and Diagnosis are required!")

    # Update / Delete Existing Record
    st.markdown("### ✏️ Update or Delete Existing Record")
    all_history = query("SELECT history_id, patient_name, visit_date, diagnosis FROM MedicalHistory")
    if not all_history.empty:
        record_ids = all_history["history_id"].tolist()
        selected_record = st.selectbox("Select Record ID to Edit/Delete", record_ids)

        if selected_record:
            record = query("SELECT * FROM MedicalHistory WHERE history_id = ?", (selected_record,)).iloc[0]

            with st.form("update_history_form"):
                col1, col2 = st.columns(2)
                with col1:
                    patient_cnic = st.text_input("Patient CNIC", value=record["patient_cnic"], disabled=True)
                    doctor_name = st.text_input("Doctor Name", value=record["doctor_name"])
                with col2:
                    visit_date = st.date_input("Visit Date", value=pd.to_datetime(record["visit_date"]))

                diagnosis = st.text_area("Diagnosis", value=record["diagnosis"], height=120)
                treatment = st.text_area("Treatment", value=record["treatment"], height=100)
                prescription = st.text_area("Prescription", value=record["prescription"], height=100)

                col_u, col_d = st.columns(2)
                update_btn = col_u.form_submit_button("Update Record", type="primary")
                delete_btn = col_d.form_submit_button("Delete Record", type="secondary")

                if update_btn:
                    execute("""UPDATE MedicalHistory 
                               SET doctor_name=?, diagnosis=?, treatment=?, prescription=?, visit_date=?
                               WHERE history_id=?""",
                            (doctor_name, diagnosis, treatment, prescription, str(visit_date), selected_record))
                    st.success("Record updated successfully!")
                    st.rerun()

                if delete_btn:
                    execute("DELETE FROM MedicalHistory WHERE history_id=?", (selected_record,))
                    st.success("Record deleted successfully!")
                    st.rerun()

# Keep your other pages (Dashboard, Patients, Doctors, Appointments, Billings) as before

st.sidebar.success("Full CRUD for Medical History Added! 🩺")
