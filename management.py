# app.py - Hospital Management System with Full Responsive Mobile Design
import streamlit as st
import sqlite3
import pandas as pd
import re
from datetime import datetime

# ================= PAGE CONFIG - MOBILE OPTIMIZED =================
st.set_page_config(
    page_title="Hospital Management System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="auto"  # Collapses on mobile
)

# ================= RESPONSIVE CSS FOR MOBILE & DESKTOP =================
st.markdown("""
<style>
    /* Mobile-first base styles */
    .main-header {
        font-size: 40px;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin: 20px 0;
    }

    .section-header {
        font-size: 28px;
        color: #1565c0;
        margin: 30px 0 20px 0;
    }

    .form-box {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin-bottom: 30px;
    }

    /* Touch-friendly buttons */
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        border-radius: 12px;
        padding: 16px;
        font-size: 18px;
        width: 100%;
        margin: 10px 0;
        min-height: 60px;
    }

    .delete-btn > button {
        background-color: #f44336;
    }

    .update-btn > button {
        background-color: #ff9800;
    }

    /* Responsive inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div {
        font-size: 16px;
        padding: 12px;
        border-radius: 10px;
    }

    /* Stack columns on mobile */
    @media (max-width: 768px) {
        .main-header { font-size: 32px; }
        .section-header { font-size: 24px; }
        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
        }
        .stDataFrame {
            font-size: 14px;
        }
    }

    /* Horizontal scroll for tables on mobile */
    .stDataFrame > div > div {
        overflow-x: auto;
    }

    /* Better spacing on mobile */
    .block-container {
        padding: 1rem;
    }

    /* Make sidebar icons larger on mobile */
    .css-1d391kg a {
        font-size: 18px;
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
        CREATE TABLE IF NOT EXISTS Pharmacy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medicine_name TEXT,
            stock INTEGER,
            price REAL
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
st.sidebar.markdown("<h2 style='color:#1E88E5; text-align:center;'>🏥 HMS</h2>", unsafe_allow_html=True)
menu = st.sidebar.radio("Navigation", [
    "🏠 Dashboard",
    "👥 Patients",
    "👨‍⚕️ Doctors",
    "🗓️ Appointments",
    "📋 Medical Records",
    "💊 Pharmacy",
    "💰 Billing"
])

# ================= DASHBOARD - RESPONSIVE =================
if menu == "🏠 Dashboard":
    st.markdown('<div class="main-header">🏥 Hospital Dashboard</div>', unsafe_allow_html=True)

    # Responsive metrics grid
    metrics = [
        ("👥 Patients", len(query("SELECT * FROM Patients"))),
        ("👨‍⚕️ Doctors", len(query("SELECT * FROM Doctors"))),
        ("🗓️ Appointments", len(query("SELECT * FROM Appointments"))),
        ("💊 Medicines", len(query("SELECT * FROM Pharmacy"))),
        ("💰 Revenue", f"${query('SELECT COALESCE(SUM(amount), 0) FROM Billings').iloc[0,0]:,.2f}")
    ]

    # Responsive columns (stack on mobile)
    cols = st.columns(min(len(metrics), 5))
    for i, (label, value) in enumerate(metrics):
        with cols[i % len(cols)]:
            st.metric(label, value)

    st.success("System optimized for mobile & desktop!")

# ================= PATIENTS - RESPONSIVE CRUD =================
elif menu == "👥 Patients":
    st.markdown('<div class="main-header">👥 Patients Management</div>', unsafe_allow_html=True)

    # Search - full width on mobile
    search = st.text_input("🔍 Search by Name, CNIC, or Phone", placeholder="Enter search term")
    if st.button("Search", type="primary", use_container_width=True):
        if search:
            patients_df = query("SELECT * FROM Patients WHERE name LIKE ? OR cnic LIKE ? OR phone LIKE ?", 
                                (f"%{search}%", f"%{search}%", f"%{search}%"))
        else:
            patients_df = query("SELECT * FROM Patients")
    else:
        patients_df = query("SELECT * FROM Patients")

    st.subheader("All Patients")
    st.dataframe(patients_df, use_container_width=True)

    # Add Patient - responsive form
    st.markdown('<div class="form-box">', unsafe_allow_html=True)
    st.markdown('<h3 class="section-header">➕ Add New Patient</h3>', unsafe_allow_html=True)
    with st.form("add_patient_form", clear_on_submit=True):
        # Stack columns on mobile
        col1, col2 = st.columns([1, 1])
        with col1:
            name = st.text_input("Full Name *")
            cnic = st.text_input("CNIC *")
        with col2:
            phone = st.text_input("Phone *")
            age = st.number_input("Age", min_value=0, max_value=120)

        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        address = st.text_area("Address")

        if st.form_submit_button("Add Patient", type="primary", use_container_width=True):
            if name and cnic and phone:
                try:
                    execute("INSERT INTO Patients (name, cnic, phone, age, gender, address) VALUES (?, ?, ?, ?, ?, ?)",
                            (name, cnic, phone, age, gender, address))
                    st.success("Patient added successfully!")
                    st.rerun()
                except:
                    st.error("CNIC already exists!")
            else:
                st.error("Required fields missing!")

    # Update/Delete - responsive
    st.markdown('<h3 class="section-header">✏️ Update / Delete Patient</h3>', unsafe_allow_html=True)
    patient_ids = query("SELECT id FROM Patients")["id"].tolist()
    if patient_ids:
        selected_id = st.selectbox("Select Patient ID", patient_ids, key="patient_select")
        pat = query("SELECT * FROM Patients WHERE id = ?", (selected_id,)).iloc[0]

        with st.form("update_patient_form"):
            col1, col2 = st.columns([1, 1])
            with col1:
                upd_name = st.text_input("Name", value=pat["name"])
                upd_cnic = st.text_input("CNIC", value=pat["cnic"])
            with col2:
                upd_phone = st.text_input("Phone", value=pat["phone"])
                upd_age = st.number_input("Age", value=int(pat["age"] or 0))

            upd_gender = st.selectbox("Gender", ["Male", "Female", "Other"], index=["Male", "Female", "Other"].index(pat["gender"] or "Male"))
            upd_address = st.text_area("Address", value=pat["address"] or "")

            col_u, col_d = st.columns([1, 1])
            if col_u.form_submit_button("Update Patient", type="primary", use_container_width=True):
                execute("UPDATE Patients SET name=?, cnic=?, phone=?, age=?, gender=?, address=? WHERE id=?",
                        (upd_name, upd_cnic, upd_phone, upd_age, upd_gender, upd_address, selected_id))
                st.success("Patient updated!")
                st.rerun()

            if col_d.form_submit_button("Delete Patient", type="secondary", use_container_width=True):
                execute("DELETE FROM Patients WHERE id=?", (selected_id,))
                st.success("Patient deleted!")
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ================= OTHER MODULES (Doctors, Appointments, etc.) =================
# (Keep your existing code with the same responsive patterns)

# ================= FOOTER =================
st.markdown("---")
st.markdown("<center style='color:#666; margin-top:50px;'>© 2025 Hospital Management System • Mobile-Optimized with ❤️</center>", unsafe_allow_html=True)
