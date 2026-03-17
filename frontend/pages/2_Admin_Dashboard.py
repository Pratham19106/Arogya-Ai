import streamlit as st
import pandas as pd
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("API_URL", "http://localhost:8000/api")
st.title("📊 Admin Dashboard")

# Fetch Metrics
try:
    metrics_res = requests.get(f"{API_URL}/dashboard/metrics")
    if metrics_res.status_code == 200:
        metrics = metrics_res.json()
        
        st.markdown("### Key Performance Indicators")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Waiting Patients", metrics["waiting_patients"])
        col2.metric("Critical Follow-ups (Worse)", metrics["critical_cases"], delta_color="inverse")
        col3.metric("Understaffed Departments", metrics["understaffed_departments"], delta_color="inverse")
    else:
        st.error("Failed to load metrics")
except Exception as e:
    st.error("Cannot connect to backend API")

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["🚦 Live Queue", "📱 WhatsApp Recovery", "👩‍⚕️ Staffing Forecast"])

with tab1:
    st.subheader("Live Queue Management")
    
    if st.button("🔄 Refresh Queue", use_container_width=False, key="queue_refresh_top"):
        st.rerun()
    
    try:
        queue_res = requests.get(f"{API_URL}/dashboard/queue")
        if queue_res.status_code == 200:
            queue_data = queue_res.json()
            if not queue_data:
                st.info("No patients currently in queue.")
            else:
                df = pd.DataFrame(queue_data)[["id", "name", "priority", "status", "complaint", "wait_time_mins", "queue_score", "time_registered"]]
                df = df.rename(columns={
                    "id": "ID", "name": "Name", "priority": "Priority",
                    "status": "Status", "complaint": "Complaint",
                    "wait_time_mins": "Est. Wait (mins)",
                    "queue_score": "Score", "time_registered": "Registered At"
                })
                
                def color_row(row):
                    if row["Priority"] == "Urgent":
                        return ["background-color: #ffcccc; color: #990000"] * len(row)
                    elif row["Priority"] == "Moderate":
                        return ["background-color: #fff3cd; color: #7d5a00"] * len(row)
                    elif row["Status"] == "Treating":
                        return ["background-color: #d4edda; color: #155724"] * len(row)
                    return [""] * len(row)
                
                display_df = df[["ID", "Name", "Priority", "Status", "Est. Wait (mins)", "Score", "Registered At"]]
                st.dataframe(display_df.style.apply(color_row, axis=1), use_container_width=True, hide_index=True, height=280)
                
                st.markdown("---")
                st.markdown("### 🩺 Patient Actions")

                col_sel, col_details = st.columns([2, 3])
                with col_sel:
                    patient_labels = {
                        f"#{row['ID']} — {row['Name']} ({row['Priority']}) [{row['Status']}]": row['ID']
                        for _, row in df.iterrows()
                    }
                    selected_label = st.selectbox("Select a Patient", list(patient_labels.keys()))
                    selected_id = patient_labels[selected_label]
                    selected_row = df[df["ID"] == selected_id].iloc[0]
                    selected_status = selected_row["Status"]
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("🏥 Induct", use_container_width=True,
                                     disabled=(selected_status != "Waiting"),
                                     help="Move from Waiting → Treating"):
                            res = requests.post(f"{API_URL}/patients/{selected_id}/induct")
                            if res.status_code == 200:
                                st.success("Patient inducted into treatment!")
                                st.rerun()
                            else:
                                st.error(res.json().get("detail", res.text))
                    with col_btn2:
                        if st.button("✅ Discharge", use_container_width=True,
                                     disabled=(selected_status == "Discharged"),
                                     help="Discharge & send WhatsApp follow-up"):
                            res = requests.post(f"{API_URL}/patients/{selected_id}/discharge")
                            if res.status_code == 200:
                                st.success("Discharged! Follow-up WhatsApp sent.")
                                st.rerun()
                            else:
                                st.error(res.json().get("detail", res.text))

                with col_details:
                    st.markdown("**📋 Patient Details**")
                    priority_emoji = {"Urgent": "🔴", "Moderate": "🟡", "Low": "🟢"}.get(selected_row["Priority"], "⚪")
                    status_emoji = {"Waiting": "⏳", "Treating": "🏥", "Discharged": "✅"}.get(selected_row["Status"], "")
                    st.info(
                        f"**Name:** {selected_row['Name']}  \n"
                        f"**Priority:** {priority_emoji} {selected_row['Priority']}  \n"
                        f"**Status:** {status_emoji} {selected_row['Status']}  \n"
                        f"**Est. Wait:** {selected_row['Est. Wait (mins)']} mins  \n"
                        f"**Queue Score:** {selected_row['Score']:.1f}  \n"
                        f"**Complaint:** _{selected_row['Complaint']}_"
                    )
    except Exception as e:
        st.error(f"Error loading queue: {e}")


