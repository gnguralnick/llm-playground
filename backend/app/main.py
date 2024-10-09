from collections.abc import Generator
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, status, UploadFile, Form
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from config import config
import data
import schemas

from contextlib import asynccontextmanager
from pydantic import UUID4, BaseModel
import uuid
from typing import cast

from datetime import datetime, timedelta, timezone

import os

from chat_models import get_chat_model, get_models, ModelInfo, ChatModel, StreamingChatModel, get_chat_model_info
from util import ModelConfig, Role

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
from jwt.exceptions import InvalidTokenError

system_user: data.models.User | None = None # global user for system messages
assistant_user: data.models.User | None = None # global user for assistant messages

@asynccontextmanager
async def lifespan(app: FastAPI):
    global system_user
    global assistant_user
    db = data.SessionLocal()
    system_user = data.crud.get_user_by_email(db, email=config.system_email)
    if system_user is None:
        system_user = data.crud.create_user(db, user=schemas.UserCreate(email=config.system_email, password='password'))
    assistant_user = data.crud.get_user_by_email(db, email=config.assistant_email)
    if assistant_user is None:
        assistant_user = data.crud.create_user(db, user=schemas.UserCreate(email=config.assistant_email, password='password'))
    db.close()
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.allowed_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

def get_db():
    db = data.SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
@app.post('/users/', response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: data.Session = Depends(get_db)):
    """Create a new user

    Args:
        user (schemas.UserCreate): The user to create

    Raises:
        HTTPException: If the email is already registered

    Returns:
        schemas.User: The newly created user
    """
    db_user = data.crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail='Email already registered')
    return data.crud.create_user(db=db, user=user)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Create a JWT access token

    Args:
        data (dict): The data to encode in the token
        expires_delta (timedelta | None, optional): The expiration time for the token. Defaults to None.

    Returns:
        str: The encoded JWT access token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=10)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.secret_key, algorithm=config.algorithm)
    return encoded_jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

async def get_current_user(token: str = Depends(oauth2_scheme), db: data.Session = Depends(get_db)) -> schemas.User:
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
    except InvalidTokenError:
        raise credentials_exception
    db_user = data.crud.get_user(db, user_id)
    if db_user is None:
        raise credentials_exception
    return db_user

class Token(BaseModel):
    access_token: str
    token_type: str

@app.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: data.Session = Depends(get_db)
) -> Token:
    user = data.auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=config.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@app.get('/users/me', response_model=schemas.User)
def read_users_me(current_user: schemas.User = Depends(get_current_user)):
    return current_user

