from sqlalchemy.orm import Session
from pydantic import UUID4

from data import models
import schemas

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
    db_chat: models.Chat | None = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
    if db_chat is None:
        raise ValueError('Chat not found')
    db_chat.title = chat.title
    db_chat.default_model = chat.default_model
    db_chat.config = chat.config
    db_system_msg = db.query(models.Message).filter(models.Message.chat_id == chat_id, models.Message.role == schemas.Role.SYSTEM).first()
    if db_system_msg is not None:
        db_system_msg.content = chat.system_prompt
    db.commit()
    db.refresh(db_chat)
    return db_chat

def create_message(db: Session, message: schemas.MessageBase, user_id: UUID4, chat_id: UUID4):
    contents = message.contents
    message_dict = message.model_dump()
    message_dict.pop('contents', None)
    db_message = models.Message(**message_dict, user_id=user_id, chat_id=chat_id)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    try:
        for i, content in enumerate(contents):
            db_content = models.MessageContent(**content.model_dump(), message_id=db_message.id, order=i)
            db.add(db_content)
        db.commit()
        db.refresh(db_message)
        return db_message
    except Exception as e:
        db.delete(db_message)
        db.commit()
        raise e

def update_message(db: Session, message_id: UUID4, message: schemas.MessageBase):
    db_message = db.query(models.Message).filter(models.Message.id == message_id).first()
    if db_message is None:
        raise ValueError('Message not found')
    db_message.role = message.role
    # db_message.contents = message.contents
    for content in db_message.contents:
        db.delete(content)
    for i, content in enumerate(message.contents):
        db_content = models.MessageContent(**content.model_dump(), message_id=message_id, order=i)
        db.add(db_content)
    db_message.model = message.model
    if message.config is not None:
        db_message.config = message.config
    db.commit()
    db.refresh(db_message)
    return db_message

def delete_message(db: Session, message_id: UUID4):
    db_message = db.query(models.Message).filter(models.Message.id == message_id).first()
    if db_message is None:
        raise ValueError('Message not found')
    db.delete(db_message)
    db.commit()
    return db_message

def create_api_key(db: Session, api_key: schemas.ModelAPIKeyCreate, user_id: UUID4):
    existing_provider_key = db.query(models.APIKey).filter(models.APIKey.user_id == user_id, models.APIKey.provider == api_key.provider).first()
    if existing_provider_key is not None:
        existing_provider_key.key = api_key.key
        db_api_key = existing_provider_key
    else:
        db_api_key = models.APIKey(**api_key.model_dump(), user_id=user_id)
        db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)
    return db_api_key

def get_api_key(db: Session, user_id: UUID4, provider: schemas.ModelAPI) -> models.APIKey | None:
    return db.query(models.APIKey).filter(models.APIKey.user_id == user_id, models.APIKey.provider == provider).first()

def update_api_key(db: Session, user_id: UUID4, api_key: schemas.ModelAPIKeyCreate):
    db_api_key = db.query(models.APIKey).filter(models.APIKey.user_id == user_id, models.APIKey.provider == api_key.provider).first()
    if db_api_key is None:
        raise ValueError('API key not found')
    db_api_key.key = api_key.key
    db.commit()
    db.refresh(db_api_key)
    return db_api_key

def delete_api_key(db: Session, user_id: UUID4, provider: schemas.ModelAPI):
    db_api_key = db.query(models.APIKey).filter(models.APIKey.user_id == user_id, models.APIKey.provider == provider).first()
    if db_api_key is None:
        raise ValueError('API key not found')
    db.delete(db_api_key)
    db.commit()
    return db_api_key

def get_user_api_providers(db: Session, user_id: UUID4) -> list[schemas.ModelAPI]:
    return db.query(models.APIKey.provider).filter(models.APIKey.user_id == user_id).all()