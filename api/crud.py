from typing import Optional
from uuid import uuid4

from fastapi import HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
import bcrypt
from api.invi_send import send_invitation_email
from api.models import User, Event, Reminder, PendingInvitation, Collaborateur
from api.schemas import UserCreate, EventCreate, InvitationCreate,UpdatePassword as data
import logging

logging.basicConfig(level=logging.INFO)  # Set the logging level
logger = logging.getLogger(__name__)

def create_user(db: Session, user: UserCreate):
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    db_user = User(
        username=user.username,
        email=user.email,
        password=hashed_password,
        created_at=datetime.utcnow(),
        last_login=datetime.utcnow()
    )
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        if "UNIQUE constraint" in str(e):
            raise HTTPException(status_code=400, detail="Username or email already exists.")
        print(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

def createEvent(db: Session, event: EventCreate):
    db_event = Event(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    reminder_date = db_event.endDate
    db_reminder = Reminder(event_id=db_event.id, reminder_date=reminder_date)
    db.add(db_reminder)
    db.commit()
    db.refresh(db_reminder)
    return db_event

def get_events_crud(db: Session, user_id: str, search: Optional[str] = Query(None), category: Optional[str] = Query(None)):
    query = db.query(Event).filter(Event.user_id == user_id)
    if search:
        query = query.filter(Event.title.ilike(f"%{search}%"))
    if category:
        query = query.filter(Event.category == category)

    events = query.all()

    if not events:
        logger.warning(f"No events found for user_id: {user_id} with search: {search} and category: {category}")
        raise HTTPException(status_code=404, detail="No events found")

    return events


def get_event_crud(db: Session, event_id: str):
    return db.query(Event).filter(Event.id == event_id).all()

def update_event_crud(db: Session, event_id: str, event: EventCreate):
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if db_event:
        for key, value in event.dict().items():
            setattr(db_event, key, value)
        db.commit()
        db.refresh(db_event)

        db_reminder = db.query(Reminder).filter(Reminder.event_id == event_id).first()
        if db_reminder:
            db_reminder.title = event.title
            db_reminder.reminder_date = event.endDate
            db.commit()
            db.refresh(db_reminder)

        return db_event
    return None

def delete_event_crud(db: Session, event_id: str):
    db_reminder = db.query(Reminder).filter(Reminder.event_id == event_id).first()
    if db_reminder:
        db.delete(db_reminder)
        db.commit()

    db_event = db.query(Event).filter(Event.id == event_id).first()
    if db_event:
        db.delete(db_event)
        db.commit()
        return True
    return False


def make_rappel_sent(db: Session,reminder_id:str):
    db_reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if db_reminder is None:
        raise HTTPException(status_code=404, detail="Rappel not found")
    db_reminder.is_reminder_sent = True
    db.commit()
    return db_reminder

def create_pending_invitation(db: Session, invitation: InvitationCreate):
    token = str(uuid4())
    pending_invitation = PendingInvitation(email=invitation.email, project_id=invitation.project_id, token=token)
    db.add(pending_invitation)
    db.commit()
    db.refresh(pending_invitation)
    # Envoyer un email contenant le lien avec le token
    send_invitation_email(invitation.email, token)  # Fonction à définir pour envoyer l'e-mail
    return pending_invitation

def get_pending_invitation_by_token(db: Session, token: str):
    return db.query(PendingInvitation).filter(PendingInvitation.token == token).first()

def mark_invitation_as_accepted(db: Session, invitation: PendingInvitation):
    invitation.is_accepted = True
    db.commit()

def add_collaborator(db: Session, email: str, project_id: int):
    collaborator = Collaborateur(email=email, project_id=project_id)
    db.add(collaborator)
    db.commit()
    db.refresh(collaborator)
    return collaborator


def get_user_crud(db: Session, user_id: str):
   return db.query(User).filter(User.id == user_id).first()

def hash_password(password: str) -> str:
    # Génère un "sel" pour un hachage sécurisé avec bcrypt
    salt = bcrypt.gensalt()
    # Hache le mot de passe avec le "sel" généré
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

# Fonction pour vérifier le mot de passe
def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Vérifie si le mot de passe en clair correspond au hash stocké
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
# Fonction pour mettre à jour le mot de passe dans la base de données
def update_password(db: Session, user_id: str, old_password: str, new_password: str):
    db_user = db.query(User).filter(User.id == user_id).first()

    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Vérifier si le mot de passe ancien est correct
    if not verify_password(old_password, db_user.password):
        raise HTTPException(status_code=400, detail="Incorrect old password")

    # Hacher le nouveau mot de passe
    hashed_new_password = hash_password(new_password)

    # Mettre à jour le mot de passe dans la base de données
    db_user.password = hashed_new_password
    db.commit()
    db.refresh(db_user)

    return db_user