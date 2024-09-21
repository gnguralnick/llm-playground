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

from models import get_chat_model_info, get_models, ModelInfo

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
from jwt.exceptions import InvalidTokenError


system_user: data.models.User | None = None
assistant_user: data.models.User | None = None

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
        expire = datetime.now(timezone.utc) + timedelta(minutes=config.access_token_expire_minutes)
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
def delete_chat(chat_id: UUID4, db: data.Session = Depends(get_db), current_user: data.schemas.User = Depends(get_current_user)):
    db_chat = data.crud.get_chat(db, chat_id)
    if db_chat is None:
        raise HTTPException(status_code=404, detail='Chat not found')
    if db_chat.user_id != current_user.id:
        raise HTTPException(status_code=403, detail='Not authorized to delete chat')
    db.delete(db_chat)
    db.commit()
    return {'message': 'Chat deleted', }

@app.post('/chat/{chat_id}/', response_model=data.schemas.MessageView)
def send_message(chat_id: UUID4, message: data.schemas.MessageCreate, db: data.Session = Depends(get_db), current_user: data.schemas.User = Depends(get_current_user)):
    chat = data.crud.get_chat(db, chat_id)
    if chat is None:
        raise HTTPException(status_code=404, detail='Chat not found')
    if chat.user_id != current_user.id:
        raise HTTPException(status_code=403, detail='Not authorized to send message to chat')
    if assistant_user is None:
        raise HTTPException(status_code=500, detail='Assistant user not found')
    if message.model is not None:
        model_info = get_chat_model_info(message.model)
    else:
        model_info = get_chat_model_info(cast(str, chat.default_model))
    model = model_info.model()
    message.model = None # user messages should not have a model; this was just for the model selection
    response_msg = model.chat(cast(list, chat.messages) + [message])
    data.crud.create_message(db=db, message=message, user_id=uuid.UUID("c0aba09b-f57e-4998-bee6-86da8b796c5b"), chat_id=chat_id)
    return data.crud.create_message(db=db, message=cast(data.schemas.MessageCreate, response_msg), user_id=cast(UUID4, assistant_user.id), chat_id=chat_id)

# async def data_stream(chat_id: UUID4):
#     if assistant_user is None:
#         raise HTTPException(status_code=500, detail='Assistant user not found')
    
#     if chat_id not in stream_state.message_queues:
#         raise HTTPException(status_code=400, detail='Chat is not streaming a response')
#     queue = stream_state.message_queues[chat_id]
#     while True:
#         token = await queue.get()
#         if token is None:
#             break
#         yield token
        
def handle_stream(chat_id: UUID4, db: data.Session, model: str, stream: Generator[str, None, None], loading_msg_id: uuid.UUID):
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
    
    data.crud.update_message(db=db, message_id=loading_msg_id, message=data.schemas.MessageCreate(role=data.schemas.Role.ASSISTANT, content=message, model=model))

@app.post('/chat/{chat_id}/stream/', response_model=dict)
async def send_message_stream(chat_id: UUID4, message: data.schemas.MessageCreate, background_tasks: BackgroundTasks, db: data.Session = Depends(get_db), current_user: data.schemas.User = Depends(get_current_user)):
    chat = data.crud.get_chat(db, chat_id)
    if chat is None:
        raise HTTPException(status_code=404, detail='Chat not found')
    if chat.user_id != current_user.id:
        raise HTTPException(status_code=403, detail='Not authorized to send message to chat')
    if assistant_user is None:
        raise HTTPException(status_code=500, detail='Assistant user not found')
    if message.model is not None:
        model_info = get_chat_model_info(message.model)
    else:
        model_info = get_chat_model_info(cast(str, chat.default_model))
    model = model_info.model()
    message.model = None
    if not model_info.supports_streaming:
        raise HTTPException(status_code=400, detail='Model does not support streaming')
    
    data.crud.create_message(db=db, message=message, user_id=uuid.UUID("c0aba09b-f57e-4998-bee6-86da8b796c5b"), chat_id=chat_id)
    
    loading_msg = data.schemas.MessageCreate(role=data.schemas.Role.ASSISTANT, content='LOADING', model=model_info.api_name)
    loading_msg_db = data.crud.create_message(db=db, message=loading_msg, user_id=cast(UUID4, assistant_user.id), chat_id=chat_id)
    
    stream = model.chat_stream(cast(list, chat.messages) + [message])
    
    # background_tasks.add_task(handle_stream_completion, chat_id, db, model_info.api_name)
    
    return StreamingResponse(handle_stream(chat_id, db, model_info.api_name, stream, cast(UUID4, loading_msg_db.id)))

# @app.get('/chat/{chat_id}/stream/', response_class=StreamingResponse)
# def stream_messages(chat_id: UUID4):
#     if chat_id not in app.state.message_queues:
#         raise HTTPException(status_code=400, detail='Chat is not streaming a response')
#     return StreamingResponse(data_stream(chat_id))

@app.get('/models/', response_model=list[ModelInfo])
def read_models(current_user: data.schemas.User = Depends(get_current_user)):
    return get_models()

@app.get('/')
async def root():
    return {'message': 'Hello, World!'}