with tab2:
    st.subheader("Post-Discharge Recovery Monitoring")
    colA, colB = st.columns([4, 1])
    with colA:
        try:
            rec_res = requests.get(f"{API_URL}/dashboard/recoveries")
            if rec_res.status_code == 200:
                rec_data = rec_res.json()
                if not rec_data:
                    st.info("No recovery data currently available.")
                else:
                    r_df = pd.DataFrame(rec_data)[["patient_name", "status", "time_replied"]]
                    r_df = r_df.rename(columns={"patient_name": "Patient Name", "status": "Current Status", "time_replied": "Last Reply"})
                    def highlight_worse(row):
                        return ['background-color: #ffcccc; color: #990000' if row['Current Status'] == 'Worse' else '' for _ in row]
                    st.dataframe(r_df.style.apply(highlight_worse, axis=1), use_container_width=True, hide_index=True)
        except Exception:
            st.error("Error loading recovery data.")
    with colB:
        if st.button("🔄 Refresh Recoveries", use_container_width=True):
            st.rerun()

with tab3:
    st.subheader("AI Staffing Forecast (Prophet Model)")
    colX, colY = st.columns([4, 1])
    with colX:
        try:
            if 'metrics' in locals() and "forecast" in metrics:
                f_df = pd.DataFrame(metrics["forecast"])
                def highlight_understaffed(row):
                    return ['background-color: #fff3cd; color: #856404' if row['Understaffed'] else '' for _ in row]
                st.dataframe(f_df.style.apply(highlight_understaffed, axis=1), use_container_width=True, hide_index=True)
            else:
                st.info("Forecast data unavailable.")
        except Exception:
            st.error("Error loading forecast data.")
    with colY:
        if st.button("🔄 Refresh Forecast", use_container_width=True):
            st.rerun()

    st.markdown("---")
    st.subheader("Current Shift Staff Input")
    st.markdown("Update the currently assigned doctors and nurses to see live gaps in the forecast above.")
    try:
        current_staff_res = requests.get(f"{API_URL}/dashboard/staff")
        current_staff = current_staff_res.json() if current_staff_res.status_code == 200 else {}
    except:
        current_staff = {}

    with st.form("staffing_form"):
        depts = ["Emergency", "General Ward", "ICU", "Pediatrics", "Orthopedics"]
        cols = st.columns(len(depts))
        staff_inputs = {}
        
        for i, dept in enumerate(depts):
            with cols[i]:
                st.markdown(f"**{dept}**")
                def_docs = current_staff.get(dept, {}).get("doctors", 0)
                def_nurs = current_staff.get(dept, {}).get("nurses", 0)
                docs = st.number_input(f"Docs", min_value=0, value=def_docs, key=f"d_{dept}")
                nurs = st.number_input(f"Nurs", min_value=0, value=def_nurs, key=f"n_{dept}")
                staff_inputs[dept] = {"doctors": docs, "nurses": nurs}
                
        submit_staff = st.form_submit_button("Update Shift Staffing", use_container_width=True)
        
    if submit_staff:
        try:
            res = requests.post(f"{API_URL}/dashboard/staff", json=staff_inputs)
            if res.status_code == 200:
                st.success("Staffing updated! The forecast table will now reflect the live gap analysis.")
                st.rerun()
        except Exception as e:
            st.error(f"Failed to update staff: {e}")

    st.markdown("---")
    st.subheader("End-of-Day Retraining")
    st.markdown("Enter today's actual patient footfall to continuously train the Prophet model.")
    with st.form("retrain_prophet_form"):
        st.write("Actual Patients Seen Today")
        col_r1, col_r2, col_r3, col_r4, col_r5 = st.columns(5)
        with col_r1: e_count = st.number_input("Emergency", min_value=0, value=25)
        with col_r2: g_count = st.number_input("General Ward", min_value=0, value=15)
        with col_r3: i_count = st.number_input("ICU", min_value=0, value=10)
        with col_r4: p_count = st.number_input("Pediatrics", min_value=0, value=12)
        with col_r5: o_count = st.number_input("Orthopedics", min_value=0, value=8)
        
        submit_retrain = st.form_submit_button("Update Records & Retrain Model", use_container_width=True)
        
    if submit_retrain:
        payload = {
            "Emergency": e_count,
            "General Ward": g_count,
            "ICU": i_count,
            "Pediatrics": p_count,
            "Orthopedics": o_count
        }
        with st.spinner("Appending to dataset and retraining AI models (this may take a moment)..."):
            try:
                ret_res = requests.post(f"{API_URL}/dashboard/retrain", json=payload)
                if ret_res.status_code == 200:
                    st.success("Prophet model successfully retrained on today's hospital data! Forecasts updated.")
                else:
                    st.error(f"Failed to retrain model. Error: {ret_res.text}")
            except Exception as e:
                st.error(f"Failed to connect to backend: {e}")

    st.markdown("---")
    st.subheader("🧠 AI Prediction Feedback")
    st.markdown("Tell the AI where its staffing prediction was wrong. It will learn from your correction and improve future forecasts automatically.")

    forecast_dept_data = {}
    if 'metrics' in locals() and "forecast" in metrics:
        for row in metrics["forecast"]:
            try:
                rec = row.get("Recommended Staff (Doc/Nurse)", "0 / 0")
                pred_docs = int(rec.split("/")[0].strip())
                forecast_dept_data[row["Department"]] = {
                    "predicted_docs": pred_docs,
                    "predicted_patients": row.get("Expected Patients", 0)
                }
            except:
                pass

    with st.form("feedback_form"):
        dept_options = list(forecast_dept_data.keys()) if forecast_dept_data else ["Emergency", "General Ward", "ICU", "Pediatrics", "Orthopedics"]
        fb_dept = st.selectbox("Department where prediction was wrong", dept_options)
        
        col_fb1, col_fb2 = st.columns(2)
        with col_fb1:
            pre_docs = forecast_dept_data.get(fb_dept, {}).get("predicted_docs", 2)
            pre_pats = forecast_dept_data.get(fb_dept, {}).get("predicted_patients", 20)
            st.metric("🤖 AI Predicted Doctors", pre_docs)
        with col_fb2:
            actual_docs_needed = st.number_input("✅ Actual Doctors You Needed", min_value=1, value=pre_docs + 2)
            
        fb_submit = st.form_submit_button("Submit Correction & Retrain Model", use_container_width=True)

    if fb_submit:
        fb_payload = {
            "dept": fb_dept,
            "predicted_docs": pre_docs,
            "actual_docs_needed": actual_docs_needed,
            "predicted_patients": pre_pats
        }
        with st.spinner("Processing your feedback and retraining the model..."):
            try:
                fb_res = requests.post(f"{API_URL}/dashboard/feedback", json=fb_payload)
                if fb_res.status_code == 200:
                    entry = fb_res.json().get("entry", {})
                    ratio = entry.get("correction_ratio", 1.0)
                    direction = "above" if ratio > 1 else "below"
                    st.success(f"✅ Feedback recorded! The model corrected by a factor of **{ratio:.2f}x** — actual demand was {direction} its prediction. Future forecasts will reflect this.")
                else:
                    st.error(f"Failed to submit feedback: {fb_res.text}")
            except Exception as e:
                st.error(f"Connection error: {e}")

    st.markdown("**📋 Feedback History**")
    try:
        log_res = requests.get(f"{API_URL}/dashboard/feedback-log")
        if log_res.status_code == 200 and log_res.json():
            log_df = pd.DataFrame(log_res.json())
            log_df = log_df[["date", "department", "predicted_doctors", "actual_doctors_needed", "predicted_patients", "actual_implied_patients", "correction_ratio"]]
            log_df.columns = ["Date", "Department", "Pred. Docs", "Actual Docs", "Pred. Patients", "Implied Patients", "Correction Factor"]
            st.dataframe(log_df, use_container_width=True, hide_index=True)
        else:
            st.info("No feedback submitted yet. The model will improve as you correct its predictions.")
    except:
        st.info("No feedback history available.")



