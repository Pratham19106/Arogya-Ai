import streamlit as st
import sys
import os

st.set_page_config(
    page_title="SmartQueue AI - Hospital Management",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
    <style>
    .stApp {
        background-color: #f8fbff;
    }
    .st-emotion-cache-1wivap2 {
        color: #1e3d59;
    }
    .stButton>button {
        background-color: #176B87;
        color: white;
        border-radius: 5px;
        border: none;
    }
    .stButton>button:hover {
        background-color: #053B50;
        color: white;
    }
    div[data-testid="stMetricValue"] {
        color: #176B87;
    }
    .main-header {
        color: #1e3d59;
        font-weight: 700;
        text-align: center;
        margin-bottom: 30px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-header'>🏥 SmartQueue AI System</h1>", unsafe_allow_html=True)

st.markdown("""
### Welcome to SmartQueue AI (Production Build)
An intelligent hospital management system that accompanies the patient from entry to recovery using minimal input.

**Navigation:**
👈 Please select a page from the sidebar to get started.

- **Receptionist Interface**: Register new patients via NLP API.
- **Admin Dashboard**: View live queues, Prophet-based staffing forecasts, and WhatsApp recovery monitoring.
- **Patient Simulator**: Simulate post-discharge WhatsApp interactions to test webhook integration.
""")
