from flask import Flask, request, jsonify
from flask_cors import CORS
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os
from dotenv import load_dotenv
from datetime import datetime

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

# ---------- Health Check ----------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


# ---------- Helper: Detect Message Type ----------
def detect_intent(message: str) -> str:
    msg = message.lower()

    recruiter_keywords = [
        "job", "role", "intern", "internship", "position", "hiring", "career"
    ]
    client_keywords = [
        "project", "client", "freelance", "budget", "timeline", "collaboration"
    ]

    if any(word in msg for word in recruiter_keywords):
        return "recruiter"
    if any(word in msg for word in client_keywords):
        return "client"
    return "general"


# ---------- Helper: Auto Reply HTML ----------
def auto_reply_html(name: str, intent: str) -> str:

    if intent == "recruiter":
        headline = "Thank you for reaching out"
        body = f"""
        I appreciate you contacting me regarding an opportunity.
        I’m actively exploring roles in <strong>AI, machine learning,
        and data-driven engineering</strong> with a focus on real-world impact.
        <br><br>
        I’ll review the details and get back to you within <strong>24 hours</strong>.
        """

    elif intent == "client":
        headline = "Thanks for getting in touch"
        body = f"""
        Thank you for reaching out regarding a potential project or collaboration.
        <br><br>
        I specialize in building <strong>AI-driven, scalable, and data-backed solutions</strong>.
        If helpful, feel free to reply with goals, timelines, or constraints.
        """

    else:
        headline = "Thank you for reaching out"
        body = f"""
        I’ve received your message and will review it shortly.
        <br><br>
        You’re welcome to reply to this email if you’d like to add more details.
        """

    return f"""
<!DOCTYPE html>
<html>
  <body style="margin:0;padding:0;background:#f8fafc;font-family:Arial,Helvetica,sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="padding:24px;">
      <tr>
        <td align="center">
          <table width="100%" cellpadding="0" cellspacing="0"
                 style="max-width:560px;background:#ffffff;border-radius:12px;
                        padding:28px;color:#0f172a;
                        box-shadow:0 12px 32px rgba(0,0,0,0.08);">

            <tr>
              <td style="font-size:20px;font-weight:600;color:#0ea5e9;padding-bottom:12px;">
                {headline}
              </td>
            </tr>

            <tr>
              <td style="font-size:14.5px;line-height:1.7;color:#334155;">
                Hi <strong>{name}</strong>,<br><br>
                {body}
              </td>
            </tr>

            <tr>
              <td style="padding:18px 0;">
                <div style="background:#f1f5f9;border-left:4px solid #0ea5e9;
                            padding:14px;border-radius:6px;font-size:13.5px;">
                  ⏱ Typical response time: within 24 hours (business days)<br>
                  📩 You can reply directly to this email to continue the conversation.
                </div>
              </td>
            </tr>

            <tr>
              <td style="font-size:13px;color:#475569;line-height:1.6;">
                Regards,<br>
                <strong>P Indhirajith</strong><br>
                AI & Data Science Engineer<br>
                <span style="color:#64748b;">Portfolio Contact · Automated Reply</span>
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
        timestamp = datetime.now().strftime("%d %b %Y, %I:%M %p IST")

        # ---------------- SendGrid Emails ----------------
        try:
            sg = SendGridAPIClient(SENDGRID_API_KEY)

            # Admin email
            admin_email = Mail(
                from_email=EMAIL_FROM,
                to_emails=RECEIVER_EMAIL,
                subject=f"📩 New Portfolio Inquiry | {name}",
                html_content=f"""
                <h3>New Contact Message</h3>
                <p><strong>Name:</strong> {name}</p>
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Time:</strong> {timestamp}</p>
                <p><strong>Message:</strong><br>{message}</p>
                <p><strong>Intent:</strong> {intent.upper()}</p>
                """
            )
            sg.send(admin_email)

            # Auto-reply email
            user_email = Mail(
                from_email=EMAIL_FROM,
                to_emails=email,
                subject="Thanks for contacting me",
                html_content=auto_reply_html(name, intent)
            )
            sg.send(user_email)

        except Exception as mail_error:
            print("SENDGRID ERROR:", mail_error)

        return jsonify({"success": True}), 200

    except Exception as e:
        print("CONTACT ERROR:", e)
        return jsonify({"error": "Server error"}), 500

# ---------------- Local Run ----------------
if __name__ == "__main__":
    app.run()