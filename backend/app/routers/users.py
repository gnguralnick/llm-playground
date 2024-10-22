from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
import jwt
from pydantic import BaseModel
from app import schemas, data, dependencies
from app.config import config
import datetime

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

@router.post('/', response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: data.Session = Depends(dependencies.get_db)):
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

def create_access_token(data: dict, expires_delta: datetime.timedelta | None = None):
    """Create a JWT access token

    Args:
        data (dict): The data to encode in the token
        expires_delta (timedelta | None, optional): The expiration time for the token. Defaults to None.

    Returns:
        str: The encoded JWT access token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    else:
        expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=10)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.secret_key, algorithm=config.algorithm)
    return encoded_jwt


class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: data.Session = Depends(dependencies.get_db)
) -> Token:
    user = data.auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = datetime.timedelta(minutes=config.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@router.get('/me', response_model=schemas.User)
def read_users_me(current_user: schemas.User = Depends(dependencies.get_current_user)):
    return current_user

@router.get('/me/api_key/', response_model=list[schemas.APIKeyBase])
def read_api_keys(db: data.Session = Depends(dependencies.get_db), current_user: schemas.User = Depends(dependencies.get_current_user)):
    return data.crud.get_user_api_providers(db=db, user_id=current_user.id)

@router.post('/me/api_key/', response_model=schemas.APIKeyBase)
def create_api_key(api_key: schemas.APIKeyCreate, db: data.Session = Depends(dependencies.get_db), current_user: schemas.User = Depends(dependencies.get_current_user)):
    return data.crud.create_api_key(db=db, api_key=api_key, user_id=current_user.id)

@router.delete('/me/api_key/{provider}')
def delete_api_key(provider: schemas.ModelAPI, db: data.Session = Depends(dependencies.get_db), current_user: schemas.User = Depends(dependencies.get_current_user)):
    data.crud.delete_api_key(db=db, user_id=current_user.id, provider=provider)
    return {'message': 'API key deleted', }

@router.put('/me/api_key/{provider}', response_model=schemas.APIKeyBase)
def update_api_key(api_key: schemas.APIKeyCreate, db: data.Session = Depends(dependencies.get_db), current_user: schemas.User = Depends(dependencies.get_current_user)):
    return data.crud.update_api_key(db=db, user_id=current_user.id, api_key=api_key)