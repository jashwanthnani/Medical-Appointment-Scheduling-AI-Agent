# app.py
import streamlit as st
import os
from utils.patient import load_patients, find_patient
from utils.calendar_ops import load_schedule, save_schedule, get_doctors, get_locations, get_dates, suggest_slots, block_slots
from utils.exporter import append_appointment
from utils.messaging import send_email_confirmation, send_sms, build_reminder_messages

st.set_page_config(page_title="AI Medical Scheduling Assistant", page_icon="🩺")

st.title(" AI Medical Scheduling Assistant")

PATIENTS_CSV = "patients.csv"
SCHEDULE_XLSX = "doctors.xlsx"
APPTS_XLSX = "appointments.xlsx"
INTAKE_FORM_PDF = os.path.join("forms", "IntakeForm.pdf")

patients_df = load_patients(PATIENTS_CSV)
schedule_df = load_schedule(SCHEDULE_XLSX)

with st.form("patient_form", clear_on_submit=False):
    st.subheader("Patient Details")
    name = st.text_input("Full Name *")
    dob = st.date_input("Date of Birth *")
    doctors = get_doctors(schedule_df)
    doctor = st.selectbox("Preferred Doctor *", doctors)
    locations = get_locations(schedule_df, doctor) if doctor else []
    location = st.selectbox("Clinic Location *", locations)
    submitted = st.form_submit_button("Proceed")

if submitted:
    dob_iso = dob.strftime("%Y-%m-%d")
    lookup = find_patient(patients_df, name, dob_iso)
    patient_type = "Returning" if lookup["exists"] else "New"
    minutes_required = 30 if patient_type == "Returning" else 60

    st.success(f"Detected patient type: **{patient_type}** (Duration: {minutes_required} mins)")

    date_options = get_dates(schedule_df, doctor, location)
    date_str = st.selectbox("Choose Appointment Date", date_options)
    if date_str:
        slots = suggest_slots(schedule_df, doctor, location, date_str, minutes_required)
        if not slots:
            st.warning("No slots found. Try another date.")
        else:
            choice = st.radio("Available Slots", [f"{s} - {e}" for s, e in slots])
            if choice:
                start_str, end_str = choice.split(" - ")

                st.subheader("Insurance Info")
                carrier = st.text_input("Insurance Carrier *")
                member_id = st.text_input("Member ID *")
                group_num = st.text_input("Group Number *")

                st.subheader("Contact Info")
                phone = st.text_input("Phone", value=lookup.get("Phone", ""))
                email = st.text_input("Email", value=lookup.get("Email", ""))

                if st.button("Confirm Appointment"):
                    updated_df, computed_end = block_slots(schedule_df.copy(), doctor, location, date_str, start_str, minutes_required)
                    if not computed_end:
                        st.error("Slot reservation failed. Try another.")
                    else:
                        save_schedule(updated_df, SCHEDULE_XLSX)
                        appt_id = append_appointment(
                            path=APPTS_XLSX,
                            name=name, dob=dob_iso, patient_type=patient_type,
                            doctor=doctor, location=location,
                            date_str=date_str, start=start_str, end=computed_end,
                            duration=minutes_required,
                            carrier=carrier, member_id=member_id, group=group_num,
                            phone=phone, email=email
                        )

                        st.success(f"✅ Appointment Confirmed! ID: {appt_id}")
                        st.info(f"{doctor} on {date_str} at {start_str}-{computed_end}")

                        subj = "Appointment Confirmation"
                        body = f"Dear {name},\n\nYour appointment is confirmed.\nDoctor: {doctor}\nDate: {date_str}\nTime: {start_str}-{computed_end}\nLocation: {location}\n\nPlease fill the attached intake form.\n\nRegards,\nClinic"
                        send_email_confirmation(email, subj, body, INTAKE_FORM_PDF)

                        st.subheader("Reminders (Simulated)")
                        reminders = build_reminder_messages(name, date_str, start_str, email, phone)
                        for mode, dest, sub, text in reminders:
                            if mode == "email":
                                send_email_confirmation(dest, sub, text)
                            else:
                                send_sms(dest, text)
                        st.success("Reminders queued (see outbox/).")
