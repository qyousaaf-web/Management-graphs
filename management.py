import streamlit as st
import sqlite3
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import re
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io
from datetime import datetime

# ================= CONFIG =================
st.set_page_config(page_title="Hospital Management System", page_icon="🏥", layout="wide")
sns.set_theme(style="whitegrid")

# ================= DATABASE =================
DB = "hospital.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS Patients(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            cnic TEXT UNIQUE,
            phone TEXT
        );
        CREATE TABLE IF NOT EXISTS Departments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        );
        CREATE TABLE IF NOT EXISTS Doctors(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            cnic TEXT UNIQUE,
            department TEXT
        );
        CREATE TABLE IF NOT EXISTS Appointments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient TEXT,
            patient_cnic TEXT,
            doctor TEXT,
            doctor_cnic TEXT,
            date TEXT,
            time TEXT,
            status TEXT
        );
        CREATE TABLE IF NOT EXISTS Billings(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient TEXT,
            patient_cnic TEXT,
            amount REAL,
            details TEXT,
            status TEXT
        );
    """)
    # Default departments
    c.execute("INSERT OR IGNORE INTO Departments(name) VALUES ('Cardiology'),('Neurology'),('Orthopedics')")
    conn.commit()
    conn.close()

init_db()

# ================= HELPERS =================
def query(sql, params=()):
    conn = sqlite3.connect(DB)
    df = pd.read_sql(sql, conn, params=params)
    conn.close()
    return df

def execute(sql, params=()):
    conn = sqlite3.connect(DB)
    conn.execute(sql, params)
    conn.commit()
    conn.close()

def valid_cnic(cnic):
    return re.match(r"^\d{5}-\d{7}-\d$", cnic)

def safe_rerun():
    st.session_state["refresh_needed"] = True

if "refresh_needed" in st.session_state and st.session_state["refresh_needed"]:
    st.session_state["refresh_needed"] = False
    st.experimental_rerun()

def export_pdf(df, title="Report", filename="report.pdf"):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = [Paragraph(title, styles["Title"])]
    data = [df.columns.tolist()] + df.values.tolist()
    table = Table(data)
    table.setStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E88E5")),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ])
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer

# ================= SIDEBAR =================
menu = st.sidebar.selectbox(
    "🏥 Navigation",
    ["Dashboard", "Patients", "Doctors", "Appointments", "Billings", "Reports"]
)

# ================= DASHBOARD =================
if menu == "Dashboard":
    st.title("🏥 Hospital Management Dashboard")
    total_patients = len(query("SELECT * FROM Patients"))
    total_doctors = len(query("SELECT * FROM Doctors"))
    total_appointments = len(query("SELECT * FROM Appointments"))
    total_revenue = query("SELECT SUM(amount) as revenue FROM Billings")["revenue"].iloc[0] or 0
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👥 Patients", total_patients)
    col2.metric("👨‍⚕️ Doctors", total_doctors)
    col3.metric("🗓️ Appointments", total_appointments)
    col4.metric("💰 Revenue", f"${total_revenue:.2f}")

    # Monthly Appointment Trend
    appt = query("SELECT * FROM Appointments")
    if not appt.empty:
        appt["date"] = pd.to_datetime(appt["date"])
        monthly = appt.groupby(appt["date"].dt.to_period("M")).size().reset_index(name="Appointments")
        monthly["date"] = monthly["date"].dt.to_timestamp()
        fig, ax = plt.subplots()
        sns.lineplot(data=monthly, x="date", y="Appointments", marker="o", ax=ax)
        ax.set_title("📈 Monthly Appointment Trend")
        st.pyplot(fig)

        # Doctor-wise Appointments
        fig2, ax2 = plt.subplots()
        sns.countplot(data=appt, y="doctor", palette="viridis", ax=ax2)
        ax2.set_title("👨‍⚕️ Doctor-wise Appointments")
        st.pyplot(fig2)

# ================= PATIENTS =================
elif menu == "Patients":
    st.header("👥 Patients Management")
    search = st.text_input("🔍 Search by CNIC or Name", key="search_patient")
    df_pat = query("SELECT * FROM Patients WHERE cnic LIKE ? OR name LIKE ?" if search else "SELECT * FROM Patients",
                   (f"%{search}%", f"%{search}%") if search else ())
    st.dataframe(df_pat)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("➕ Add Patient")
        pname = st.text_input("Name", key="add_pat_name")
        pcnic = st.text_input("CNIC (xxxxx-xxxxxxx-x)", key="add_pat_cnic")
        pphone = st.text_input("Phone", key="add_pat_phone")
        if st.button("Add Patient", key="btn_add_patient"):
            if not valid_cnic(pcnic):
                st.error("⚠️ Invalid CNIC")
            else:
                try:
                    execute("INSERT INTO Patients VALUES(NULL,?,?,?)", (pname, pcnic, pphone))
                    st.success("✅ Patient added successfully!")
                    safe_rerun()
                except sqlite3.IntegrityError:
                    st.error("⚠️ CNIC already exists!")

    with col2:
        st.subheader("✏️ Update/Delete Patient")
        pid = st.number_input("Patient ID", min_value=1, key="upd_pat_id")
        pat_row = query("SELECT * FROM Patients WHERE id=?", (pid,))
        if not pat_row.empty:
            pname = st.text_input("Name", pat_row["name"].iloc[0], key="upd_pat_name")
            pcnic = st.text_input("CNIC", pat_row["cnic"].iloc[0], key="upd_pat_cnic")
            pphone = st.text_input("Phone", pat_row["phone"].iloc[0], key="upd_pat_phone")
            ucol, dcol = st.columns(2)
            with ucol:
                if st.button("Update Patient", key="upd_patient_btn"):
                    if valid_cnic(pcnic):
                        execute("UPDATE Patients SET name=?, cnic=?, phone=? WHERE id=?", (pname, pcnic, pphone, pid))
                        st.success("✅ Patient updated")
                        safe_rerun()
            with dcol:
                if st.button("Delete Patient", key="del_patient_btn"):
                    execute("DELETE FROM Patients WHERE id=?", (pid,))
                    st.success("❌ Patient deleted")
                    safe_rerun()

# ================= DOCTORS =================
elif menu == "Doctors":
    st.header("👨‍⚕️ Doctors Management")
    search = st.text_input("🔍 Search by CNIC or Name", key="search_doc")
    df_doc = query("SELECT * FROM Doctors WHERE cnic LIKE ? OR name LIKE ?" if search else "SELECT * FROM Doctors",
                   (f"%{search}%", f"%{search}%") if search else ())
    st.dataframe(df_doc)

    col1, col2 = st.columns(2)
    departments = query("SELECT name FROM Departments")["name"].tolist()
    with col1:
        st.subheader("➕ Add Doctor")
        dname = st.text_input("Name", key="add_doc_name")
        dcnic = st.text_input("CNIC", key="add_doc_cnic")
        ddept = st.selectbox("Department", departments, key="add_doc_dept")
        if st.button("Add Doctor", key="btn_add_doc"):
            if valid_cnic(dcnic):
                try:
                    execute("INSERT INTO Doctors VALUES(NULL,?,?,?)", (dname, dcnic, ddept))
                    st.success("✅ Doctor added successfully!")
                    safe_rerun()
                except sqlite3.IntegrityError:
                    st.error("⚠️ CNIC already exists!")
            else:
                st.error("⚠️ Invalid CNIC")

    with col2:
        st.subheader("✏️ Update/Delete Doctor")
        did = st.number_input("Doctor ID", min_value=1, key="upd_doc_id")
        doc_row = query("SELECT * FROM Doctors WHERE id=?", (did,))
        if not doc_row.empty:
            dname = st.text_input("Name", doc_row["name"].iloc[0], key="upd_doc_name")
            dcnic = st.text_input("CNIC", doc_row["cnic"].iloc[0], key="upd_doc_cnic")
            ddept = st.selectbox("Department", departments, index=departments.index(doc_row["department"].iloc[0]), key="upd_doc_dept")
            ucol, dcol = st.columns(2)
            with ucol:
                if st.button("Update Doctor", key="upd_doc_btn"):
                    if valid_cnic(dcnic):
                        execute("UPDATE Doctors SET name=?, cnic=?, department=? WHERE id=?", (dname, dcnic, ddept, did))
                        st.success("✅ Doctor updated")
                        safe_rerun()
            with dcol:
                if st.button("Delete Doctor", key="del_doc_btn"):
                    execute("DELETE FROM Doctors WHERE id=?", (did,))
                    st.success("❌ Doctor deleted")
                    safe_rerun()

# ================= Footer =================
st.markdown("---")
st.markdown("<center>Built with ❤️ using Streamlit • Database: hospital.db</center>", unsafe_allow_html=True)
