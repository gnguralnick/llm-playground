import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import UUID4
from app import data, schemas, dependencies, chat_models
from app.util import Role, ModelConfig
from typing import Generator, cast

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    responses={404: {"description": "Not found"}},
)

@router.get('/', response_model=list[schemas.ChatView])
def read_chats(skip: int = 0, limit: int = 100, db: data.Session = Depends(dependencies.get_db), current_user: schemas.User = Depends(dependencies.get_current_user)):
    return data.crud.get_chats(db, user_id=current_user.id, skip=skip, limit=limit)

@router.post('/', response_model=schemas.ChatView)
def create_chat(chat: schemas.ChatCreate, db: data.Session = Depends(dependencies.get_db), current_user: schemas.User = Depends(dependencies.get_current_user), system_user = Depends(dependencies.get_system_user)):
    chat_db = data.crud.create_chat(db=db, chat=chat, user_id=current_user.id)
    system_msg = schemas.MessageBuilder(role=Role.SYSTEM).add_text(chat.system_prompt).build()
    data.crud.create_message(db=db, message=system_msg, user_id=cast(UUID4, system_user.id), chat_id=cast(UUID4, chat_db.id))
    return chat_db

@router.get('/{chat_id}', response_model=schemas.ChatFull)
def read_chat(chat: data.models.Chat = Depends(dependencies.get_chat)):
    return chat

@router.get('/{chat_id}/images/{image_path}', response_class=FileResponse, dependencies=[Depends(dependencies.get_chat)])
def read_image(chat_id: UUID4, image_path: str):
    return f'images/{chat_id}/{image_path}'

@router.put('/{chat_id}', response_model=schemas.ChatView)
def update_chat(chat: schemas.ChatCreate, db_chat: data.models.Chat = Depends(dependencies.get_chat), db: data.Session = Depends(dependencies.get_db)):
    return data.crud.update_chat(db=db, chat_id=cast(UUID4, db_chat.id), chat=chat)

@router.delete('/{chat_id}')
def delete_chat(db: data.Session = Depends(dependencies.get_db), db_chat: data.models.Chat = Depends(dependencies.get_chat)):
    db.delete(db_chat)
    db.commit()
    return {'message': 'Chat deleted', }

def autogen_chat_title(db: data.Session, chat_id: UUID4, messages: list[schemas.Message], model: chat_models.chat_model.ChatModel) -> schemas.chat.Chat:
    db_chat = data.crud.get_chat(db, chat_id)
    if db_chat is None:
        raise HTTPException(status_code=404, detail='Chat not found')
    chat_create = schemas.chat.ChatCreate.model_validate(db_chat, from_attributes=True)
    prompt = "Below is a conversation between a user and an AI assistant. Generate a title for this chat. The title should be short and memorable. Respond with the title only. Do not include quotation marks."
    for m in messages:
        if m.role == Role.USER:
            prompt += f"\nUser: {m.contents[0].content}"
        elif m.role == Role.ASSISTANT:
            prompt += f"\nAssistant: {m.contents[0].content}"
            
    prompt += "\nTitle:"
    prompt_message = schemas.MessageBuilder(role=Role.USER).add_text(prompt).build()
    title = model.chat([prompt_message]).contents[0].content
    chat_create.title = title
    
    db_chat = data.crud.update_chat(db=db, chat_id=cast(UUID4, db_chat.id), chat=chat_create)
    
    return schemas.chat.Chat.model_validate(db_chat, from_attributes=True)

@router.post('/{chat_id}/', response_model=schemas.MessageView)
def send_message(chat_id: UUID4, message: schemas.Message = Depends(dependencies.save_images), db: data.Session = Depends(dependencies.get_db), db_chat: data.models.Chat = Depends(dependencies.get_chat), model_with_config: tuple[chat_models.chat_model.ChatModel, ModelConfig] = Depends(dependencies.get_model), assistant_user = Depends(dependencies.get_assistant_user)):
    chat: schemas.ChatFull = schemas.ChatFull.model_validate(db_chat, from_attributes=True)
    
    model, _ = model_with_config

    response_msg = model.chat(chat.messages + [message])
    db_msg = data.crud.create_message(db=db, message=message, user_id=uuid.UUID("c0aba09b-f57e-4998-bee6-86da8b796c5b"), chat_id=chat_id)
    try:
        msg = data.crud.create_message(db=db, message=response_msg, user_id=cast(UUID4, assistant_user.id), chat_id=chat_id)
        if chat.title == 'New Chat':
            autogen_chat_title(db, chat_id, chat.messages + [message, response_msg], model)
        return msg
    except Exception as e:
        data.crud.delete_message(db=db, message_id=cast(UUID4, db_msg.id))
        raise HTTPException(status_code=400, detail=str(e))
        
def handle_stream(msg_id: uuid.UUID, db: data.Session, model_name: str, stream: Generator[str, None, None], chat: schemas.ChatFull, model: chat_models.chat_model.ChatModel):
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
    
    new_message = schemas.MessageBuilder(role=schemas.Role.ASSISTANT, model=model_name).add_text(message).build()
    data.crud.update_message(db=db, message_id=msg_id, message=new_message)
    if chat.title == 'New Chat':
        autogen_chat_title(db, chat.id, chat.messages + [new_message], model)

@router.post('/{chat_id}/stream/', response_model=dict)
async def send_message_stream(chat_id: UUID4, message = Depends(dependencies.save_images), db: data.Session = Depends(dependencies.get_db), db_chat: data.models.Chat = Depends(dependencies.get_chat), model_with_config: tuple[chat_models.chat_model.ChatModel, ModelConfig] = Depends(dependencies.get_model), assistant_user = Depends(dependencies.get_assistant_user)):
    chat: schemas.ChatFull = schemas.ChatFull.model_validate(db_chat, from_attributes=True)
    model, config = model_with_config

    if not isinstance(model, chat_models.StreamingChatModel):
        raise HTTPException(status_code=400, detail='Model does not support streaming')
    
    db_msg = data.crud.create_message(db=db, message=message, user_id=uuid.UUID("c0aba09b-f57e-4998-bee6-86da8b796c5b"), chat_id=chat_id)
    
    # create a temporary loading message to show the user that the model is processing
    loading_msg = schemas.MessageBuilder(role=schemas.Role.ASSISTANT, model=model.api_name, config=config).add_text('LOADING').build()
    loading_msg_db = data.crud.create_message(db=db, message=loading_msg, user_id=cast(UUID4, assistant_user.id), chat_id=chat_id)
    
    try:
        stream = model.chat_stream(chat.messages + [message])
        
        return StreamingResponse(handle_stream(cast(UUID4, loading_msg_db.id), db, model.api_name, stream, chat, model))
    except Exception as e:
        # if an error occurs, delete the loading message and the message that was sent to the model
        data.crud.delete_message(db=db, message_id=cast(UUID4, loading_msg_db.id))
        data.crud.delete_message(db=db, message_id=cast(UUID4, db_msg.id))
        raise HTTPException(status_code=400, detail=str(e))