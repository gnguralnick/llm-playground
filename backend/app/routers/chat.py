import os
import shutil
import uuid
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import UUID4
from app import data, schemas, dependencies, chat_models
from app.schemas.model_config import ModelConfigWithTools
from app.util import Role
from typing import cast
from app.chat_stream import ChatStreamManager
import asyncio

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
def update_chat(chat: schemas.ChatCreate, db_chat: data.models.Chat = Depends(dependencies.get_chat), db: data.Session = Depends(dependencies.get_db), tools = Depends(dependencies.get_tools)):
    old_chat = schemas.ChatFull.model_validate(db_chat, from_attributes=True)
    if chat.default_model != old_chat.default_model:
        # if default model is changed, completely overwrite chat config
        default_model_config = chat_models.get_chat_model(chat.default_model).config_type()
        if chat.config is None:
            chat.config = default_model_config
        return data.crud.update_chat(db=db, chat_id=cast(UUID4, db_chat.id), chat=chat)
    
    if isinstance(old_chat.config, ModelConfigWithTools) and isinstance(chat.config, ModelConfigWithTools) and [tool.name for tool in chat.config.tools] != chat.tools:
        kept_tools = []
        for tool in old_chat.config.tools:
            if tool.name in chat.tools:
                kept_tools.append(tool)
        chat.config.tools = kept_tools
        for tool_name in chat.tools:
            if tool_name not in tools:
                raise HTTPException(status_code=400, detail=f'Tool {tool_name} not found')
            if not hasattr(chat.config, 'tools'):
                raise HTTPException(status_code=400, detail='Chat model does not support tools')
            chat.config.tools.append(tools[tool_name])
        assert [tool.name for tool in chat.config.tools] == chat.tools
    return data.crud.update_chat(db=db, chat_id=cast(UUID4, db_chat.id), chat=chat)

@router.delete('/{chat_id}')
def delete_chat(db: data.Session = Depends(dependencies.get_db), db_chat: data.models.Chat = Depends(dependencies.get_chat)):
    if os.path.exists(f'images/{db_chat.id}'):
        shutil.rmtree(f'images/{db_chat.id}')
    db.delete(db_chat)
    db.commit()
    return {'message': 'Chat deleted', }

def autogen_chat_title(db: data.Session, chat_id: UUID4, messages: list[schemas.Message], model: chat_models.chat_model.ChatModel) -> schemas.chat.Chat:
    db_chat = data.crud.get_chat(db, chat_id)
    if db_chat is None:
        raise HTTPException(status_code=404, detail='Chat not found')
    chat_create = schemas.chat.ChatCreate.model_validate(db_chat, from_attributes=True)
    prompt = "Below is a conversation between a user and an AI assistant. Generate a title for this chat. The title should be short and memorable. Respond with the title only. Do not include quotation marks. Do not use any tools."
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

def handle_tool_calls(message: schemas.Message, user_id: UUID4, chat_id: UUID4, db: data.Session, tools: dict[str, schemas.ToolConfig]) -> data.models.Message:
    print('handling tool calls')
    tool_result_message = schemas.MessageBuilder(role=Role.TOOL)
    for content in message.contents:
        if isinstance(content, schemas.ToolCallMessageContent):
            tool_call = content.content
            print('tool call', tool_call)
            tool = tools.get(tool_call.name)
            if tool is None:
                raise HTTPException(status_code=400, detail=f'Tool {tool_call.name} not found')
            tool_result = tool(**tool_call.args)
            print('tool result', tool_result)
            tool_result_message.add_tool_result(tool_result, tool_call_id=content.tool_call_id)
    
    db_msg = data.crud.create_message(db=db, message=tool_result_message.build(), user_id=user_id, chat_id=chat_id)
    
    return db_msg

