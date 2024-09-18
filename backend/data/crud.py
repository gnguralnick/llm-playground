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

def get_message(db: Session, message_id: int):
    return db.query(models.Message).filter(models.Message.id == message_id).first()

def create_chat(db: Session, chat: schemas.ChatCreate, user_id: int):
    chat = chat.model_dump()
    chat.pop('system_prompt', None)
    db_chat = models.Chat(**chat, user_id=user_id)
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    return db_chat

def update_chat(db: Session, chat_id: int, chat: schemas.ChatCreate):
    db_chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
    db_chat.title = chat.title
    db_system_msg = db.query(models.Message).filter(models.Message.chat_id == chat_id and models.Message.role == schemas.Role.SYSTEM).first()
    db_system_msg.content = chat.system_prompt
    db.commit()
    db.refresh(db_chat)
    return db_chat

def create_message(db: Session, message: schemas.MessageCreate, user_id: int, chat_id: int):
    db_message = models.Message(**message.model_dump(), user_id=user_id, chat_id=chat_id)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def update_message(db: Session, message_id: int, message: schemas.MessageCreate):
    db_message = db.query(models.Message).filter(models.Message.id == message_id).first()
    db_message.content = message.content
    db_message.role = message.role
    db.commit()
    db.refresh(db_message)
    return db_message