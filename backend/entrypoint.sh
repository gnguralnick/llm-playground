#!/bin/sh

cd /app

alembic upgrade head

fastapi run app/main.py --port 8000