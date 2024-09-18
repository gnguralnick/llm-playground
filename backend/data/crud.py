from sqlalchemy.orm import Session

from data import models, schemas

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = user.password # TODO: hash the password
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_chat(db: Session, chat_id: int):
    return db.query(models.Chat).filter(models.Chat.id == chat_id).first()

def get_chats(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Chat).filter(models.Chat.user_id == user_id).offset(skip).limit(limit).all()

def create_chat(db: Session, chat: schemas.ChatCreate, user_id: int):
    db_chat = models.Chat(**chat.model_dump(), user_id=user_id)
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    return db_chat

def update_chat(db: Session, chat_id: int, chat: schemas.ChatCreate):
    db_chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
    db_chat.title = chat.title
    db.commit()
    db.refresh(db_chat)
    return db_chat

def create_message(db: Session, message: schemas.MessageCreate, user_id: int, chat_id: int):
    db_message = models.Message(**message.model_dump(), user_id=user_id, chat_id=chat_id)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message