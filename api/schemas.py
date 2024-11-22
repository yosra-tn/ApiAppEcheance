from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List


class UpdatePassword(BaseModel):
    old_password: str
    new_password: str

class TokenRequest(BaseModel):
    token: str
class InviteRequest(BaseModel):
    email: str
    event_name: str
class EventCreate(BaseModel):
    user_id: str
    title: str
    startDate: datetime
    endDate: datetime
    category: Optional[str] = None
    typeOcc: Optional[str] = None

class EventResponse(BaseModel):
    id: str
    user_id: str
    title: str
    startDate: datetime
    endDate: datetime
    category: Optional[str] = None
    typeOcc: Optional[str] = None

class CollaborateurBase(BaseModel):
    email: str
    event_id: str
    permission: str
class CollaborateurCreate(BaseModel):
    pass

class CollaborateurResponse(BaseModel):
    id: str
    email: str
    event_id: str
    permission: str

class Collaborateur(CollaborateurBase):
    id: str

class ProjectResponse(BaseModel):
    id: str
    title: str
    collaborators: List[CollaborateurResponse]

class InvitationCreate(BaseModel):
    email: str
    event_id: str

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class User(BaseModel):
    id: str
    username: str
    email: str
    created_at: datetime
    last_login: datetime

    class Config:
        from_attributes = True



