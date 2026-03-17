# Arogya AI 

An intelligent hospital management system that accompanies the patient from entry to recovery using minimal input (receptionist + WhatsApp interaction). 
Designed as a fully functional, production-ready system.

## Vision

“From a single receptionist input and a simple patient response, an AI system manages the patient journey from entry to recovery.”

## System Architecture

- **Frontend**: Streamlit multi-page dashboard.
- **Backend**: FastAPI REST API handling all business logic.
- **Database**: SQLite with SQLAlchemy ORM.
- **Machine Learning**: 
  - spaCy + scikit-learn for NLP Triage classification.
  - Facebook Prophet for staffing and patient inflow forecasting.
- **Integration**: Twilio API for real WhatsApp communication.

## Folder Structure

* `backend/`: FastAPI application, routers, database configuration, and schemas.
* `frontend/`: Streamlit dashboard with multi-page interface.
* `ml/`: Model training and inference scripts for Triage and Forecasting.

## Getting Started

### Prerequisites

Ensure you have Python 3.8+ installed.

### Setup Instructions

1. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

2. **Configure Environment Variables**

   A `.env` file has been created in the root directory. You can edit this file to configure API URLs and Twilio credentials:
   
   ```env
   # API Configuration
   API_URL=http://localhost:8000/api
   
   # Database Configuration
   DATABASE_URL=sqlite:///./smartqueue.db
   
   # Twilio Credentials
   TWILIO_ACCOUNT_SID=your_sid
   TWILIO_AUTH_TOKEN=your_token
   TWILIO_PHONE_NUMBER=whatsapp:+14155238886
   ```
   *If Twilio credentials are left as `mock_sid` and `mock_token`, the system defaults to a console mock output.*

3. **Run the FastAPI Backend**

   The backend automatically initializes the database database schema and handles ML models.
   
   ```cmd
   uvicorn backend.main:app --reload --port 8000
   ```
   *The API will be available at `http://localhost:8000`*

4. **Run the Streamlit Frontend**

   In a new terminal window, launch the dashboard:
   
   ```cmd
   streamlit run frontend/app.py
   ```
   *The UI will be available at `http://localhost:8501`*

## Usage Flow

1. **Receptionist Interface**: Enter patient details and complaint. Submitting triggers the NLP engine via the backend to categorize priority, add to the DB, and dispatch a WhatsApp message.
2. **Admin Dashboard**: View the live queue dynamically sorted by queue score and priority. Unload patients using the Discharge action. Check Prophet staffing forecasts and monitor post-discharge recovery statuses.
3. **Patient Simulator**: Enter a phone number for a discharged patient and simulate a WhatsApp response to see the admin dashboard update in real-time, simulating Twilio inbound webhooks.
