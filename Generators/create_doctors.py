# create_doctors.py
import pandas as pd
from datetime import datetime, timedelta, time
import os

doctors = [
    "Dr. Rajesh Kumar",
    "Dr. Priya Sharma",
    "Dr. Srinivas"
]
locations = [
    "Hyderabad - Jubilee Hills",
    "Hyderabad - Gachibowli"
]

start_date = datetime.now().date() + timedelta(days=1)   # start from tomorrow
days = 7                                                 # number of days to generate
slot_minutes = 30                                        # slot duration
work_start = time(9, 0)                                  # clinic opens
work_end = time(17, 0)                                   # clinic closes

rows = []
for d in range(days):
    date = start_date + timedelta(days=d)
    for doctor in doctors:
        location = locations[d % len(locations)]  # rotate locations
        t = datetime.combine(date, work_start)
        end = datetime.combine(date, work_end)
        while t < end:
            rows.append([
                doctor,
                date.strftime("%Y-%m-%d"),
                t.strftime("%H:%M"),
                (t + timedelta(minutes=slot_minutes)).strftime("%H:%M"),
                slot_minutes,
                location,
                True   # Available by default
            ])
            t += timedelta(minutes=slot_minutes)

df = pd.DataFrame(rows, columns=[
    "Doctor", "Date", "Start", "End", "Slots", "Location", "Available"
])

os.makedirs("data", exist_ok=True)

output_file = os.path.join("data", "doctors.xlsx")
df.to_excel(output_file, index=False, sheet_name="Schedule")

print(f"✅ {output_file} created with {len(df)} slots")
