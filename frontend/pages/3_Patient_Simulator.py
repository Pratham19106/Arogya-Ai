import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("API_URL", "http://localhost:8000/api")
st.title("📱 WhatsApp Sandbox Simulator")
st.markdown("""
Welcome to the simulated **Twilio WhatsApp Sandbox** environment.
Since we are using the Twilio Sandbox instead of a live registered WhatsApp Business API, setting up a public webhook URL (via ngrok) is required for real two-way messaging.

To make local testing seamless, this page **simulates the inbound Twilio webhook**. When you select a reply below, it sends the exact same payload a real WhatsApp user would send to our backend.
""")

st.info("Ensure you have discharged a patient from the Admin Dashboard first so they are awaiting a reply.")

with st.form("webhook_sim"):
    st.subheader("Simulate Inbound Message")
    st.markdown("Enter the phone number exactly as registered (e.g. `+1234567890`).")
    phone = st.text_input("Patient Phone Number")
    
    st.markdown("Select how the patient is feeling:")
    reply = st.radio("Patient Reply", ["1 - Better 🟢", "2 - Same 🟡", "3 - Worse 🔴"])
    
    st.markdown("---")
    submitted = st.form_submit_button("Submit Simulated Reply", use_container_width=True)

if submitted:
    reply_code = reply[0] # "1", "2", or "3"
    
    res = requests.post(f"{API_URL}/webhook/simulate", json={"phone": phone, "reply_code": reply_code})
    
    if res.status_code == 200:
        data = res.json()
        if data["status"] == "success":
            st.success("Webhook processed! Admin dashboard should reflect the change.")
        else:
            st.error(data.get("detail", "Error"))
    else:
        st.error("API Error or backend not reachable.")
