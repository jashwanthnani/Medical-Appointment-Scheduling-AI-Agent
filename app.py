# app.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import uuid
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import uuid
import re

# Load environment
load_dotenv()
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")

# File paths
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
PATIENT_DB = os.path.join(DATA_DIR, "patients.csv")
DOCTOR_DB = os.path.join(DATA_DIR, "doctors.xlsx")
APPOINTMENTS_DB = os.path.join(DATA_DIR, "appointments.xlsx")
INTAKE_FORM = os.path.join("forms", "new_patient_intake_form.pdf")

# Scheduler
if "scheduler" not in st.session_state:
    scheduler = BackgroundScheduler()
    scheduler.start()
    st.session_state.scheduler = scheduler
else:
    scheduler = st.session_state.scheduler

#  UTILITY FUNCTIONS
def load_patients():
    if os.path.exists(PATIENT_DB):
        return pd.read_csv(PATIENT_DB)
    else:
        df = pd.DataFrame(columns=["Name", "DOB", "Type", "Phone", "Email"])
        df.to_csv(PATIENT_DB, index=False)
        return df

def load_doctors():
    if os.path.exists(DOCTOR_DB):
        return pd.read_excel(DOCTOR_DB)
    else:
        st.error("Doctor schedule file not found. Please create doctors.xlsx in 'data/'.")
        return pd.DataFrame()

def load_appointments():
    try:
        if os.path.exists(APPOINTMENTS_DB):
            return pd.read_excel(APPOINTMENTS_DB)
    except Exception:
        st.warning("⚠️ Appointments file corrupted. Re-creating a new one.")
        os.remove(APPOINTMENTS_DB)
    df = pd.DataFrame(columns=[
        "AppointmentID", "Name", "DOB", "Gender", "Phone", "Email", "Address",
        "EmergencyContact", "Insurance", "Reason", "Symptoms", "DurationOfSymptoms",
        "Allergy", "AllergyList", "AllergyTested", "EpiPen", "Medications", "MedicalHistory",
        "Acknowledged", "Doctor", "Slot", "Duration", "Confirmed", "Timestamp",
        "Reminder1_Sent", "Reminder2_Sent", "Reminder3_Sent"
    ])
    df.to_excel(APPOINTMENTS_DB, index=False)
    return df

# Email sending
def send_email(to_email, subject, body, attachment_path=None):
    msg = MIMEMultipart()
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))

    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, "rb") as f:
            from email.mime.application import MIMEApplication
            part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
            part["Content-Disposition"] = f'attachment; filename="{os.path.basename(attachment_path)}"'
            msg.attach(part)

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, to_email, msg.as_string())
        server.quit()
        print(f"Email sent to {to_email}: {subject}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

# Receipt Generation
def generate_receipt(details, filename=os.path.join(DATA_DIR, "appointment_receipt.pdf")):
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph("MediCare Clinic", styles['Title']))
    elements.append(Paragraph("Appointment Confirmation Receipt", styles['Heading2']))
    elements.append(Spacer(1, 12))

    # Patient Info
    patient_data = [
        ["Patient Name", details.get("Name", "")],
        ["Date of Birth", details.get("DOB", "")],
        ["Gender", details.get("Gender", "")],
        ["Phone", details.get("Phone", "")],
        ["Email", details.get("Email", "")]
    ]
    t1 = Table(patient_data, colWidths=[140, 330])
    t1.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.whitesmoke),
                            ("GRID", (0,0), (-1,-1), 0.5, colors.grey)]))
    elements.append(Paragraph("Patient Information", styles['Heading3']))
    elements.append(t1)
    elements.append(Spacer(1, 14))

    # Appointment Info
    appt_data = [
        ["Appointment ID", details.get("AppointmentID", "")],
        ["Doctor", details.get("Doctor", "")],
        ["Appointment Slot", details.get("Slot", "")],
        ["Duration", f"{details.get('Duration', '')} minutes"],
        ["Booked On", details.get("Timestamp", "")]
    ]
    t2 = Table(appt_data, colWidths=[140, 330])
    t2.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.whitesmoke),
                            ("GRID", (0,0), (-1,-1), 0.5, colors.grey)]))
    elements.append(Paragraph("Appointment Details", styles['Heading3']))
    elements.append(t2)
    elements.append(Spacer(1, 18))

    # Footer
    elements.append(Paragraph(
        "Thank you for booking with <b>MediCare Clinic</b>.<br/>"
        "Hyderabad, India | +91-9876543210 | support@medicare.com",
        styles['Normal']
    ))

    doc.build(elements)
    return filename

