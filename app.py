from flask import Flask, request, jsonify
from flask_cors import CORS
import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
from flask_cors import CORS

CORS(
    app,
    resources={
        r"/*": {
            "origins": [
                "https://portfolio-indhirajith.vercel.app/"
            ]
        }
    }
)

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "https://portfolio-indhirajith.vercel.app/"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response



EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")


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


# ---------- Contact Endpoint ----------
@app.route("/contact", methods=["POST"])
def contact():
    try:
        data = request.get_json()

        name = data.get("name")
        email = data.get("email")
        message = data.get("message")

        if not name or not email or not message:
            return jsonify({"error": "All fields are required"}), 400

        timestamp = datetime.now().strftime("%d %b %Y, %I:%M %p IST")
        intent = detect_intent(message)

        # ---------- Admin Email ----------
        admin_msg = EmailMessage()
        admin_msg["Subject"] = f"📩 New Portfolio Inquiry | {name}"
        admin_msg["From"] = EMAIL_USER
        admin_msg["To"] = RECEIVER_EMAIL
        admin_msg["Reply-To"] = email
        intent_upper = intent.upper()
        is_urgent = intent_upper in ["RECRUITER", "CLIENT"]
        intent_styles = {
             "RECRUITER": ("#e0f2fe", "#0369a1"),  # Blue
             "CLIENT": ("#dcfce7", "#166534"),     # Green
             "GENERAL": ("#f1f5f9", "#475569")     # Gray
             }
        bg_color, text_color = intent_styles.get(intent_upper, intent_styles["GENERAL"])
        admin_msg.set_content(f"""
<!DOCTYPE html>
<html>
  <body style="margin:0;padding:0;background:#ffffff;font-family:Arial,Helvetica,sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="padding:24px;">
      <tr>
        <td align="center">

          <table width="100%" cellpadding="0" cellspacing="0"
                 style="max-width:640px;background:#ffffff;color:#0f172a;">

            <!-- Header -->
            <tr>
              <td style="font-size:18px;font-weight:600;color:#0ea5e9;padding-bottom:18px;">
                📩 New Portfolio Inquiry
                {f'<span style="margin-left:8px;color:#dc2626;font-size:13px;font-weight:700;">🚨 URGENT</span>' if is_urgent else ''}
              </td>
            </tr>

            <!-- Meta -->
            <tr><td style="font-size:14px;padding-bottom:6px;"><strong>Name:</strong> {name}</td></tr>
            <tr><td style="font-size:14px;padding-bottom:6px;"><strong>Email:</strong> {email}</td></tr>
            <tr><td style="font-size:14px;padding-bottom:10px;"><strong>Received:</strong> {timestamp}</td></tr>

            <!-- Intent Badge -->
            <tr>
              <td style="font-size:14px;padding-bottom:16px;">
                <strong>Intent:</strong>
                <span style="
                  display:inline-block;
                  padding:4px 10px;
                  border-radius:999px;
                  background:{bg_color};
                  color:{text_color};
                  font-size:12px;
                  font-weight:700;
                  margin-left:6px;
                ">
                  {intent_upper}
                </span>
              </td>
            </tr>

            <!-- Divider -->
            <tr><td><div style="height:1px;background:#e5e7eb;margin:14px 0;"></div></td></tr>

            <!-- Message -->
            <tr>
              <td style="font-size:15px;font-weight:600;padding-bottom:10px;">
                Message
              </td>
            </tr>

            <tr>
              <td style="
                background:#f8fafc;
                border-radius:8px;
                padding:16px;
                font-size:14px;
                white-space:pre-wrap;
              ">
{message}
              </td>
            </tr>

            <!-- Divider -->
            <tr><td><div style="height:1px;background:#e5e7eb;margin:18px 0;"></div></td></tr>

            <!-- Actions -->
            <tr>
              <td>
                <a href="mailto:{email}"
                   style="
                     display:inline-block;
                     padding:10px 16px;
                     background:#0ea5e9;
                     color:#ffffff;
                     border-radius:6px;
                     font-size:13.5px;
                     font-weight:600;
                     text-decoration:none;
                   ">
                  Reply to {name}
                </a>
              </td>
            </tr>

            <!-- Footer -->
            <tr>
              <td style="padding-top:18px;font-size:12px;color:#64748b;">
                Source: Portfolio Contact Form
              </td>
            </tr>

          </table>

        </td>
      </tr>
    </table>
  </body>
</html>
""", subtype="html")


        # ---------- User Auto Reply ----------
        user_msg = EmailMessage()
        user_msg["Subject"] = "Thanks for contacting me — I’ll be in touch shortly"
        user_msg["From"] = EMAIL_USER
        user_msg["To"] = email

        user_msg.set_content(
            f"Hi {name},\n\nThanks for reaching out. I’ve received your message and will get back to you shortly.\n\nRegards,\nP Indhirajith"
        )

        user_msg.add_alternative(
            auto_reply_html(name, intent),
            subtype="html"
        )

        # ---------- Send Emails ----------
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(admin_msg)
            server.send_message(user_msg)

        return jsonify({"success": True}), 200

    except Exception as e:
        print("EMAIL ERROR:", e)
        return jsonify({"error": "Failed to send email"}), 500


if __name__ == "__main__":
    app.run()
