from dotenv import load_dotenv
import os

load_dotenv()

class Config():
    database_url: str = os.getenv('DATABASE_URL')

config = Config()