import smtplib
from email.mime.text import MIMEText
import logging
from fastapi import HTTPException
import os
from dotenv import load_dotenv

load_dotenv()

def send_invitation_email(email: str,project_name: str, token: str):
    subject = f"Invitation à collaborer sur le projet {project_name}"
    accept_url = f"http://your-frontend-domain.com/accept/{token}"
    body = f"""
    Bonjour,

    Vous avez été invité(e) à collaborer sur le projet "{project_name}".
    Cliquez sur le lien suivant pour accepter l'invitation :
    {accept_url}
    Si vous ne souhaitez pas collaborer, ignorez cet email.
    """
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = os.getenv("yosra.abid.tn@gmail.com")
    msg['To'] = email

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login("yosra.abid.tn@gmail.com", "atrhikjcalgohrja")
            server.send_message(msg)
        logging.info("Email d'invitation envoyé avec succès")
    except Exception as e:
        logging.error(f"Erreur lors de l'envoi de l'email d'invitation : {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'envoi de l'email d'invitation.")
