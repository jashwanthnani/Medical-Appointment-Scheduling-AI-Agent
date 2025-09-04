# main chatbot code (Streamlit)

import streamlit as st
import pandas as pd

st.title("AI Medical Scheduling Assistant")

name = st.text_input("Enter your full name")
dob = st.date_input("Enter your Date of Birth")
doctor = st.selectbox("Choose doctor", ["Dr. Adams", "Dr. Brown"])
location = st.text_input("Enter clinic location")

if st.button("Proceed"):
    st.write(f"Welcome {name}, checking availability...")
