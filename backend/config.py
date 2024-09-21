from dotenv import load_dotenv
import os

load_dotenv()

class Config():
    database_url: str = os.getenv('DATABASE_URL')
    system_email: str = os.getenv('SYSTEM_EMAIL')
    assistant_email: str = os.getenv('ASSISTANT_EMAIL')
    allowed_origins: list[str] = os.getenv('ALLOWED_ORIGINS')
    secret_key: str = os.getenv('SECRET_KEY')
    algorithm: str = os.getenv('ALGORITHM')
    access_token_expire_minutes: int = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))

config = Config()