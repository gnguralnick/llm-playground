from sqlalchemy.orm import Session
from pydantic import UUID4

from data import models, schemas



def get_user(db: Session, user_id: UUID4) -> models.User | None:
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> models.User | None:
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> list[models.User]:
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    from data.auth import get_password_hash
    hashed_password = get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_chat(db: Session, chat_id: UUID4) -> models.Chat | None:
    return db.query(models.Chat).filter(models.Chat.id == chat_id).first()

def get_chats(db: Session, user_id: UUID4, skip: int = 0, limit: int = 100):
    return db.query(models.Chat).filter(models.Chat.user_id == user_id).order_by(models.Chat.created_at.desc()).offset(skip).limit(limit).all()

def get_message(db: Session, message_id: UUID4):
    return db.query(models.Message).filter(models.Message.id == message_id).first()

def create_chat(db: Session, chat: schemas.ChatCreate, user_id: UUID4):
    chat_dict = chat.model_dump()
    chat_dict.pop('system_prompt', None)
    db_chat = models.Chat(**chat_dict, user_id=user_id)
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    return db_chat

def update_chat(db: Session, chat_id: UUID4, chat: schemas.ChatCreate):
    db_chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
    if db_chat is None:
        raise ValueError('Chat not found')
    db_chat.title = chat.title
    db_chat.default_model = chat.default_model
    db_system_msg = db.query(models.Message).filter(models.Message.chat_id == chat_id and models.Message.role == schemas.Role.SYSTEM).first()
    if db_system_msg is not None:
        db_system_msg.content = chat.system_prompt
    db.commit()
    db.refresh(db_chat)
    return db_chat

def create_message(db: Session, message: schemas.MessageCreate, user_id: UUID4, chat_id: UUID4):
    db_message = models.Message(**message.model_dump(), user_id=user_id, chat_id=chat_id)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def update_message(db: Session, message_id: UUID4, message: schemas.MessageCreate):
    db_message = db.query(models.Message).filter(models.Message.id == message_id).first()
    if db_message is None:
        raise ValueError('Message not found')
    db_message.role = message.role
    db_message.content = message.content
    db_message.model = message.model
    db.commit()
    db.refresh(db_message)
    return db_message