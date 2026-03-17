import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("API_URL", "http://localhost:8000/api")
st.title("📝 Receptionist Interface")
st.markdown("Register incoming patients. The AI will classify urgency, predict wait time, and trigger a WhatsApp message.")

with st.form("patient_registration"):
    st.subheader("Patient Details")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Patient Name", placeholder="e.g. Rajesh Kumar")
    with col2:
        phone = st.text_input("Phone Number", placeholder="e.g. +919000000001")
        
    complaint = st.text_area("Patient Complaint / Symptoms", placeholder="Describe the symptoms in natural language...", height=150)
    
    st.markdown("---")
    submitted = st.form_submit_button("Register & AI Triage", use_container_width=True)

if submitted:
    if not name or not phone or not complaint:
        st.error("Please fill in all fields.")
    else:
        with st.spinner("AI analyzing complaint and registering..."):
            payload = {
                "name": name,
                "phone": phone,
                "complaint": complaint
            }
            try:
                response = requests.post(f"{API_URL}/patients/intake", json=payload)
                if response.status_code == 200:
                    data = response.json()
                    st.success(f"Patient {data['name']} successfully registered!")
                    
                    priority_color = {
                        "Urgent": "red",
                        "Moderate": "orange",
                        "Low": "green"
                    }.get(data["priority"], "blue")
                    
                    st.markdown(f"### Priority: <span style='color:{priority_color}; font-weight:bold;'>{data['priority']}</span>", unsafe_allow_html=True)
                    st.info(f"Estimated Wait Time: **{data['wait_time_mins']} mins**")
                    st.success("A WhatsApp message has been dispatched (Check logs if using mock).")
                else:
                    st.error(f"Error from API: {response.text}")
            except requests.exceptions.ConnectionError:
                st.error("Failed to connect to the Backend API. Is uvicorn running?")
