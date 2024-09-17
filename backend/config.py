from dotenv import load_dotenv
import os

load_dotenv()

class Config():
    database_url: str = os.getenv('DATABASE_URL')
    system_email: str = os.getenv('SYSTEM_EMAIL')
    assistant_email: str = os.getenv('ASSISTANT_EMAIL')
    allowed_origins: list[str] = os.getenv('ALLOWED_ORIGINS')

config = Config()