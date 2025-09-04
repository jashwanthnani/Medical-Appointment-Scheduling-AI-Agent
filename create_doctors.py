# create_doctors.py
import pandas as pd
from datetime import datetime, timedelta, time

doctors = ["Dr. Adams", "Dr. Brown", "Dr. Chen"]
locations = ["Hyderabad - Jubilee Hills", "Hyderabad - Gachibowli"]

start_date = datetime.now().date() + timedelta(days=1)
days = 7
slot_minutes = 30

rows = []
for d in range(days):
    date = start_date + timedelta(days=d)
    for doctor in doctors:
        location = locations[d % len(locations)]
        t = datetime.combine(date, time(9, 0))
        end = datetime.combine(date, time(17, 0))
        while t < end:
            rows.append([
                doctor,
                date.strftime("%Y-%m-%d"),
                t.strftime("%H:%M"),
                (t + timedelta(minutes=slot_minutes)).strftime("%H:%M"),
                slot_minutes,
                location,
                "Yes"
            ])
            t += timedelta(minutes=slot_minutes)

df = pd.DataFrame(rows, columns=["Doctor", "Date", "Start", "End", "SlotMinutes", "Location", "Available"])
df.to_excel("doctors.xlsx", index=False, sheet_name="Schedule")

print("✅ doctors.xlsx created")
