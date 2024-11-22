import smtplib
import uuid
from datetime import date
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
import bcrypt
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from apscheduler.schedulers.background import BackgroundScheduler
from api.models import Event, User, Reminder, Collaborateur
from api import crud, models
from api.crud import get_user_crud, update_password
from api.invi_send  import send_invitation_email
from api.database import SessionLocal, init_db
from api.schemas import UserCreate, User as UserResponse, EventResponse, EventCreate, CollaborateurResponse, \
    CollaborateurCreate, InviteRequest, TokenRequest, UpdatePassword, ProjectResponse
from api.schemas import Collaborateur as Col
# configuration de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger('apscheduler').setLevel(logging.DEBUG)

app = FastAPI()
def send_email(email_to: str, subject: str, msgBody: str):
    sender_email = "yosra.abid.tn@gmail.com"
    password = "atrhikjcalgohrja"
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = email_to
    msg['Subject'] = subject
    msg.attach(MIMEText(msgBody, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, email_to, msg.as_string())
            logging.info("Email envoyé avec succès")
    except smtplib.SMTPAuthenticationError:
        logging.error("Erreur d'authentification SMTP : Vérifiez l'e-mail et le mot de passe.")
        raise HTTPException(status_code=401, detail="Erreur d'authentification SMTP.")
    except Exception as e:
        logging.error(f"Erreur lors de l'envoi de l'email: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'envoi de l'email.")

def scheduler_task():
    logging.info("Exécution de la tâche planifiée.")
    db = SessionLocal()
    try:
        today = date.today()
        logging.info(f"Date actuelle pour vérification des échéances : {today}")
        events = db.query(Event).filter(func.date(Event.endDate) == today).all()
        logging.info(f"Nombre d'échéances trouvées : {len(events)}")

        for event in events:
            reminders = db.query(Reminder).filter(Reminder.event_id == event.id, Reminder.is_reminder_sent == False).all()
            logging.info(f"Nombre de rappels trouvés : {len(reminders)}")
            for reminder in reminders:
                user = db.query(User).filter(User.id == event.user_id).first()
                if user:
                    logging.info(f"Envoi d'email à {user.email} pour l'échéance {event.title}.")
                    send_email(user.email, "Rappel d'Échéance", f"Ceci est un rappel que l'échéance de votre événement intitulé  {event.title} approche. Celui-ci est prévu pour le {event.endDate}. Merci de vérifier et de vous assurer que tout est en ordre d'ici cette date.")
                    reminder.is_reminder_sent = True
                    db.commit()
                    logging.info(f"Marqué comme envoyé pour rappel ID {reminder.id}")
    except Exception as e:
        logging.error(f"Erreur lors de l'exécution de la tâche planifiée : {e}")
    finally:
        db.close()
        logging.info("Fin de l'exécution de la tâche planifiée.")

scheduler = BackgroundScheduler()
scheduler.add_job(scheduler_task, 'cron', hour=0)  # Exécute tous les jours à minuit
scheduler.start()



app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

init_db()

@app.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    logging.info(f"Tentative d'enregistrement de l'utilisateur : {user.username}")
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Nom d'utilisateur déjà enregistré")
    db_user = crud.create_user(db, user)
    return db_user

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    userId: str
    message: str

@app.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == request.username).first()
    if not user or not bcrypt.checkpw(request.password.encode('utf-8'), user.password.encode('utf-8')):
        raise HTTPException(status_code=400, detail="Nom d'utilisateur ou mot de passe incorrect")
    return {"message": "Connexion réussie", "userId": user.id}

@app.post("/events", response_model=EventResponse)
def add_event(event: EventCreate, db: Session = Depends(get_db)):
    return crud.createEvent(db, event)

@app.get("/events", response_model=List[EventResponse])
def get_events(user_id: str,search: Optional[str] = Query(None), category: Optional[str] = Query(None) ,db: Session = Depends(get_db)):
    return crud.get_events_crud(db, user_id,search,category)

