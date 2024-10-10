# LLM Playground
### Created by Gabriel Guralnick

This repo contains the frontend and backend for a web application to interact with large language models (LLMs). I created it initially to refresh my web development skills and reacquaint myself with interacting with LLM APIs after spending a while without working in this area. Now that the basic chat app is implemented, I plan to add more complex and interesting use-cases such as agentic functionality and integration of other models to enable multimodal inputs and responses.

The frontend is written in React with TypeScript.
The backend is a FastAPI application, tested with a PostgreSQL database using SQLAlchemy as an ORM layer.

NOTE: You will have to provide API keys for whichever model providers you'd like to use. This can be done on the site -- once you've made an account, you should be automatically redirected to the user edit page with fields to add API keys.

## Installation Instructions

This project uses Docker to make production installation simple. First, make sure you have docker installed, so the `docker-compose` command works in your shell.

Then, simply run
```bash
docker-compose up
```

To spin up the database, frontend, and backend containers.

The site should now be accessible at [http://localhost:3000](http://localhost:3000).

## Development Installation Instructions

The frontend and backend each need a `.env` file.
```bash
mv frontend/.env.example frontend/.env
mv backend/.env.example backend/.env
```
Fill in the fields in each file appropriately.

### Frontend

```bash
cd frontend
pnpm i
pnpm dev
```

### Backend
First, install package requrirements.
```bash
cd backend
python3 -m venv venv # create a virtual environment
source venv/bin/activate
pip install -r requirements.txt
```
This project expects to connect to a database. I used PostgreSQL, but any SQL DBMS should work. The main requirement is support of the UUID type. If you're not using PostgreSQL, you will need to update the `data/models.py` file and change the import of the UUID type to use your particular dialect. You may also encounter issues with applying the migrations with alembic.

If you don't have PostgreSQL installed, you can follow [this guide](https://www.prisma.io/dataguide/postgresql/setting-up-a-local-postgresql-database#setting-up-postgresql-on-macos). Once it is installed and you've created a database to use for this application, fill in the `.env` file with the line
```bash
DATABASE_URL="postgresql://postgres:[port]@localhost:[port]/[database-name]"
```

Then run the database migrations to set up the table
```bash
cd data
alembic upgrade head
```

At this point, the application is set up.
```bash
fastapi dev
```