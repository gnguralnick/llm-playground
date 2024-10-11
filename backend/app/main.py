from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import config
from app.routers import chat, models, users

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.allowed_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(users.router)
app.include_router(chat.router)
app.include_router(models.router)


@app.get('/')
async def root():
    return {'message': 'Hello, World!'}