@app.put("/events/{event_id}", response_model=EventResponse)
def update_event(event: EventCreate, event_id: str, db: Session = Depends(get_db)):
    updated_event = crud.update_event_crud(db, event_id, event)
    if not updated_event:
        raise HTTPException(status_code=404, detail="Événement non trouvé")
    return updated_event

@app.delete("/events/{event_id}", response_model=EventResponse)
def delete_event(event_id: str, db: Session = Depends(get_db)):
    deleted_event = crud.delete_event_crud(db, event_id)
    if not deleted_event:
        raise HTTPException(status_code=404, detail="Événement non trouvé")
    return deleted_event

@app.post("/inviter/")
def inviter_collaborateur(request: InviteRequest, db: Session = Depends(get_db)):
    # Vérifier si l'événement existe
    event = db.query(models.Event).filter(models.Event.title == request.event_name).first()
    if not event:
        raise HTTPException(status_code=404, detail=f"Event with ID {request.event_id} not found.")

    # Générer un jeton unique pour l'invitation
    token = str(uuid.uuid4())

    # Créer une entrée dans la table des invitations en attente
    pending_invitation = models.PendingInvitation(email=request.email,project_name=event.title , event_id=event.id, token=token)
    db.add(pending_invitation)
    db.commit()

    # Envoyer l'e-mail d'invitation avec le jeton
    send_invitation_email(request.email, token)

    return {"message": "Invitation envoyée avec succès"}
@app.get("/accept/{token}")
def accept_invitation(token: str, db: Session = Depends(get_db)):
    pending_invitation = db.query(models.PendingInvitation).filter(models.PendingInvitation.token == token).first()

    if not pending_invitation:
        raise HTTPException(status_code=404, detail="Invitation non trouvée ou déjà traitée.")

    # Ajouter le collaborateur
    new_collaborateur = models.Collaborateur(
        email=pending_invitation.email,
        event_id=pending_invitation.event_id,
        permission='read'
    )
    db.add(new_collaborateur)

    # Supprimer l'invitation en attente
    db.delete(pending_invitation)
    db.commit()

    return {"message": "Vous avez accepté l'invitation. Merci de rejoindre le projet."}


@app.get("/collaborateurs/", response_model=List[Col])
def read_collaborateurs(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(Collaborateur).offset(skip).limit(limit).all()


@app.put("/update_permission/", response_model=dict)
def update_permission(email: str, permission: str, db: Session = Depends(get_db)):
    collab = db.query(Collaborateur).filter(Collaborateur.email == email).first()  # Obtenez le premier collaborateur
    if not collab:
        raise HTTPException(status_code=404, detail='Collaborateur non trouvé')
    else:
        collab.permission = permission  # Mettez à jour la permission
        db.commit()  # Validez la transaction
        return {"message": f"Permission mise à jour pour {collab.email} à '{collab.permission}'"}  # Utilisez l'objet collab

@app.put("/update_password/")
def update_mdp(
    data: UpdatePassword,
    user_id: str,
    db: Session = Depends(get_db)
):

    updated_user = update_password(db, user_id, data.old_password, data.new_password)
    return {"message": "Password updated successfully", "user": updated_user}


@app.get("/get_user/", response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db)):
    db_user = get_user_crud(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return db_user

@app.get("/user/{user_id}/collaborators", response_model=dict)
def get_user_collaborators(user_id: str, db: Session = Depends(get_db)):
    # Vérifie si l'utilisateur existe
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Récupère les événements de l'utilisateur
    events = db.query(Event).filter(Event.user_id == user_id).all()
    if not events:
        raise HTTPException(status_code=404, detail="No events found for this user")

    # Prépare une réponse avec les collaborateurs par événement
    result = {}
    for event in events:
        collaborators = db.query(Collaborateur).filter(Collaborateur.event_id == event.id).all()
        result[event.title] = [
            {"email": c.email, "permission": c.permission} for c in collaborators
        ]

    return {"user_id": user_id, "collaborators": result}