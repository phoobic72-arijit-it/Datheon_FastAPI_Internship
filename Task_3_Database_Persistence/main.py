"""Persistent Users and Notes REST API with async SQLAlchemy and SQLite."""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Path, Query, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import Base, engine, get_db
from models import Note, User
from schemas import (
    NoteInput,
    NoteRead,
    NoteWithOwner,
    UserInput,
    UserRead,
    UserWithNotes,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Users and Notes Database API",
    description="Async SQLAlchemy sessions, persistent SQLite storage, and relational joins.",
    version="1.0.0",
    lifespan=lifespan,
)


async def find_user(db: AsyncSession, user_id: int):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


async def find_note(db: AsyncSession, note_id: int):
    note = await db.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


async def save_changes(db: AsyncSession):
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Database conflict: username already exists or related user changed",
        ) from None


@app.get("/", tags=["Information"])
async def home():
    return {"message": "Persistent Users and Notes API", "docs": "/docs"}


@app.post("/users", response_model=UserRead, status_code=201, tags=["Users"])
async def create_user(user_input: UserInput, db: AsyncSession = Depends(get_db)):
    user = User(**user_input.model_dump())
    db.add(user)
    await save_changes(db)
    await db.refresh(user)
    return user


@app.get("/users", response_model=list[UserRead], tags=["Users"])
async def list_users(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    result = await db.scalars(select(User).order_by(User.id).limit(limit).offset(offset))
    return result.all()


@app.get("/users/{user_id}", response_model=UserWithNotes, tags=["Users"])
async def get_user(
    user_id: int = Path(ge=1), db: AsyncSession = Depends(get_db)
):
    # Eager loading avoids implicit asynchronous database reads during serialization.
    query = select(User).options(selectinload(User.notes)).where(User.id == user_id)
    user = await db.scalar(query)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.put("/users/{user_id}", response_model=UserRead, tags=["Users"])
async def update_user(
    user_input: UserInput,
    user_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),
):
    user = await find_user(db, user_id)
    user.username = user_input.username
    user.full_name = user_input.full_name
    await save_changes(db)
    await db.refresh(user)
    return user


@app.delete("/users/{user_id}", status_code=204, tags=["Users"])
async def delete_user(
    user_id: int = Path(ge=1), db: AsyncSession = Depends(get_db)
):
    user = await find_user(db, user_id)
    await db.delete(user)
    await save_changes(db)
    return Response(status_code=204)


@app.post(
    "/users/{user_id}/notes", response_model=NoteRead, status_code=201, tags=["Notes"]
)
async def create_note(
    note_input: NoteInput,
    user_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),
):
    await find_user(db, user_id)
    note = Note(user_id=user_id, **note_input.model_dump())
    db.add(note)
    await save_changes(db)
    await db.refresh(note)
    return note


@app.get("/notes", response_model=list[NoteWithOwner], tags=["Notes"])
async def list_notes(
    user_id: int | None = Query(default=None, ge=1),
    username: str | None = Query(default=None, min_length=3, max_length=30),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    # This is an actual SQL JOIN between the notes and users tables.
    query = select(Note, User.username).join(User, Note.user_id == User.id)
    if user_id is not None:
        query = query.where(Note.user_id == user_id)
    if username is not None:
        query = query.where(User.username == username)
    result = await db.execute(query.order_by(Note.id).limit(limit).offset(offset))
    return [
        NoteWithOwner(
            **NoteRead.model_validate(note).model_dump(), owner_username=owner_username
        )
        for note, owner_username in result.all()
    ]


@app.get("/notes/{note_id}", response_model=NoteWithOwner, tags=["Notes"])
async def get_note(
    note_id: int = Path(ge=1), db: AsyncSession = Depends(get_db)
):
    query = (
        select(Note, User.username)
        .join(User, Note.user_id == User.id)
        .where(Note.id == note_id)
    )
    row = (await db.execute(query)).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Note not found")
    note, owner_username = row
    return NoteWithOwner(
        **NoteRead.model_validate(note).model_dump(), owner_username=owner_username
    )


@app.put("/notes/{note_id}", response_model=NoteRead, tags=["Notes"])
async def update_note(
    note_input: NoteInput,
    note_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),
):
    note = await find_note(db, note_id)
    note.title = note_input.title
    note.content = note_input.content
    await save_changes(db)
    await db.refresh(note)
    return note


@app.delete("/notes/{note_id}", status_code=204, tags=["Notes"])
async def delete_note(
    note_id: int = Path(ge=1), db: AsyncSession = Depends(get_db)
):
    note = await find_note(db, note_id)
    await db.delete(note)
    await save_changes(db)
    return Response(status_code=204)