# Save appointment and reminders
def save_appointment_row(details):
    df = load_appointments()
    df = pd.concat([df, pd.DataFrame([details])], ignore_index=True)
    df.to_excel(APPOINTMENTS_DB, index=False)

def mark_reminder_sent(appointment_id, reminder_field):
    df = load_appointments()
    idx = df.index[df["AppointmentID"] == appointment_id]
    if len(idx) == 0: return False
    df.loc[idx, reminder_field] = datetime.now().strftime("%Y-%m-%d %H:%M")
    df.to_excel(APPOINTMENTS_DB, index=False)
    return True

def send_reminder_job(appointment_row, reminder_no):
    appt_id = appointment_row["AppointmentID"]
    to_email = appointment_row["Email"]

    subjects = {
        1: "Appointment Confirmation - MediCare Clinic",
        2: "Reminder: Please complete and return the intake form",
        3: "Final Reminder: Confirm attendance or provide cancellation reason"
    }

    bodies = {
        1: f"<p>Dear <b>{appointment_row['Name']}</b>,</p>"
           f"<p>Your appointment with <b>{appointment_row['Doctor']}</b> is confirmed for {appointment_row['Slot']}.</p>",
        2: "Please complete and return the intake form before your visit.",
        3: "Please confirm if you are attending your appointment. If not, reply with the reason for cancellation."
    }

    receipt_path = os.path.join(DATA_DIR, f"receipt_{appt_id}.pdf")
    if not os.path.exists(receipt_path):
        generate_receipt(appointment_row, receipt_path)

    sent = send_email(to_email, subjects[reminder_no], bodies[reminder_no], receipt_path)
    if sent:
        mark_reminder_sent(appt_id, f"Reminder{reminder_no}_Sent")

def schedule_reminders_for_appointment(appointment_row):
    slot_str = appointment_row.get("Slot", "")
    try:
        date_part = slot_str.split("|")[0].strip()
        time_part = slot_str.split("|")[1].split("-")[0].strip()
        slot_dt = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M")
    except Exception:
        slot_dt = datetime.now() + timedelta(days=2)

    now = datetime.now()
    scheduler.add_job(send_reminder_job, args=[appointment_row, 1], next_run_time=now + timedelta(seconds=5))
    scheduler.add_job(send_reminder_job, args=[appointment_row, 2], next_run_time=slot_dt - timedelta(hours=48))
    scheduler.add_job(send_reminder_job, args=[appointment_row, 3], next_run_time=slot_dt - timedelta(hours=24))

# STREAMLIT UI 
if "step" not in st.session_state: st.session_state.step = 1
if "patient_info" not in st.session_state: st.session_state.patient_info = {}

def next_step(): st.session_state.step += 1
def prev_step(): st.session_state.step -= 1 if st.session_state.step > 1 else 1

st.set_page_config(page_title="AI Medical Scheduler", layout="centered")
st.title("🤖 AI Medical Appointment Scheduler")

patients_df = load_patients()
doctors_df = load_doctors()
appointments_df = load_appointments()

