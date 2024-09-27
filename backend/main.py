from collections.abc import Generator
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, status
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from config import config
import data
from contextlib import asynccontextmanager
from pydantic import UUID4, BaseModel
import uuid
from typing import cast

from datetime import datetime, timedelta, timezone

from models import get_chat_model, get_models, ModelInfo, ChatModel

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
        system_user = data.crud.create_user(db, user=data.schemas.UserCreate(email=config.system_email, password='password'))
    assistant_user = data.crud.get_user_by_email(db, email=config.assistant_email)
    if assistant_user is None:
        assistant_user = data.crud.create_user(db, user=data.schemas.UserCreate(email=config.assistant_email, password='password'))
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
        
@app.post('/users/', response_model=data.schemas.User)
def create_user(user: data.schemas.UserCreate, db: data.Session = Depends(get_db)):
    db_user = data.crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail='Email already registered')
    return data.crud.create_user(db=db, user=user)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=10)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.secret_key, algorithm=config.algorithm)
    return encoded_jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

async def get_current_user(token: str = Depends(oauth2_scheme), db: data.Session = Depends(get_db)) -> data.schemas.User:
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

@app.get('/users/me', response_model=data.schemas.User)
def read_users_me(current_user: data.schemas.User = Depends(get_current_user)):
    return current_user

@app.get('/users/me/api_key/', response_model=list[data.schemas.ModelAPIKeyBase])
def read_api_keys(db: data.Session = Depends(get_db), current_user: data.schemas.User = Depends(get_current_user)):
    return data.crud.get_user_api_providers(db=db, user_id=current_user.id)

@app.post('/users/me/api_key/', response_model=data.schemas.ModelAPIKeyBase)
def create_api_key(api_key: data.schemas.ModelAPIKeyCreate, db: data.Session = Depends(get_db), current_user: data.schemas.User = Depends(get_current_user)):
    return data.crud.create_api_key(db=db, api_key=api_key, user_id=current_user.id)

@app.delete('/users/me/api_key/{provider}')
def delete_api_key(provider: data.schemas.ModelAPI, db: data.Session = Depends(get_db), current_user: data.schemas.User = Depends(get_current_user)):
    data.crud.delete_api_key(db=db, user_id=current_user.id, provider=provider)
    return {'message': 'API key deleted', }

@app.put('/users/me/api_key/{provider}', response_model=data.schemas.ModelAPIKeyBase)
def update_api_key(api_key: data.schemas.ModelAPIKeyCreate, db: data.Session = Depends(get_db), current_user: data.schemas.User = Depends(get_current_user)):
    return data.crud.update_api_key(db=db, user_id=current_user.id, api_key=api_key)

@app.get('/chat/', response_model=list[data.schemas.ChatView])
def read_chats(skip: int = 0, limit: int = 100, db: data.Session = Depends(get_db), current_user: data.schemas.User = Depends(get_current_user)):
    return data.crud.get_chats(db, user_id=current_user.id, skip=skip, limit=limit)

@app.post('/chat/', response_model=data.schemas.Chat)
def create_chat(chat: data.schemas.ChatCreate, db: data.Session = Depends(get_db), current_user: data.schemas.User = Depends(get_current_user)):
    chat_db = data.crud.create_chat(db=db, chat=chat, user_id=current_user.id)
    system_msg = data.schemas.MessageCreate(role=data.schemas.Role.SYSTEM, content=chat.system_prompt)
    if system_user is None:
        raise HTTPException(status_code=500, detail='System user not found')
    data.crud.create_message(db=db, message=system_msg, user_id=cast(UUID4, system_user.id), chat_id=cast(UUID4, chat_db.id))
    return chat_db

async def get_chat(chat_id: UUID4, db: data.Session = Depends(get_db), current_user: data.schemas.User = Depends(get_current_user)) -> data.models.Chat:
    db_chat = data.crud.get_chat(db, chat_id=chat_id)
    if db_chat is None:
        raise HTTPException(status_code=404, detail='Chat not found')
    if db_chat.user_id != current_user.id:
        raise HTTPException(status_code=403, detail='Not authorized to access chat')
    return db_chat

@app.get('/chat/{chat_id}', response_model=data.schemas.Chat)
def read_chat(chat: data.models.Chat = Depends(get_chat)):
    return chat