@router.post('/{chat_id}/', response_model=schemas.MessageView)
def send_message(chat_id: UUID4, current_user: schemas.User = Depends(dependencies.get_current_user), message: schemas.Message = Depends(dependencies.save_images), db: data.Session = Depends(dependencies.get_db), db_chat: data.models.Chat = Depends(dependencies.get_chat), model_with_config: tuple[chat_models.chat_model.ChatModel, schemas.ModelConfig] = Depends(dependencies.get_model), assistant_user = Depends(dependencies.get_assistant_user), tools = Depends(dependencies.get_tools)):
    chat: schemas.ChatFull = schemas.ChatFull.model_validate(db_chat, from_attributes=True)
    
    model, _ = model_with_config
    
    db_msgs = []
    
    try:
        db_msg = data.crud.create_message(db=db, message=message, user_id=current_user.id, chat_id=chat_id)
        db_msgs.append(db_msg)
        messages = chat.messages + [message]
        while True:
            response_msg = model.chat(messages)
            messages.append(response_msg)
            msg = data.crud.create_message(db=db, message=response_msg, user_id=cast(UUID4, assistant_user.id), chat_id=chat_id)
            db_msgs.append(msg)
            if not response_msg.has_tool_calls():
                break
            db_msg = handle_tool_calls(response_msg, current_user.id, chat_id, db, tools)
            db_msgs.append(db_msg)
            tool_msg = schemas.Message.model_validate(db_msg, from_attributes=True)
            messages.append(tool_msg)
        if chat.title == 'New Chat':
            autogen_chat_title(db, chat_id, chat.messages + [message, response_msg], model)
        return msg
    except Exception as e:
        # rollback messages
        for db_msg in db_msgs:
            data.crud.delete_message(db=db, message_id=cast(UUID4, db_msg.id))
        raise HTTPException(status_code=400, detail=str(e))
     
stream_manager = ChatStreamManager()
   
def handle_stream(chat_id: UUID4, message: schemas.Message, chat: schemas.ChatFull, model: chat_models.chat_model.StreamingChatModel, user_msg_id: UUID4):
    """Process a stream of tokens from a chat model and update the message in the database when the stream ends

    Args:


    Yields:
        str: The tokens from the stream
    """
    
    stream_manager.reset_chat(chat_id)
    
    stream = model.chat_stream(chat.messages + [message])

    while True:
        try:
            token = next(stream)
        except StopIteration:
            break
        if token is None:
            break
        asyncio.run(stream_manager.send_message(chat_id, token))
        
    asyncio.run(stream_manager.end_message(chat_id))
    message_txt = stream_manager.get_full_message(chat_id)
    new_message = schemas.MessageBuilder(role=Role.ASSISTANT, model=model.api_name).add_text(message_txt).build()
    db = next(dependencies.get_db())
    try:
        assistant_user = dependencies.get_assistant_user(db=db)
        data.crud.create_message(db=db, message=new_message, user_id=cast(UUID4, assistant_user.id), chat_id=chat_id)
        if chat.title == 'New Chat':
            autogen_chat_title(db, chat_id, chat.messages + [new_message], model)
    except Exception as e:
        data.crud.delete_message(db=db, message_id=user_msg_id)
        stream_manager.reset_chat(chat_id)
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        print('finished streaming, closing db')
        db.close()
        return

@router.post('/{chat_id}/stream/', response_model=dict)
async def send_message_stream(background_tasks: BackgroundTasks, chat_id: UUID4, message = Depends(dependencies.save_images), db: data.Session = Depends(dependencies.get_db), db_chat: data.models.Chat = Depends(dependencies.get_chat), model_with_config: tuple[chat_models.chat_model.ChatModel, schemas.ModelConfig] = Depends(dependencies.get_model)):
    chat: schemas.ChatFull = schemas.ChatFull.model_validate(db_chat, from_attributes=True)
    model, _ = model_with_config

    if not isinstance(model, chat_models.StreamingChatModel):
        raise HTTPException(status_code=400, detail='Model does not support streaming')
    
    db_msg = data.crud.create_message(db=db, message=message, user_id=uuid.UUID("c0aba09b-f57e-4998-bee6-86da8b796c5b"), chat_id=chat_id)
    
    background_tasks.add_task(handle_stream, chat_id, message, chat, model, cast(UUID4, db_msg.id))
    
    return {'message': 'Stream started'}
    
@router.websocket('/{chat_id}/stream')
async def consume_chat_stream(websocket: WebSocket, chat_id: UUID4, token: str = Query()):
    db = next(dependencies.get_db())
    current_user = await dependencies.get_current_user(token=token, db=db, req_type='websocket')
    await dependencies.get_chat(chat_id=chat_id, db=db, current_user=current_user)
    db.close()
    await websocket.accept()
    try:
        await websocket.send_text(stream_manager.get_full_message(chat_id))
        while True:
            if stream_manager.chat_has_message(chat_id):
                msg = await stream_manager.consume_message(chat_id)
                await websocket.send_text(msg)
                if msg == 'END MESSAGE':
                    stream_manager.reset_chat(chat_id)
            else:
                await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        pass