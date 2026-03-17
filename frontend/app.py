import streamlit as st
import sys
import os
import subprocess
import time
import requests

# Background process to run FastAPI
def start_backend():
    try:
        # Check if backend is already running
        requests.get("http://localhost:8000/", timeout=1)
    except:
        # Start if not running
        with st.spinner("Starting Arogya Ai Backend... (This may take up to 20 seconds)"):
            env = os.environ.copy()
            # Run detached so it doesn't block Streamlit
            subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            # Wait for it to spin up
            for i in range(25):
                try:
                    res = requests.get("http://localhost:8000/", timeout=2)
                    if res.status_code == 200:
                        break
                except:
                    time.sleep(1)

# Initialize backend on startup
if "backend_started" not in st.session_state:
    start_backend()
    st.session_state["backend_started"] = True

st.set_page_config(
    page_title="Arogya Ai - Hospital Management",
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

st.markdown("<h1 class='main-header'>🏥 Arogya Ai System</h1>", unsafe_allow_html=True)

st.markdown("""
### Welcome to Arogya Ai (Production Build)
An intelligent hospital management system that accompanies the patient from entry to recovery using minimal input.

**Navigation:**
👈 Please select a page from the sidebar to get started.

- **Receptionist Interface**: Register new patients via NLP API.
- **Admin Dashboard**: View live queues, Prophet-based staffing forecasts, and WhatsApp recovery monitoring.
- **Patient Simulator**: Simulate post-discharge WhatsApp interactions to test webhook integration.
""")
