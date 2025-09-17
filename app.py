import os
import csv
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify
from dotenv import load_dotenv
from twilio.rest import Client
from chatbot import RoofingChatbot

load_dotenv()

app = Flask(__name__)

# Configuration from environment variables
LEADS_FILE = os.path.join(os.path.dirname(__file__), "leads.csv")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
OWNER_PHONE_NUMBER = os.getenv("OWNER_PHONE_NUMBER")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize clients
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN else None
chatbot = RoofingChatbot(OPENAI_API_KEY)

def save_lead(data: dict) -> None:
    """Append a new lead entry to the CSV file."""
    exists = os.path.exists(LEADS_FILE)
    with open(LEADS_FILE, mode="a", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "timestamp",
            "name",
            "phone",
            "email",
            "address",
            "job_type",
            "description",
            "photo_filename",
            "chatbot_interaction",
            "lead_score",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerow(data)

def send_sms(to_number: str, message_body: str) -> None:
    """Send an SMS message using Twilio. If Twilio credentials are missing, skip."""
    if twilio_client and TWILIO_PHONE_NUMBER and to_number:
        try:
            twilio_client.messages.create(
                body=message_body,
                from_=TWILIO_PHONE_NUMBER,
                to=to_number,
            )
            print(f"Sent SMS to {to_number}")
        except Exception as ex:
            print(f"Failed to send SMS: {ex}")
    else:
        print("Twilio not configured or missing number — skipping SMS")

@app.route("/")
def index():
    """Render the landing page."""
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    """Handle chatbot interactions via AJAX."""
    try:
        data = request.get_json()
        user_message = data.get("message", "")
        user_info = data.get("user_info", {})
        
        if not user_message:
            return jsonify({"error": "No message provided"}), 400
        
        response = chatbot.get_response(user_message, user_info)
        return jsonify({"response": response})
        
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({"error": "Sorry, I'm having trouble right now. Please try again."}), 500

@app.route("/submit_lead", methods=["POST"])
def submit_lead():
    """Handle lead form submission."""
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip()
    address = request.form.get("address", "").strip()
    job_type = request.form.get("job_type", "").strip()
    description = request.form.get("description", "").strip()

    photo_filename = ""
    photo = request.files.get("photo")
    if photo and photo.filename:
        uploads_dir = os.path.join(app.root_path, "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        photo_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{photo.filename}"
        photo_path = os.path.join(uploads_dir, photo_filename)
        photo.save(photo_path)

    # Pre-qualify the lead using AI
    lead_data = {
        "name": name,
        "phone": phone,
        "email": email,
        "address": address,
        "job_type": job_type,
        "description": description,
    }
    
    chatbot_assessment = chatbot.pre_qualify_lead(lead_data)
    
    # Determine lead score based on available information
    lead_score = calculate_lead_score(lead_data)
    
    # Save lead with all information
    full_lead_data = {
        "timestamp": datetime.now().isoformat(),
        "name": name,
        "phone": phone,
        "email": email,
        "address": address,
        "job_type": job_type,
        "description": description,
        "photo_filename": photo_filename,
        "chatbot_interaction": chatbot_assessment,
        "lead_score": lead_score,
    }

    save_lead(full_lead_data)

    # Send personalized SMS to the lead
    customer_message = chatbot.generate_follow_up_message(lead_data, "initial")
    if phone:
        send_sms(phone, customer_message)

    # Notify the owner with AI assessment
    if OWNER_PHONE_NUMBER:
        owner_message = (
            f"🏠 NEW LEAD (Score: {lead_score}/10)\n"
            f"Name: {name}\n"
            f"Phone: {phone}\n"
            f"Job: {job_type}\n"
            f"AI Assessment: {chatbot_assessment}"
        )
        send_sms(OWNER_PHONE_NUMBER, owner_message)

    return jsonify({"success": True, "message": "Thank you! We'll contact you soon."})

def calculate_lead_score(lead_data: dict) -> int:
    """Calculate a lead score from 1-10 based on available information."""
    score = 0
    
    # Phone number provided (high value)
    if lead_data.get("phone"):
        score += 3
    
    # Email provided
    if lead_data.get("email"):
        score += 2
    
    # Address provided
    if lead_data.get("address"):
        score += 2
    
    # Detailed description
    description = lead_data.get("description", "")
    if len(description) > 50:
        score += 2
    elif len(description) > 20:
        score += 1
    
    # Job type indicates urgency
    job_type = lead_data.get("job_type", "").lower()
    if job_type in ["repair", "emergency"]:
        score += 1
    
    return min(score, 10)

if __name__ == "__main__":
    # Create leads file if it does not exist
    if not os.path.exists(LEADS_FILE):
        with open(LEADS_FILE, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "timestamp",
                "name",
                "phone",
                "email",
                "address",
                "job_type",
                "description",
                "photo_filename",
                "chatbot_interaction",
                "lead_score",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
    app.run(host="0.0.0.0", port=5001, debug=True)
