import os
import uuid
from fastapi import Depends, Form, HTTPException, UploadFile, WebSocketException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from pydantic import UUID4
from app import data, schemas, chat_models, tools
from app.config import config
from typing import cast

def get_db():
    db = data.SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/users/token')
        
async def get_current_user(token: str = Depends(oauth2_scheme), db: data.Session = Depends(get_db), req_type: str = 'http') -> schemas.user.User:
    """Get the current user from the JWT token

    Args:
        token (str, optional): The JWT token. Defaults to Depends(oauth2_scheme).

    Raises:
        credentials_exception: If the token is invalid or the user does not exist

    Returns:
        schemas.User: The user associated with the token
    """
    if req_type == 'http':
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif req_type == 'websocket':
        credentials_exception = WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason='Could not validate credentials')
    else:
        raise ValueError('Invalid request type')
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

async def get_chat(chat_id: UUID4, db: data.Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user), req_type: str = 'http') -> data.models.Chat:
    db_chat = data.crud.get_chat(db, chat_id=chat_id)
    if db_chat is None:
        raise HTTPException(status_code=404, detail='Chat not found') if req_type == 'http' else WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason='Chat not found')
    if db_chat.user_id != current_user.id:
        raise HTTPException(status_code=403, detail='Not authorized to access chat') if req_type == 'http' else WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason='Not authorized to access chat')
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

async def get_tools(db: data.Session = Depends(get_db), current_user = Depends(get_current_user)) -> dict[str, schemas.ToolConfig]:
    res = {}
    for tool_name in tools.get_tools():
        tool = tools.get_tools()[tool_name]
        if not tool.requires_api_key:
            res[tool_name] = tool
        elif tool.api_provider is None:
            raise ValueError(f'Tool {tool_name} requires an API key but no provider is specified')
        else:
            api_key = data.crud.get_api_key(db, current_user.id, tool.api_provider)
            if api_key is not None:
                tool.set_api_key(cast(str, api_key.key))
                res[tool_name] = tool
    return res

def save_files(chat_id: UUID4, files: list[UploadFile] | None = None, message: schemas.Message = Depends(get_message)) -> schemas.Message:
    """Save files to disk and update message content to include file paths

    Args:
        chat_id (UUID4): The chat ID to which the message belongs / will belong
        files (list[UploadFile] | None, optional): The list of files uploaded with the message. Defaults to None, in which case the function should have no effect.
        message (schemas.MessageCreate, optional): The message to process. Defaults to Depends(get_message).

    Raises:
        HTTPException: If the message contains an file content but no file is provided whose filename matches the content

    Returns:
        schemas.MessageCreate: The message with updated content, where file content is replaced with local file paths
    """
    for c in message.contents:
        if isinstance(c, schemas.ImageMessageContent):
            if files is None:
                raise HTTPException(status_code=400, detail='File content requires a file')
            file = next((f for f in files if f.filename == c.content), None)
            if file is None:
                raise HTTPException(status_code=400, detail='File content file not found')
            if file.content_type is None:
                raise HTTPException(status_code=400, detail='File content file type not provided')
            file_data = file.file.read()
            # save image to disk and set content to file path
            if not os.path.exists(f'uploads/{chat_id}'):
                os.makedirs(f'uploads/{chat_id}')
            with open(f'uploads/{chat_id}/{c.content}', 'wb') as f:
                f.write(file_data)
            c.content = f'uploads/{chat_id}/{c.content}'
            c.image_type = file.content_type
    return message

def get_system_user(db: data.Session = Depends(get_db)) -> data.models.User:
    """Get the system user from the database

    Args:
        db (data.Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        data.models.User: The system user
    """
    
    system_user = data.crud.get_user_by_email(db, email=config.system_email)
    if system_user is None:
        system_user = data.crud.create_user(db, user=schemas.UserCreate(email=config.system_email, password='password'))
    return system_user

def get_assistant_user(db: data.Session = Depends(get_db)) -> schemas.User:
    """Get the assistant user from the database

    Args:
        db (data.Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        data.models.User: The assistant user
    """
    assistant_user = data.crud.get_user_by_email(db, email=config.assistant_email)
    if assistant_user is None:
        assistant_user = data.crud.create_user(db, user=schemas.UserCreate(email=config.assistant_email, password='password'))
    return schemas.User.model_validate(assistant_user, from_attributes=True)