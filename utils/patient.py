# utils/patient.py
import pandas as pd

def load_patients(path="patients.csv"):
    return pd.read_csv(path)

def normalize_name(name: str) -> str:
    return " ".join(name.strip().lower().split())

def find_patient(patients_df: pd.DataFrame, name: str, dob_iso: str):
    nm = normalize_name(name)
    mask = (patients_df["Name"].str.lower().str.strip() == nm) & (patients_df["DOB"] == dob_iso)
    match = patients_df[mask]
    if not match.empty:
        row = match.iloc[0]
        return {
            "exists": True,
            "Type": row.get("Type", "Returning"),
            "Phone": row.get("Phone", ""),
            "Email": row.get("Email", "")
        }
    return {"exists": False, "Type": "New", "Phone": "", "Email": ""}