# STEP 1: Patient Info
if st.session_state.step == 1:
    st.header("Patient Info")
    user_greeting = st.text_input("Say something to start (e.g., 'Hi, I want to book a doctor appointment')")
    if user_greeting:
        if "hi" in user_greeting.lower() or "hello" in user_greeting.lower():
            st.success("👋 Hello! I can help you schedule a medical appointment. Please fill in your details below.")
        elif "book" in user_greeting.lower() or "appointment" in user_greeting.lower():
            st.success("Great! Let's get your appointment booked. Please provide your details below.")
        else:
            st.info("I'm here to help you schedule your appointment. Please fill in your details below.")
    else:
        st.info("Welcome! Please provide your details to begin booking an appointment.")

    with st.form("f1"):
        name = st.text_input("Full Name *")
        now = datetime.now()          # works
        dob = st.date_input("DOB", min_value=date(1900,1,1), max_value=date.today())
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        phone = st.text_input("Phone (optional)")
        email = st.text_input("Email *")
        address = st.text_input("Address")
        submitted = st.form_submit_button("Continue")

    if submitted:
        # Input validation
        if not name or not email:
            st.error("Name and Email are required.")
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            st.error("Invalid email format.")
        else:
            patient_type = "Returning" if ((patients_df["Name"].str.lower() == name.lower()) & (patients_df["DOB"] == str(dob))).any() else "New"
            st.session_state.patient_info = {
                "Name": name, "DOB": str(dob), "Gender": gender, "Phone": phone, "Email": email,
                "Address": address, "PatientType": patient_type
            }
            next_step()

# STEP 2: Emergency & Insurance 
elif st.session_state.step == 2:
    st.header("Emergency & Insurance")
    with st.form("f2"):
        em_name = st.text_input("Emergency contact name")
        em_rel = st.text_input("Relationship")
        em_phone = st.text_input("Emergency phone")
        ins_comp = st.text_input("Insurance Company")
        member_id = st.text_input("Member ID")
        group_no = st.text_input("Group Number")
        submitted = st.form_submit_button("Continue")
    if submitted:
        st.session_state.patient_info.update({
            "EmergencyContact": f"{em_name},{em_rel},{em_phone}",
            "Insurance": f"{ins_comp},{member_id},{group_no}"
        })
        next_step()
    st.button("Back", on_click=prev_step)

# STEP 3: Symptoms
elif st.session_state.step == 3:
    st.header("Symptoms")
    with st.form("f3"):
        reason = st.text_area("Reason for visit")
        symptoms = st.multiselect("Symptoms", ["Sneezing","Cough","Headache","Fever"])
        submitted = st.form_submit_button("Continue")
    if submitted:
        st.session_state.patient_info.update({"Reason": reason, "Symptoms": ",".join(symptoms)})
        next_step()
    st.button("Back", on_click=prev_step)

# STEP 4: History 
elif st.session_state.step == 4:
    st.header("Allergy & History")
    with st.form("f4"):
        allergy = st.radio("Do you have allergies?", ["Yes","No","Not sure"])
        allergy_list = st.text_area("Allergies (if any)")
        medications = st.text_area("Medications")
        med_hist = st.multiselect("Medical history", ["Asthma","Diabetes","Hypertension"])
        submitted = st.form_submit_button("Continue")
    if submitted:
        st.session_state.patient_info.update({
            "Allergy": allergy, "AllergyList": allergy_list,
            "Medications": medications, "MedicalHistory": ",".join(med_hist)
        })
        next_step()
    st.button("Back", on_click=prev_step)

