import os
import stripe
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from models import SessionLocal, LicenseKey
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

router = APIRouter()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def generate_secure_key():
    return "UA-" + secrets.token_urlsafe(16)

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the checkout.session.completed event
    if event.type == 'checkout.session.completed':
        session = event.data.object
        
        customer_details = getattr(session, "customer_details", None)
        customer_email = getattr(customer_details, "email", None) if customer_details else None
        session_id = getattr(session, "id", None)
        
        # Idempotency check
        if session_id:
            existing = db.query(LicenseKey).filter(LicenseKey.stripe_session_id == session_id).first()
            if existing:
                print(f"Skipping duplicate event for session {session_id}")
                return {"status": "success", "message": "Already processed"}

        metadata = getattr(session, "metadata", {})
        tier = metadata.get("tier", "Pro") if hasattr(metadata, "get") else getattr(metadata, "tier", "Pro")

        # Generate license key
        new_key = generate_secure_key()
        db_key = LicenseKey(key=new_key, tier=tier, email=customer_email, stripe_session_id=session_id)
        db.add(db_key)
        db.commit()
        db.refresh(db_key)

        print(f"Generated key {new_key} for {customer_email} (Tier: {tier})")

        # Send Email via Gmail SMTP
        if GMAIL_ADDRESS and GMAIL_APP_PASSWORD and customer_email:
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = "Your Understand-Anything License Key"
                msg["From"] = f"Understand-Anything Licensing <{GMAIL_ADDRESS}>"
                msg["To"] = customer_email
                
                html_content = f"<p>Thanks for your purchase!</p><p>Your {tier} tier license key is: <strong>{new_key}</strong></p><p>Setup: Configure your .env with UA_LICENSE_KEY={new_key}</p>"
                msg.attach(MIMEText(html_content, "html"))

                with smtplib.SMTP("smtp.gmail.com", 587) as server:
                    server.starttls()
                    server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
                    server.send_message(msg)
                
                print(f"Email sent successfully to {customer_email}")
            except Exception as e:
                print(f"Failed to send email to {customer_email}: {e}")

    return {"status": "success"}
