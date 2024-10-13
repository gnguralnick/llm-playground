from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json
from pydantic import BaseModel

import os
import sys

here = os.path.dirname(__file__)
sys.path.append(os.path.join(here, '..'))

from app.config import config

SQLALCHEMY_DATABASE_URL = config.database_url

def json_serialize(obj):
    if isinstance(obj, BaseModel):
        return obj.model_dump_json()
    return json.dumps(obj)

engine = create_engine(SQLALCHEMY_DATABASE_URL, json_serializer=json_serialize)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()