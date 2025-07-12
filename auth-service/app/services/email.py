# app/services/email.py
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.core.config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_TLS=True,
    MAIL_SSL=False,
    USE_CREDENTIALS=True,
)

async def send_verification_email(email_to: str, link: str):
    message = MessageSchema(
        subject="Please verify your email",
        recipients=[email_to],
        body=f"Click this link to verify your email: {link}",
        subtype="plain"
    )

    fm = FastMail(conf)
    
    print("waiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiit")
    print(message)
    await fm.send_message(message)
    print("waiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiit")
    print(fm)
