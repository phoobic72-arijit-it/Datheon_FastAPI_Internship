# Task 3: Database Persistence with SQLAlchemy and SQLite

An asynchronous FastAPI Users and Notes API with persistent storage.
One user can own many notes. This is a separate task folder; Tasks 1 and 2
do not need to be running.

## Screenshot requirements covered

- SQLAlchemy ORM replaces an in-memory list.
- SQLite stores records across server restarts.
- Relational User and Note models with a foreign key.
- Async engine, async_sessionmaker, and AsyncSession per request.
- database.py, models.py, and schemas.py are separate modules.
- Depends(get_db) supplies the database session.
- GET /notes performs an explicit JOIN and returns the owner's username.
- GET /users/{id} eagerly loads that user's notes.
- CRUD, validation, pagination, duplicate handling, and cascade deletion.

## Requirements and installation

Python 3.10 or newer. SQLite support is included with Python; no separate
database server, PostgreSQL installation, or database account is needed.
The aiosqlite package provides the asynchronous SQLite driver.

Extract this folder onto your Desktop, then run:

```bash
cd ~/Desktop/Task_3_Database_Persistence
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8003
```

Open [Swagger UI](http://127.0.0.1:8003/docs).
Stop with Control + C. Activate .venv again in each new Terminal window.
The first startup automatically creates the data folder and database tables.
No .env or setup_env.py is required.

## Files

| File | Purpose |
|---|---|
| main.py | Async routes, lifespan, CRUD, and joined queries |
| database.py | SQLite path, async engine, sessionmaker, session dependency |
| models.py | Relational SQLAlchemy User and Note tables |
| schemas.py | Pydantic input and response DTOs |
| requirements.txt | All required Python packages |
| INSTALL_MAC.md | Short Mac terminal instructions |
| .gitignore | Excludes local environments, caches, and database files |

## API endpoints

| Method | Route | Purpose |
|---|---|---|
| POST | /users | Create a user |
| GET | /users | List users with limit and offset |
| GET | /users/{user_id} | Read a user and their notes |
| PUT | /users/{user_id} | Replace username and full name |
| DELETE | /users/{user_id} | Delete a user and their notes |
| POST | /users/{user_id}/notes | Create a note for an existing user |
| GET | /notes | Join users and notes; filter by user_id or username |
| GET | /notes/{note_id} | Read one note with its owner's username |
| PUT | /notes/{note_id} | Replace a note's title and content |
| DELETE | /notes/{note_id} | Delete a note |

## Example workflow in Swagger

1. Create a user with POST /users:

```json
{"username": "arijit", "full_name": "Arijit Jana"}
```

2. Copy the returned id and use it in POST /users/{user_id}/notes:

```json
{"title": "Async SQLAlchemy", "content": "Each request gets its own async session."}
```

3. Open GET /notes to see note data and owner_username from a relational join.
4. Open GET /users/{user_id} to see the user with their nested notes.
5. Stop and restart the server with the same command. The saved records remain.
6. PUT updates a record; DELETE returns 204 with an empty response body.

Errors: 404 for unknown records, 409 for conflicting usernames/foreign keys,
and 422 for invalid input. Usernames are case-sensitive. Whitespace-only
names, titles, and content are rejected. Timestamps use SQLite's UTC clock.

## Persistence and scope

Data is stored in data/users_notes.db relative to this project, even if the
server is started from another working directory. Do not delete this database
if you want to keep your records. Deleting a user cascades to their notes.
The schema is created automatically for this task; schema migrations are not
included. These standalone CRUD endpoints do not implement Task 2's login.

## GitHub

Extract and upload the Task_3_Database_Persistence folder beside your other
task folders in Datheon_FastAPI_Internship. Upload the source files and docs;
exclude .venv, caches, and generated database files. Upload the extracted
folder rather than only the ZIP if you want GitHub to display the code.

## References

- [SQLAlchemy asyncio documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [FastAPI documentation](https://fastapi.tiangolo.com/)
