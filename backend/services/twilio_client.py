import os
import json
import uuid
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "mock_sid")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "mock_token")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "whatsapp:+14155238886")
DOCTOR_PHONE_NUMBER = os.getenv("DOCTOR_PHONE_NUMBER", "whatsapp:+14155238886")

# Content Template SID from Twilio Content Template Builder
# Leave blank to fall back to plain text messages
FOLLOWUP_TEMPLATE_SID = os.getenv("FOLLOWUP_TEMPLATE_SID", "")

IS_MOCK = TWILIO_ACCOUNT_SID == "mock_sid" or TWILIO_AUTH_TOKEN == "mock_token"

def _get_client() -> Client:
    return Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def send_whatsapp_message(to_number: str, message: str) -> str:
    """
    Sends a plain-text WhatsApp message via Twilio.
    Returns the message SID.
    """
    if to_number and not to_number.startswith("whatsapp:"):
        to_number = f"whatsapp:{to_number}"
        
    if IS_MOCK:
        print(f"[MOCK TWILIO] Sending to {to_number}: {message}")
        return f"SM{uuid.uuid4().hex[:32]}"

    try:
        client = _get_client()
        message_obj = client.messages.create(
            from_=TWILIO_PHONE_NUMBER,
            body=message,
            to=to_number
        )
        return message_obj.sid
    except Exception as e:
        print(f"Twilio Error: {e}")
        return "error_sid"

def send_whatsapp_template(to_number: str, content_sid: str, content_variables: dict) -> str:
    """
    Sends a WhatsApp message using a Twilio Content Template (with buttons).
    
    Args:
        to_number: Recipient phone number
        content_sid: The Content Template SID from Twilio (HXxxx...)
        content_variables: Dict of variable substitutions, e.g. {"1": "John"}
    """
    if to_number and not to_number.startswith("whatsapp:"):
        to_number = f"whatsapp:{to_number}"

    if IS_MOCK:
        print(f"[MOCK TWILIO TEMPLATE] Sending template {content_sid} to {to_number} with vars {content_variables}")
        return f"SM{uuid.uuid4().hex[:32]}"

    try:
        client = _get_client()
        message_obj = client.messages.create(
            from_=TWILIO_PHONE_NUMBER,
            to=to_number,
            content_sid=content_sid,
            content_variables=json.dumps(content_variables)
        )
        return message_obj.sid
    except Exception as e:
        print(f"Twilio Template Error: {e}")
        return "error_sid"

def send_followup_whatsapp(patient_name: str, to_number: str) -> str:
    """
    Sends the follow-up recovery message.
    - Uses Content Template with quick-reply buttons if FOLLOWUP_TEMPLATE_SID is configured.
    - Falls back to formatted plain-text message otherwise.
    """
    if FOLLOWUP_TEMPLATE_SID:
        # Use real WhatsApp quick-reply buttons via Content Template
        return send_whatsapp_template(
            to_number=to_number,
            content_sid=FOLLOWUP_TEMPLATE_SID,
            content_variables={"1": patient_name}  # {{1}} = patient name in the template
        )
    else:
        # Fallback: formatted plain-text (works in Sandbox)
        message = generate_followup_message(patient_name)
        return send_whatsapp_message(to_number, message)

def generate_triage_message(patient_name: str, priority: str, wait_time: str) -> str:
    msg = f"Hello {patient_name},\n\n"
    msg += f"Your triage assessment is complete. Priority Level: *{priority}*.\n"
    msg += f"Estimated wait time: *{wait_time}*.\n\n"
    if priority == "Urgent":
        msg += "Please remain seated near the triage desk; a nurse will attend to you shortly."
    else:
        msg += "Please take a seat in the waiting area. We will call you when it's your turn."
    return msg

def generate_followup_message(patient_name: str) -> str:
    return (
        f"👋 Hi *{patient_name}*, this is *Arogya AI* - your hospital's health assistant.\n\n"
        f"We hope you're recovering well after your visit! 🏥\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"*How are you feeling today?*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Reply with just a number:\n\n"
        f"*1️⃣ 1* — 🟢 Feeling Better\n"
        f"*2️⃣ 2* — 🟡 About the Same\n"
        f"*3️⃣ 3* — 🔴 Feeling Worse\n\n"
        f"_Your response is sent directly to our medical team. "
        f"If you chose 3, a doctor will contact you immediately._"
    )
