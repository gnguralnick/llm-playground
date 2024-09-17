from fastapi import FastAPI, HTTPException, Depends
from .config import config
from . import data

app = FastAPI()

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

@app.get('/')
async def root():
    return {'message': 'Hello, World!'}