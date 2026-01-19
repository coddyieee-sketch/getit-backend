from flask import Flask, request, jsonify
from flask_cors import CORS
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os
from dotenv import load_dotenv
from datetime import datetime
import pytz

# ---------------- Load Environment ----------------
load_dotenv()

app = Flask(__name__)

# ---------------- CORS ----------------
ALLOWED_ORIGINS = [
    "https://portfolio-indhirajith.vercel.app",
]

CORS(
    app,
    origins=ALLOWED_ORIGINS,
    methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# ---------------- Environment Variables ----------------
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM")          # Verified SendGrid sender
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")  # Your inbox

# ---------------- Health Check ----------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


# ---------------- Intent Detection ----------------
def detect_intent(message: str) -> str:
    msg = message.lower()

    recruiter_keywords = [
        "job", "role", "intern", "internship",
        "position", "hiring", "career"
    ]
    client_keywords = [
        "project", "client", "freelance",
        "budget", "timeline", "collaboration"
    ]

    if any(word in msg for word in recruiter_keywords):
        return "recruiter"
    if any(word in msg for word in client_keywords):
        return "client"
    return "general"


# ---------------- Intent Metadata ----------------
def intent_ui(intent: str, message: str):
    urgent_keywords = ["urgent", "asap", "immediate", "priority"]

    is_urgent = (
        intent == "recruiter"
        or any(word in message.lower() for word in urgent_keywords)
    )

    if intent == "recruiter":
        label = "RECRUITER"
    elif intent == "client":
        label = "CLIENT"
    else:
        label = "GENERAL"

    return label, is_urgent


# ---------------- Auto Reply HTML ----------------
def auto_reply_html(name: str, intent: str) -> str:
    if intent == "recruiter":
        headline = "Thank you for reaching out"
        body = """
        I appreciate you contacting me regarding an opportunity.
        I’m actively exploring roles in <strong>AI, machine learning,
        and data-driven engineering</strong>.
        <br><br>
        I’ll review the details and get back to you within <strong>24 hours</strong>.
        """

    elif intent == "client":
        headline = "Thanks for getting in touch"
        body = """
        Thank you for reaching out regarding a potential project or collaboration.
        <br><br>
        I specialize in building <strong>AI-driven, scalable solutions</strong>.
        Feel free to share goals or timelines.
        """

    else:
        headline = "Thank you for reaching out"
        body = """
        I’ve received your message and will review it shortly.
        <br><br>
        You’re welcome to reply with more details.
        """

    return f"""
<!DOCTYPE html>
<html>
  <body style="background:#f8fafc;font-family:Arial,sans-serif;padding:24px;">
    <table width="100%" align="center">
      <tr>
        <td align="center">
          <table width="560" style="background:#ffffff;
               padding:28px;border-radius:12px;
               box-shadow:0 12px 32px rgba(0,0,0,0.08);">
            <tr>
              <td style="font-size:20px;font-weight:600;color:#0ea5e9;">
                {headline}
              </td>
            </tr>
            <tr>
              <td style="padding-top:14px;font-size:14.5px;color:#334155;line-height:1.7;">
                Hi <strong>{name}</strong>,<br><br>
                {body}
              </td>
            </tr>
            <tr>
              <td style="padding-top:20px;font-size:13px;color:#475569;">
                Regards,<br>
                <strong>P Indhirajith</strong><br>
                AI & Data Science Engineer
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""


# ---------------- OPTIONS Preflight ----------------
@app.route("/contact", methods=["OPTIONS"])
def contact_preflight():
    return "", 204


# ---------------- Contact Endpoint ----------------
@app.route("/contact", methods=["POST"])
def contact():
    try:
        data = request.get_json(force=True, silent=True) or {}

        name = data.get("name")
        email = data.get("email")
        message = data.get("message")

        if not name or not email or not message:
            return jsonify({"error": "All fields are required"}), 400

        intent = detect_intent(message)
        label, is_urgent = intent_ui(intent, message)

        # IST Time
        ist = pytz.timezone("Asia/Kolkata")
        timestamp = datetime.now(ist).strftime("%d %b %Y, %I:%M %p IST")

        urgent_prefix = "[URGENT] " if is_urgent else ""

        # ---------- ADMIN EMAIL (PLAIN TEXT ONLY) ----------
        admin_email = Mail(
            from_email=EMAIL_FROM,
            to_emails=RECEIVER_EMAIL,
            subject=f"{urgent_prefix}New Portfolio Inquiry - {name}",
            plain_text_content=f"""
New Contact Message

Name: {name}
Email: {email}
Intent: {label}
Time: {timestamp}

Message:
{message}
"""
        )

        # ---------- USER AUTO-REPLY ----------
        user_email = Mail(
            from_email=EMAIL_FROM,
            to_emails=email,
            subject="Thanks for contacting me",
            html_content=auto_reply_html(name, intent)
        )

        # ---- Send Admin Email ----
        try:
            sg_admin = SendGridAPIClient(SENDGRID_API_KEY)
            response = sg_admin.send(admin_email)
            print("ADMIN EMAIL STATUS:", response.status_code)
        except Exception as e:
            print("ADMIN EMAIL ERROR:", e)

        # ---- Send User Auto Reply ----
        try:
            sg_user = SendGridAPIClient(SENDGRID_API_KEY)
            response = sg_user.send(user_email)
            print("USER EMAIL STATUS:", response.status_code)
        except Exception as e:
            print("USER EMAIL ERROR:", e)

        return jsonify({"success": True}), 200

    except Exception as e:
        print("CONTACT ERROR:", e)
        return jsonify({"error": "Server error"}), 500


# ---------------- Local Run ----------------
if __name__ == "__main__":
    app.run()

