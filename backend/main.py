from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from config import config
import data
from contextlib import asynccontextmanager
from pydantic import UUID4

from models import get_chat_model

system_user = None
assistant_user = None

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
    return data.crud.get_chats(db, user_id="c0aba09b-f57e-4998-bee6-86da8b796c5b", skip=skip, limit=limit) # TODO: get user_id from token

@app.get('/chat/{chat_id}', response_model=data.schemas.Chat)
def read_chat(chat_id: UUID4, db: data.Session = Depends(get_db)):
    db_chat = data.crud.get_chat(db, chat_id=chat_id)
    if db_chat is None:
        raise HTTPException(status_code=404, detail='Chat not found')
    return db_chat

@app.post('/chat/', response_model=data.schemas.Chat)
def create_chat(chat: data.schemas.ChatCreate, db: data.Session = Depends(get_db)):
    chat_db = data.crud.create_chat(db=db, chat=chat, user_id="c0aba09b-f57e-4998-bee6-86da8b796c5b") # TODO: get user_id from token
    system_msg = data.schemas.MessageCreate(role=data.schemas.Role.SYSTEM, content=chat.system_prompt)
    data.crud.create_message(db=db, message=system_msg, user_id=system_user.id, chat_id=chat_db.id)
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
    model = get_chat_model('gpt-4o-mini') # TODO: get model from chat
    response_msg = model.chat(chat.messages + [message])
    data.crud.create_message(db=db, message=message, user_id="c0aba09b-f57e-4998-bee6-86da8b796c5b", chat_id=chat_id)
    return data.crud.create_message(db=db, message=response_msg, user_id=assistant_user.id, chat_id=chat_id)

@app.put('/chat/{chat_id}/', response_model=data.schemas.MessageView)
def update_message(chat_id: UUID4, message_id: UUID4, message: data.schemas.MessageCreate, db: data.Session = Depends(get_db)):
    db_message = data.crud.get_message(db, message_id)
    if db_message is None:
        raise HTTPException(status_code=404, detail='Message not found')
    if db_message.chat_id != chat_id:
        raise HTTPException(status_code=400, detail='Message does not belong to chat')
    return data.crud.update_message(db=db, message=message, message_id=message_id)

@app.get('/')
async def root():
    return {'message': 'Hello, World!'}