import os
import sys

# Ensure `ml` modules can be imported if running directly from `backend/`
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from backend.database import engine, Base
from backend.routers import patients, dashboard, webhook

# Create DB tables if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Arogya Ai API", description="Production API for Intelligent Hospital Management.")

app.include_router(patients.router)
app.include_router(dashboard.router)
app.include_router(webhook.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Arogya Ai API"}
