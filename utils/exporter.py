# utils/exporter.py
import pandas as pd
from datetime import datetime
import uuid

SHEET = "Appointments"

def append_appointment(
    path="appointments.xlsx",
    name="",
    dob="",
    patient_type="New",
    doctor="",
    location="",
    date_str="",
    start="",
    end="",
    duration=30,
    carrier="",
    member_id="",
    group="",
    phone="",
    email="",
    status="Confirmed"
):
    try:
        df = pd.read_excel(path, sheet_name=SHEET)
    except Exception:
        cols = ["AppointmentID","Name","DOB","PatientType","Doctor","Location","Date","Start","End",
                "DurationMinutes","InsuranceCarrier","MemberID","GroupNumber","Phone","Email","Status","CreatedAt"]
        df = pd.DataFrame(columns=cols)
    appt_id = str(uuid.uuid4())[:8]
    row = {
        "AppointmentID": appt_id,
        "Name": name,
        "DOB": dob,
        "PatientType": patient_type,
        "Doctor": doctor,
        "Location": location,
        "Date": date_str,
        "Start": start,
        "End": end,
        "DurationMinutes": duration,
        "InsuranceCarrier": carrier,
        "MemberID": member_id,
        "GroupNumber": group,
        "Phone": phone,
        "Email": email,
        "Status": status,
        "CreatedAt": datetime.now().isoformat(timespec="seconds")
    }
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    with pd.ExcelWriter(path, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name=SHEET)
    return appt_id
