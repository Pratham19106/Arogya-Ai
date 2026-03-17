# Helper utilities for data formatting, etc.

def calculate_dynamic_queue_score(base_score: int, wait_time_mins: int) -> int:
    """
    Mock queue score calculation that increases score as people wait longer.
    """
    # Simply adds a penalty for waiting longer to bump priority
    return base_score + (wait_time_mins // 10)

def generate_whatsapp_message(patient_name: str, priority: str, wait_time: str) -> str:
    """
    Generates a mock WhatsApp message.
    """
    msg = f"Hello {patient_name},\n\n"
    msg += f"Your triage assessment is complete. Priority Level: *{priority}*.\n"
    msg += f"Estimated wait time: *{wait_time}*.\n\n"
    if priority == "Urgent":
        msg += "Please remain seated near the triage desk; a nurse will attend to you shortly."
    else:
        msg += "Please take a seat in the waiting area. We will call you when it's your turn."
        
    return msg
