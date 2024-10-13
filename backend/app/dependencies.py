import os
import uuid
from fastapi import Depends, Form, HTTPException, UploadFile, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from pydantic import UUID4
from app import data, schemas, chat_models
from app.config import config
from typing import cast

def get_db():
    db = data.SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/users/token')
        
async def get_current_user(token: str = Depends(oauth2_scheme), db: data.Session = Depends(get_db)) -> schemas.user.User:
    """Get the current user from the JWT token

    Args:
        token (str, optional): The JWT token. Defaults to Depends(oauth2_scheme).

    Raises:
        credentials_exception: If the token is invalid or the user does not exist

    Returns:
        schemas.User: The user associated with the token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, config.secret_key, algorithms=[config.algorithm])
        user_id: UUID4 = uuid.UUID(payload.get('sub'))
        if user_id is None:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception
    db_user = data.crud.get_user(db, user_id)
    if db_user is None:
        raise credentials_exception
    return db_user

async def get_chat(chat_id: UUID4, db: data.Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)) -> data.models.Chat:
    db_chat = data.crud.get_chat(db, chat_id=chat_id)
    if db_chat is None:
        raise HTTPException(status_code=404, detail='Chat not found')
    if db_chat.user_id != current_user.id:
        raise HTTPException(status_code=403, detail='Not authorized to access chat')
    return db_chat

def get_message(message: str = Form()) -> schemas.Message:
    return schemas.Message.model_validate_json(message)

async def get_model(message: schemas.Message = Depends(get_message), chat: data.models.Chat = Depends(get_chat), db: data.Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    if message.model is not None:
        # user can select a model for a single message
        model_type = chat_models.get_chat_model(message.model)
    else:
        # otherwise use the default model for the chat
        model_type = chat_models.get_chat_model(cast(str, chat.default_model))
    key = None
    if model_type.requires_key:
        db_key = data.crud.get_api_key(db, current_user.id, model_type.api_provider)
        if db_key is None:
            raise HTTPException(status_code=400, detail='No API key registered for model for this user')
        key = db_key.key
    if message.config is not None:
        config = message.config
    else:
        config = cast(dict, chat.config)
    model = model_type(api_key=cast(str, key), config=config) # construct model instance, using API key if required
    message.model = None # user messages should not have a model; this was just for the model selection
    return model, config

def save_images(chat_id: UUID4, files: list[UploadFile] | None = None, message: schemas.Message = Depends(get_message)) -> schemas.Message:
    """Save image files to disk and update message content to include file paths

    Args:
        chat_id (UUID4): The chat ID to which the message belongs / will belong
        files (list[UploadFile] | None, optional): The list of files uploaded with the message. Defaults to None, in which case the function should have no effect.
        message (schemas.MessageCreate, optional): The message to process. Defaults to Depends(get_message).

    Raises:
        HTTPException: If the message contains an image content but no file is provided whose filename matches the content

    Returns:
        schemas.MessageCreate: The message with updated content, where image content is replaced with local file paths
    """
    for c in message.contents:
        if c.type == schemas.MessageContentType.IMAGE:
            if files is None:
                raise HTTPException(status_code=400, detail='Image content requires a file')
            image = next((f for f in files if f.filename == c.content), None)
            if image is None:
                raise HTTPException(status_code=400, detail='Image content file not found')
            image_data = image.file.read()
            # save image to disk and set content to file path
            if not os.path.exists(f'images/{chat_id}'):
                os.makedirs(f'images/{chat_id}')
            with open(f'images/{chat_id}/{c.content}', 'wb') as f:
                f.write(image_data)
            c.content = f'images/{chat_id}/{c.content}'
            c.image_type = image.content_type
    return message

system_user: data.models.User | None = None # global user for system messages
assistant_user: data.models.User | None = None # global user for assistant messages

def get_system_user(db: data.Session = Depends(get_db)) -> data.models.User:
    """Get the system user from the database

    Args:
        db (data.Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        data.models.User: The system user
    """
    global system_user
    if system_user is None:
        system_user = data.crud.get_user_by_email(db, email=config.system_email)
        if system_user is None:
            system_user = data.crud.create_user(db, user=schemas.UserCreate(email=config.system_email, password='password'))
    return system_user

def get_assistant_user(db: data.Session = Depends(get_db)) -> data.models.User:
    """Get the assistant user from the database

    Args:
        db (data.Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        data.models.User: The assistant user
    """
    global assistant_user
    if assistant_user is None:
        assistant_user = data.crud.get_user_by_email(db, email=config.assistant_email)
        if assistant_user is None:
            assistant_user = data.crud.create_user(db, user=schemas.UserCreate(email=config.assistant_email, password='password'))
    return assistant_user