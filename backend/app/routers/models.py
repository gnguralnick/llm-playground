from fastapi import APIRouter, Depends
from app import chat_models, data, schemas, dependencies
from typing import cast
from pydantic import UUID4

router = APIRouter(
    prefix="/models",
    tags=["models"],
    responses={404: {"description": "Not found"}},
)

@router.get('/', response_model=list[chat_models.ModelInfo])
def read_models(db: data.Session = Depends(dependencies.get_db), user: schemas.User = Depends(dependencies.get_current_user)):
    models = chat_models.get_models()
    for model in models:
        if model.requires_key:
            has_key = data.crud.get_api_key(db, cast(UUID4, user.id), model.api_provider) is not None
            model.user_has_key = has_key
    return models

@router.get('/{model_name}', response_model=chat_models.ModelInfo)
def read_model(model_name: str, db: data.Session = Depends(dependencies.get_db), user: schemas.User = Depends(dependencies.get_current_user)):
    model_info = chat_models.get_chat_model_info(model_name)
    if model_info.requires_key:
        has_key = data.crud.get_api_key(db, cast(UUID4, user.id), model_info.api_provider) is not None
        model_info.user_has_key = has_key
    return model_info