@app.get('/users/me/api_key/', response_model=list[schemas.ModelAPIKeyBase])
def read_api_keys(db: data.Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    return data.crud.get_user_api_providers(db=db, user_id=current_user.id)

@app.post('/users/me/api_key/', response_model=schemas.ModelAPIKeyBase)
def create_api_key(api_key: schemas.ModelAPIKeyCreate, db: data.Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    return data.crud.create_api_key(db=db, api_key=api_key, user_id=current_user.id)

@app.delete('/users/me/api_key/{provider}')
def delete_api_key(provider: schemas.ModelAPI, db: data.Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    data.crud.delete_api_key(db=db, user_id=current_user.id, provider=provider)
    return {'message': 'API key deleted', }

@app.put('/users/me/api_key/{provider}', response_model=schemas.ModelAPIKeyBase)
def update_api_key(api_key: schemas.ModelAPIKeyCreate, db: data.Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    return data.crud.update_api_key(db=db, user_id=current_user.id, api_key=api_key)

@app.get('/chat/', response_model=list[schemas.ChatView])
def read_chats(skip: int = 0, limit: int = 100, db: data.Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    return data.crud.get_chats(db, user_id=current_user.id, skip=skip, limit=limit)

@app.post('/chat/', response_model=schemas.Chat)
def create_chat(chat: schemas.ChatCreate, db: data.Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    chat_db = data.crud.create_chat(db=db, chat=chat, user_id=current_user.id)
    system_msg = schemas.MessageBuilder(role=Role.SYSTEM).add_text(chat.system_prompt).build()
    if system_user is None:
        raise HTTPException(status_code=500, detail='System user not found')
    data.crud.create_message(db=db, message=system_msg, user_id=cast(UUID4, system_user.id), chat_id=cast(UUID4, chat_db.id))
    return chat_db

async def get_chat(chat_id: UUID4, db: data.Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)) -> data.models.Chat:
    db_chat = data.crud.get_chat(db, chat_id=chat_id)
    if db_chat is None:
        raise HTTPException(status_code=404, detail='Chat not found')
    if db_chat.user_id != current_user.id:
        raise HTTPException(status_code=403, detail='Not authorized to access chat')
    return db_chat

@app.get('/chat/{chat_id}', response_model=schemas.Chat)
def read_chat(chat: data.models.Chat = Depends(get_chat)):
    return chat

@app.get('/images/{chat_id}/{image_path}', response_class=FileResponse)
def read_image(chat_id: UUID4, image_path: str, chat: data.models.Chat = Depends(get_chat)):
    return f'images/{chat_id}/{image_path}'

@app.put('/chat/{chat_id}', response_model=schemas.Chat)
def update_chat(chat: schemas.ChatCreate, db_chat: data.models.Chat = Depends(get_chat), db: data.Session = Depends(get_db)):
    return data.crud.update_chat(db=db, chat_id=cast(UUID4, db_chat.id), chat=chat)

@app.delete('/chat/{chat_id}')
def delete_chat(db: data.Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user), db_chat: data.models.Chat = Depends(get_chat)):
    db.delete(db_chat)
    db.commit()
    return {'message': 'Chat deleted', }

def get_message(message: str = Form()) -> schemas.MessageCreate:
    return schemas.MessageCreate.model_validate_json(message)

async def get_model(message: schemas.MessageCreate = Depends(get_message), chat: data.models.Chat = Depends(get_chat), db: data.Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    if message.model is not None:
        # user can select a model for a single message
        model_type = get_chat_model(message.model)
    else:
        # otherwise use the default model for the chat
        model_type = get_chat_model(cast(str, chat.default_model))
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

def save_images(chat_id: UUID4, files: list[UploadFile] | None = None, message: schemas.MessageCreate = Depends(get_message)) -> schemas.MessageCreate:
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

@app.post('/chat/{chat_id}/', response_model=schemas.MessageView)
def send_message(chat_id: UUID4, message = Depends(save_images), db: data.Session = Depends(get_db), db_chat: data.models.Chat = Depends(get_chat), model_with_config: tuple[ChatModel, ModelConfig] = Depends(get_model)):
    chat: schemas.chat.Chat = schemas.chat.Chat.model_validate(db_chat, from_attributes=True)
    
    model, config = model_with_config
    if assistant_user is None:
        raise HTTPException(status_code=500, detail='Assistant user not found')

    response_msg = model.chat(cast(list, chat.messages) + [message])
    db_msg = data.crud.create_message(db=db, message=message, user_id=uuid.UUID("c0aba09b-f57e-4998-bee6-86da8b796c5b"), chat_id=chat_id)
    try:
        return data.crud.create_message(db=db, message=response_msg, user_id=cast(UUID4, assistant_user.id), chat_id=chat_id)
    except Exception as e:
        data.crud.delete_message(db=db, message_id=cast(UUID4, db_msg.id))
        raise HTTPException(status_code=400, detail=str(e))
        
def handle_stream(msg_id: uuid.UUID, db: data.Session, model: str, stream: Generator[str, None, None]):
    """Process a stream of tokens from a chat model and update the message in the database when the stream ends

    Args:
        msg_id (uuid.UUID): The ID of the message to update - a loading message that will be replaced with the final model response
        db (data.Session): The database session
        model (str): The name of the model
        stream (Generator[str, None, None]): The stream of tokens from the model

    Raises:
        HTTPException: If the assistant user is not initialized

    Yields:
        str: The tokens from the stream
    """
    if assistant_user is None:
        raise HTTPException(status_code=500, detail='Assistant user not found')

    message = ''
    while True:
        try:
            token = next(stream)
        except StopIteration:
            break
        if token is None:
            break
        message += token
        yield token
    
    new_message = schemas.MessageBuilder(role=schemas.Role.ASSISTANT, model=model).add_text(message).build()
    data.crud.update_message(db=db, message_id=msg_id, message=new_message)

@app.post('/chat/{chat_id}/stream/', response_model=dict)
async def send_message_stream(chat_id: UUID4, message = Depends(save_images), db: data.Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user), db_chat: data.models.Chat = Depends(get_chat), model_with_config: tuple[ChatModel, ModelConfig] = Depends(get_model)):
    chat: schemas.chat.Chat = schemas.chat.Chat.model_validate(db_chat, from_attributes=True)
    
    model, config = model_with_config
    if assistant_user is None:
        raise HTTPException(status_code=500, detail='Assistant user not found')

    if not isinstance(model, StreamingChatModel):
        raise HTTPException(status_code=400, detail='Model does not support streaming')
    
    db_msg = data.crud.create_message(db=db, message=message, user_id=uuid.UUID("c0aba09b-f57e-4998-bee6-86da8b796c5b"), chat_id=chat_id)
    
    # create a temporary loading message to show the user that the model is processing
    loading_msg = schemas.MessageBuilder(role=schemas.Role.ASSISTANT, model=model.api_name, config=config).add_text('LOADING').build()
    loading_msg_db = data.crud.create_message(db=db, message=loading_msg, user_id=cast(UUID4, assistant_user.id), chat_id=chat_id)
    
    try:
        stream = model.chat_stream(cast(list, chat.messages) + [message])
        
        return StreamingResponse(handle_stream(cast(UUID4, loading_msg_db.id), db, model.api_name, stream))
    except Exception as e:
        # if an error occurs, delete the loading message and the message that was sent to the model
        data.crud.delete_message(db=db, message_id=cast(UUID4, loading_msg_db.id))
        data.crud.delete_message(db=db, message_id=cast(UUID4, db_msg.id))
        raise HTTPException(status_code=400, detail=str(e))

@app.get('/models/', response_model=list[ModelInfo])
def read_models(db: data.Session = Depends(get_db), user: schemas.User = Depends(get_current_user)):
    models = get_models()
    for model in models:
        if model.requires_key:
            has_key = data.crud.get_api_key(db, cast(UUID4, user.id), model.api_provider) is not None
            model.user_has_key = has_key
    return models

@app.get('/models/{model_name}', response_model=ModelInfo)
def read_model(model_name: str, db: data.Session = Depends(get_db), user: schemas.User = Depends(get_current_user)):
    model_info = get_chat_model_info(model_name)
    if model_info.requires_key:
        has_key = data.crud.get_api_key(db, cast(UUID4, user.id), model_info.api_provider) is not None
        model_info.user_has_key = has_key
    return model_info

@app.get('/')
async def root():
    return {'message': 'Hello, World!'}