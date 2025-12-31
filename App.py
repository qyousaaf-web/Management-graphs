import streamlit as st
import sqlite3
import pandas as pd
import re
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import io

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Hospital Management System", page_icon="🏥", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .main-header { font-size: 48px; font-weight: bold; color: #1E88E5; text-align: center; margin-bottom: 30px; }
    .section-header { font-size: 28px; color: #1565c0; margin-top: 40px; }
    .form-box { background-color: #f8f9fa; padding: 25px; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 30px; }
    .stButton>button { background-color: #4CAF50; color: white; font-weight: bold; border-radius: 8px; padding: 12px; }
    .delete-btn > button { background-color: #f44336; }
    .pdf-btn > button { background-color: #d32f2f; color: white; }
    .search-box { background-color: #f0f8ff; padding: 20px; border-radius: 12px; border-left: 6px solid #2196F3; margin-bottom: 30px; }
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

# ================= PDF GENERATION FOR PATIENT REPORT =================
def generate_patient_report_pdf(patient_name, patient_cnic, records_df):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=1*inch, bottomMargin=1*inch)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=28,
        textColor=colors.HexColor('#1E88E5'),
        spaceAfter=30,
        alignment=1  # Center
    )
    story.append(Paragraph("Patient Medical Report", title_style))
    story.append(Spacer(1, 20))

    # Patient Info
    story.append(Paragraph(f"<b>Patient Name:</b> {patient_name}", styles['Normal']))
    story.append(Paragraph(f"<b>CNIC:</b> {patient_cnic}", styles['Normal']))
    story.append(Paragraph(f"<b>Report Generated:</b> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
    story.append(Spacer(1, 30))

    # Medical History Table
    if not records_df.empty:
        data = [["Date", "Doctor", "Diagnosis", "Treatment", "Prescription"]]
        for _, row in records_df.iterrows():
            data.append([
                row["date"],
                row["doctor"],
                row["diagnosis"][:60] + "..." if len(row["diagnosis"]) > 60 else row["diagnosis"],
                row["treatment"][:60] + "..." if len(row["treatment"]) > 60 else row["treatment"],
                row["prescription"][:60] + "..." if len(row["prescription"]) > 60 else row["prescription"]
            ])

        table = Table(data, colWidths=[1.2*inch, 1.2*inch, 1.4*inch, 1.4*inch, 1.4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E88E5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0f8ff')),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        story.append(table)
    else:
        story.append(Paragraph("No medical records found for this patient.", styles['Normal']))

    story.append(Spacer(1, 40))
    story.append(Paragraph("This report is confidential and for medical use only.", styles['Italic']))
    story.append(Paragraph("Generated by Hospital Management System", styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return buffer

# ================= SIDEBAR =================
st.sidebar.markdown("<h2 style='color:#1E88E5;'>🏥 Hospital System</h2>", unsafe_allow_html=True)
menu = st.sidebar.radio("Navigate", ["Dashboard", "Patients", "Doctors", "Appointments", "Medical Records", "Billings"])

# ================= MEDICAL RECORDS WITH PDF EXPORT =================
elif menu == "Medical Records":
    st.markdown('<div class="main-header">📋 Medical Records</div>', unsafe_allow_html=True)

    # Search Patient
    st.markdown('<div class="search-box">', unsafe_allow_html=True)
    st.subheader("🔍 Search Patient Medical History")
    search_cnic = st.text_input("Enter Patient CNIC", placeholder="xxxxx-xxxxxxx-x")
    search_btn = st.button("Search Records", type="primary")
    st.markdown('</div>', unsafe_allow_html=True)

    records_df = pd.DataFrame()
    patient_name = "Unknown"

    if search_btn and search_cnic:
        records_df = query("SELECT * FROM MedicalRecords WHERE patient_cnic = ? ORDER BY date DESC", (search_cnic,))
        if not records_df.empty:
            patient_name = records_df.iloc[0]["patient"]
            st.success(f"Found {len(records_df)} record(s) for {patient_name}")

    # Display Records
    if not records_df.empty:
        st.subheader(f"Medical History - {patient_name}")
        st.dataframe(records_df, use_container_width=True)

        # PDF Download Button
        pdf_buffer = generate_patient_report_pdf(patient_name, search_cnic, records_df)
        st.markdown('<div class="pdf-btn">', unsafe_allow_html=True)
        st.download_button(
            label="📄 Download Full Patient Report as PDF",
            data=pdf_buffer,
            file_name=f"Medical_Report_{patient_name.replace(' ', '_')}_{search_cnic}.pdf",
            mime="application/pdf"
        )
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        if search_btn:
            st.warning("No records found for this CNIC.")

    # Add New Record
    st.markdown('<div class="form-box">', unsafe_allow_html=True)
    st.markdown('<h3 class="section-header">➕ Add New Medical Record</h3>', unsafe_allow_html=True)
    with st.form("add_record_form"):
        col1, col2 = st.columns(2)
        with col1:
            patient_cnic = st.text_input("Patient CNIC *")
            doctor = st.text_input("Doctor Name *")
        with col2:
            date = st.date_input("Visit Date *")
        diagnosis = st.text_area("Diagnosis *")
        treatment = st.text_area("Treatment")
        prescription = st.text_area("Prescription")

        submitted = st.form_submit_button("Save Record", type="primary")
        if submitted:
            if patient_cnic and doctor and diagnosis:
                pat = query("SELECT name FROM Patients WHERE cnic=?", (patient_cnic,))
                if not pat.empty:
                    patient_name = pat.iloc[0]["name"]
                    execute("INSERT INTO MedicalRecords (patient, patient_cnic, doctor, diagnosis, treatment, prescription, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (patient_name, patient_cnic, doctor, diagnosis, treatment, prescription, str(date)))
                    st.success("Medical record saved successfully!")
                    st.rerun()
                else:
                    st.error("Patient CNIC not found!")
            else:
                st.error("Patient CNIC, Doctor Name, and Diagnosis are required!")

    # Update/Delete Record
    st.markdown('<h3 class="section-header">✏️ Update or Delete Record</h3>', unsafe_allow_html=True)
    record_ids = query("SELECT id FROM MedicalRecords")["id"].tolist()
    if record_ids:
        selected_id = st.selectbox("Select Record ID", record_ids)
        rec = query("SELECT * FROM MedicalRecords WHERE id = ?", (selected_id,)).iloc[0]

        with st.form("update_record_form"):
            col1, col2 = st.columns(2)
            with col1:
                patient_cnic = st.text_input("Patient CNIC", value=rec["patient_cnic"], disabled=True)
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
                execute("UPDATE MedicalRecords SET doctor=?, diagnosis=?, treatment=?, prescription=?, date=? WHERE id=?",
                        (doctor, diagnosis, treatment, prescription, str(date), selected_id))
                st.success("Record updated!")
                st.rerun()

            if delete:
                execute("DELETE FROM MedicalRecords WHERE id=?", (selected_id,))
                st.success("Record deleted!")
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ================= OTHER MODULES (keep your existing code for Dashboard, Patients, Doctors, Appointments, Billings) =================

# Footer
st.markdown("---")
st.markdown("<center>© 2025 Hospital Management System • Built with ❤️ using Streamlit</center>", unsafe_allow_html=True)