# STEP 5: Schedule Appointment 
elif st.session_state.step == 5:
    st.header("Schedule Appointment")
    if doctors_df.empty:
        st.error("No doctor schedule found. Please add data/doctors.xlsx")
        st.button("Back", on_click=prev_step)
    else:
        doctor = st.selectbox("Choose doctor", doctors_df["Doctor"].unique())
        available_slots_df = doctors_df[(doctors_df["Doctor"]==doctor) & (doctors_df["Available"]==True)].reset_index(drop=True)
        if available_slots_df.empty:
            st.warning("No available slots for this doctor.")
        else:
            slot_labels = available_slots_df.apply(lambda x: f"{x['Date']} | {x['Start']}-{x['End']} | {x['Location']}", axis=1).tolist()
            slot_choice = st.selectbox("Choose slot", slot_labels)

            if st.button("📅 Book this slot now") and slot_choice:
                patient_type = st.session_state.patient_info.get("PatientType","New")
                duration_min = 60 if patient_type=="New" else 30
                appt_id = f"MC-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"

                appointment = st.session_state.patient_info.copy()
                appointment.update({
                    "AppointmentID": appt_id,
                    "Doctor": doctor,
                    "Slot": slot_choice,
                    "Duration": duration_min,
                    "Confirmed": True,
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Reminder1_Sent": "", "Reminder2_Sent": "", "Reminder3_Sent": ""
                })

                # Generate receipt
                receipt_path = os.path.join(DATA_DIR, f"receipt_{appt_id}.pdf")
                generate_receipt(appointment, receipt_path)

                # Send confirmation email
                subject = f"MediCare Appointment Confirmation - {appt_id}"
                html_body = f"""
                <p>Dear <b>{appointment['Name']}</b>,</p>
                <p>Your appointment is confirmed:</p>
                <ul>
                  <li><b>Doctor:</b> {appointment['Doctor']}</li>
                  <li><b>Slot:</b> {appointment['Slot']}</li>
                  <li><b>Duration:</b> {appointment['Duration']} minutes</li>
                </ul>
                <p>Appointment ID: {appt_id}</p>
                <p>Regards,<br/>MediCare Clinic</p>
                """
                attachments = [receipt_path]
                if appointment.get("PatientType")=="New" and os.path.exists(INTAKE_FORM):
                    attachments.append(INTAKE_FORM)

                # Email send loop
                email_failed = False
                for attach in attachments:
                    if not send_email(appointment['Email'], subject, html_body):
                        email_failed = True
                        break
                if email_failed:
                    st.error("Failed to send confirmation email. Appointment not saved.")
                else:
                    # Save appointment
                    save_appointment_row(appointment)

                    # Update doctor slot as unavailable
                    slot_idx = doctors_df[(doctors_df['Doctor']==doctor) & 
                                          (doctors_df.apply(lambda x: f"{x['Date']} | {x['Start']}-{x['End']} | {x['Location']}", axis=1)==slot_choice)].index
                    if len(slot_idx)>0:
                        doctors_df.loc[slot_idx, 'Available'] = False
                        doctors_df.to_excel(DOCTOR_DB, index=False)

                    # Schedule reminders
                    schedule_reminders_for_appointment(appointment)

                    # Save for Step 6
                    st.session_state.final_appointment = appointment
                    st.session_state.final_receipt = receipt_path
                    next_step()
                    
#  STEP 6: Final Appointment Summary
elif st.session_state.step == 6:
    st.header("Appointment Confirmation")
    if "final_appointment" not in st.session_state or "final_receipt" not in st.session_state:
        st.error("No appointment found in session. Please go back and book an appointment.")
    else:
        appt = st.session_state.final_appointment
        st.success(f"✅ Appointment Confirmed! Appointment ID: {appt['AppointmentID']}")

        st.subheader("Appointment Details")
        st.write(f"**Patient Name:** {appt['Name']}")
        st.write(f"**Doctor:** {appt['Doctor']}")
        st.write(f"**Slot:** {appt['Slot']}")
        st.write(f"**Duration:** {appt['Duration']} minutes")
        st.write(f"**Email:** {appt['Email']}")

        st.subheader("Download Confirmation Receipt")
        with open(st.session_state.final_receipt, "rb") as f:
            st.download_button("📄 Download PDF Receipt", f, file_name=os.path.basename(st.session_state.final_receipt))

        st.info("📧 A confirmation email has also been sent to your email address with the receipt and intake form (if new patient).")

        st.button("Back to Home", on_click=lambda: st.session_state.update({"step":1}))