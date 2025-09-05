# create_patients.py
import pandas as pd
from faker import Faker
import random

fake = Faker()
records = []

for i in range(50):
    name = fake.name()
    dob = fake.date_of_birth(minimum_age=18, maximum_age=70).strftime("%Y-%m-%d")
    patient_type = random.choice(["New", "Returning"])
    phone = fake.msisdn()[:10]  # 10-digit
    email = fake.email()
    records.append([name, dob, patient_type, phone, email])

df = pd.DataFrame(records, columns=["Name", "DOB", "Type", "Phone", "Email"])
df.to_csv("patients.csv", index=False)

print("✅ patients.csv created")