@app.put('/chat/{chat_id}', response_model=data.schemas.Chat)
def update_chat(chat: data.schemas.ChatCreate, db_chat: data.models.Chat = Depends(get_chat), db: data.Session = Depends(get_db)):
    return data.crud.update_chat(db=db, chat_id=cast(UUID4, db_chat.id), chat=chat)

@app.delete('/chat/{chat_id}')
def delete_chat(db: data.Session = Depends(get_db), current_user: data.schemas.User = Depends(get_current_user), db_chat: data.models.Chat = Depends(get_chat)):
    db.delete(db_chat)
    db.commit()
    return {'message': 'Chat deleted', }

async def get_model(message: data.schemas.MessageCreate, chat: data.models.Chat = Depends(get_chat), db: data.Session = Depends(get_db), current_user: data.schemas.User = Depends(get_current_user)):
    if message.model is not None:
        model_type = get_chat_model(message.model)
    else:
        model_type = get_chat_model(cast(str, chat.default_model))
    key = None
    if model_type.requires_key:
        db_key = data.crud.get_api_key(db, current_user.id, model_type.api_provider)
        if db_key is None:
            raise HTTPException(status_code=400, detail='No API key registered for model for this user')
        key = db_key.key
    model = model_type(api_key=cast(str, key))
    message.model = None # user messages should not have a model; this was just for the model selection
    return model

@app.post('/chat/{chat_id}/', response_model=data.schemas.MessageView)
def send_message(chat_id: UUID4, message: data.schemas.MessageCreate, db: data.Session = Depends(get_db), chat: data.models.Chat = Depends(get_chat), model: ChatModel = Depends(get_model)):
    if assistant_user is None:
        raise HTTPException(status_code=500, detail='Assistant user not found')
    response_msg = model.chat(cast(list, chat.messages) + [message])
    db_msg = data.crud.create_message(db=db, message=message, user_id=uuid.UUID("c0aba09b-f57e-4998-bee6-86da8b796c5b"), chat_id=chat_id)
    try:
        return data.crud.create_message(db=db, message=cast(data.schemas.MessageCreate, response_msg), user_id=cast(UUID4, assistant_user.id), chat_id=chat_id)
    except Exception as e:
        data.crud.delete_message(db=db, message_id=cast(UUID4, db_msg.id))
        raise HTTPException(status_code=400, detail=str(e))
        
def handle_stream(msg_id: uuid.UUID, db: data.Session, model: str, stream: Generator[str, None, None]):
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
    
    data.crud.update_message(db=db, message_id=msg_id, message=data.schemas.MessageCreate(role=data.schemas.Role.ASSISTANT, content=message, model=model))

@app.post('/chat/{chat_id}/stream/', response_model=dict)
async def send_message_stream(chat_id: UUID4, message: data.schemas.MessageCreate, background_tasks: BackgroundTasks, db: data.Session = Depends(get_db), current_user: data.schemas.User = Depends(get_current_user), chat: data.models.Chat = Depends(get_chat), model: ChatModel = Depends(get_model)):
    if assistant_user is None:
        raise HTTPException(status_code=500, detail='Assistant user not found')

    if not model.supports_streaming:
        raise HTTPException(status_code=400, detail='Model does not support streaming')
    
    db_msg = data.crud.create_message(db=db, message=message, user_id=uuid.UUID("c0aba09b-f57e-4998-bee6-86da8b796c5b"), chat_id=chat_id)
    
    loading_msg = data.schemas.MessageCreate(role=data.schemas.Role.ASSISTANT, content='LOADING', model=model.api_name)
    loading_msg_db = data.crud.create_message(db=db, message=loading_msg, user_id=cast(UUID4, assistant_user.id), chat_id=chat_id)
    
    try:
        stream = model.chat_stream(cast(list, chat.messages) + [message])
        
        return StreamingResponse(handle_stream(cast(UUID4, loading_msg_db.id), db, model.api_name, stream))
    except Exception as e:
        data.crud.delete_message(db=db, message_id=cast(UUID4, loading_msg_db.id))
        data.crud.delete_message(db=db, message_id=cast(UUID4, db_msg.id))
        raise HTTPException(status_code=400, detail=str(e))

@app.get('/models/', response_model=list[ModelInfo])
def read_models(_: data.schemas.User = Depends(get_current_user)):
    return get_models()

@app.get('/')
async def root():
    return {'message': 'Hello, World!'}