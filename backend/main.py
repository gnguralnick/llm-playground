from collections.abc import Generator
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from config import config
import data
from contextlib import asynccontextmanager
from pydantic import UUID4
import uuid
from typing import cast
from asyncio import Queue, create_task, sleep
from typing import AsyncIterable, AsyncIterator

from models import get_chat_model_info, get_models, ModelInfo


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

@app.get('/chat/', response_model=list[data.schemas.ChatView])
def read_chats(skip: int = 0, limit: int = 100, db: data.Session = Depends(get_db)):
    return data.crud.get_chats(db, user_id=uuid.UUID("c0aba09b-f57e-4998-bee6-86da8b796c5b"), skip=skip, limit=limit) # TODO: get user_id from token

@app.get('/chat/{chat_id}', response_model=data.schemas.Chat)
def read_chat(chat_id: UUID4, db: data.Session = Depends(get_db)):
    db_chat = data.crud.get_chat(db, chat_id=chat_id)
    if db_chat is None:
        raise HTTPException(status_code=404, detail='Chat not found')
    return db_chat

@app.post('/chat/', response_model=data.schemas.Chat)
def create_chat(chat: data.schemas.ChatCreate, db: data.Session = Depends(get_db)):
    chat_db = data.crud.create_chat(db=db, chat=chat, user_id=uuid.UUID("c0aba09b-f57e-4998-bee6-86da8b796c5b")) # TODO: get user_id from token
    system_msg = data.schemas.MessageCreate(role=data.schemas.Role.SYSTEM, content=chat.system_prompt)
    if system_user is None:
        raise HTTPException(status_code=500, detail='System user not found')
    data.crud.create_message(db=db, message=system_msg, user_id=cast(UUID4, system_user.id), chat_id=cast(UUID4, chat_db.id))
    return chat_db

@app.put('/chat/{chat_id}', response_model=data.schemas.Chat)
def update_chat(chat_id: UUID4, chat: data.schemas.ChatCreate, db: data.Session = Depends(get_db)):
    db_chat = data.crud.get_chat(db, chat_id)
    if db_chat is None:
        raise HTTPException(status_code=404, detail='Chat not found')
    return data.crud.update_chat(db=db, chat=chat, chat_id=chat_id)

@app.delete('/chat/{chat_id}')
def delete_chat(chat_id: UUID4, db: data.Session = Depends(get_db)):
    db_chat = data.crud.get_chat(db, chat_id)
    if db_chat is None:
        raise HTTPException(status_code=404, detail='Chat not found')
    db.delete(db_chat)
    db.commit()
    return {'message': 'Chat deleted', }

@app.post('/chat/{chat_id}/', response_model=data.schemas.MessageView)
def send_message(chat_id: UUID4, message: data.schemas.MessageCreate, db: data.Session = Depends(get_db)):
    chat = data.crud.get_chat(db, chat_id)
    if chat is None:
        raise HTTPException(status_code=404, detail='Chat not found')
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
async def send_message_stream(chat_id: UUID4, message: data.schemas.MessageCreate, background_tasks: BackgroundTasks, db: data.Session = Depends(get_db)):
    chat = data.crud.get_chat(db, chat_id)
    if chat is None:
        raise HTTPException(status_code=404, detail='Chat not found')
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
def read_models():
    return get_models()

@app.get('/')
async def root():
    return {'message': 'Hello, World!'}