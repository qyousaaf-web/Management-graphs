# app.py - Hospital Management System with Billing Receipt PDF Export
import streamlit as st
import sqlite3
import pandas as pd
import re
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
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
    .pdf-btn > button { background-color: #d32f2f; }
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
        CREATE TABLE IF NOT EXISTS Billings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient TEXT,
            patient_cnic TEXT,
            amount REAL,
            details TEXT,
            status TEXT,
            bill_date TEXT DEFAULT (date('now'))
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

# ================= BILLING RECEIPT PDF GENERATION =================
def generate_billing_receipt_pdf(bill_data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.8*inch, bottomMargin=0.8*inch)
    styles = getSampleStyleSheet()
    story = []

    # Hospital Header
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Title'],
        fontSize=28,
        textColor=colors.HexColor('#1E88E5'),
        alignment=1,
        spaceAfter=20
    )
    story.append(Paragraph("🏥 City General Hospital", header_style))
    story.append(Paragraph("123 Health Street, Medical City", styles['Normal']))
    story.append(Paragraph("Phone: (123) 456-7890 | Email: info@cityhospital.com", styles['Normal']))
    story.append(Spacer(1, 30))

    # Receipt Title
    receipt_title = ParagraphStyle('ReceiptTitle', parent=styles['Heading1'], fontSize=22, alignment=1, textColor=colors.HexColor('#2E7D32'))
    story.append(Paragraph("BILLING RECEIPT", receipt_title))
    story.append(Spacer(1, 20))

    # Bill Details Table
    data = [
        ["Bill ID", f"#{bill_data['id']}"],
        ["Patient Name", bill_data['patient']],
        ["CNIC", bill_data['patient_cnic']],
        ["Bill Date", bill_data['bill_date']],
        ["Status", bill_data['status']],
        ["Details", bill_data['details'] or "General Consultation"],
        ["Amount", f"${bill_data['amount']:,.2f}"]
    ]

    table = Table(data, colWidths=[2*inch, 4*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E88E5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0f8ff')),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('LEFTPADDING', (0, 1), (-1, -1), 15),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8f5e8')),
        ('FONTNAME', (0, -1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 16),
    ]))
    story.append(table)
    story.append(Spacer(1, 40))

    # Footer
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], alignment=1, textColor=colors.grey)
    story.append(Paragraph("Thank you for choosing City General Hospital", footer_style))
    story.append(Paragraph("This is a computer-generated receipt.", footer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer

# ================= SIDEBAR =================
st.sidebar.markdown("<h2 style='color:#1E88E5;'>🏥 Hospital System</h2>", unsafe_allow_html=True)
menu = st.sidebar.radio("Navigate", ["Dashboard", "Patients", "Billings"])

# ================= BILLINGS WITH PDF RECEIPT =================
if menu == "Billings":
    st.markdown('<div class="main-header">💰 Billing Management</div>', unsafe_allow_html=True)

    bills_df = query("SELECT * FROM Billings ORDER BY bill_date DESC")
    st.subheader("All Bills")
    st.dataframe(bills_df, use_container_width=True)

    # View Specific Bill & Generate Receipt
    st.markdown("### 📄 View Bill & Download Receipt")
    bill_ids = query("SELECT id FROM Billings")["id"].tolist()
    if bill_ids:
        selected_id = st.selectbox("Select Bill ID to View Receipt", bill_ids)
        bill = query("SELECT * FROM Billings WHERE id = ?", (selected_id,)).iloc[0]

        # Display Bill Details
        st.markdown(f"**Patient:** {bill['patient']} | **CNIC:** {bill['patient_cnic']}")
        st.markdown(f"**Amount:** ${bill['amount']:,.2f} | **Status:** {bill['status']} | **Date:** {bill['bill_date']}")
        st.markdown(f"**Details:** {bill['details'] or 'N/A'}")

        # Generate and Download PDF Receipt
        pdf_buffer = generate_billing_receipt_pdf(bill)
        st.markdown('<div class="pdf-btn">', unsafe_allow_html=True)
        st.download_button(
            label="📄 Download Billing Receipt as PDF",
            data=pdf_buffer,
            file_name=f"Receipt_Bill_{bill['id']}_{bill['patient_cnic']}.pdf",
            mime="application/pdf"
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # Create New Bill
    st.markdown('<div class="form-box">', unsafe_allow_html=True)
    st.subheader("Create New Bill")
    with st.form("add_bill_form"):
        col1, col2 = st.columns(2)
        with col1:
            patient_cnic = st.text_input("Patient CNIC *")
            amount = st.number_input("Amount ($)", min_value=0.0, format="%.2f")
        with col2:
            details = st.text_area("Bill Details")
            status = st.selectbox("Payment Status", ["Pending", "Paid"])

        submitted = st.form_submit_button("Create Bill", type="primary")
        if submitted:
            if not patient_cnic:
                st.error("Patient CNIC is required!")
            else:
                pat = query("SELECT name FROM Patients WHERE cnic=?", (patient_cnic,))
                if not pat.empty:
                    patient_name = pat.iloc[0]["name"]
                    execute("INSERT INTO Billings (patient, patient_cnic, amount, details, status) VALUES (?, ?, ?, ?, ?)",
                            (patient_name, patient_cnic, amount, details, status))
                    st.success("Bill created successfully!")
                    st.rerun()
                else:
                    st.error("Patient not found in records!")
    st.markdown('</div>', unsafe_allow_html=True)

# ================= OTHER MODULES (Patients, Dashboard, etc.) =================
# Keep your existing code for other pages

# Footer
st.markdown("---")
st.markdown("<center>© 2025 Hospital Management System • Built with ❤️ using Streamlit</center>", unsafe_allow_html=True)
