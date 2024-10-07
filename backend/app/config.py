from dotenv import load_dotenv
import os

load_dotenv()

vars = [
    'DATABASE_URL',
    'SYSTEM_EMAIL',
    'ASSISTANT_EMAIL',
    'ALLOWED_ORIGINS',
    'SECRET_KEY',
    'ALGORITHM',
    'ACCESS_TOKEN_EXPIRE_MINUTES'
]

for var in vars:
    if os.getenv(var) is None:
        raise ValueError(f'{var} is not set in the environment')

class Config():
    database_url: str = os.getenv('DATABASE_URL') # type: ignore
    system_email: str = os.getenv('SYSTEM_EMAIL') # type: ignore
    assistant_email: str = os.getenv('ASSISTANT_EMAIL') # type: ignore
    allowed_origins: list[str] = os.getenv('ALLOWED_ORIGINS') # type: ignore
    secret_key: str = os.getenv('SECRET_KEY') # type: ignore
    algorithm: str = os.getenv('ALGORITHM') # type: ignore
    access_token_expire_minutes: int = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES')) # type: ignore

config = Config()