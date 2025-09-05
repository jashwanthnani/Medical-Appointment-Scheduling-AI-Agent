# create_appointments.py
import pandas as pd

cols = [
    "AppointmentID","Name","DOB","PatientType","Doctor","Location","Date","Start","End",
    "DurationMinutes","InsuranceCarrier","MemberID","GroupNumber","Phone","Email","Status","CreatedAt"
]

df = pd.DataFrame(columns=cols)
df.to_excel("appointments.xlsx", index=False, sheet_name="Appointments")

print("✅ appointments.xlsx created")
