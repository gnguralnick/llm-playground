#!/bin/sh

cd /app/app/data

alembic upgrade head

cd /app
fastapi run app/main.py --port 8000