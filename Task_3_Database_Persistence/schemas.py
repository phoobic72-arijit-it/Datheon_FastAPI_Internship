"""Pydantic request validation and response DTOs."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    username: str = Field(
        min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9_]+$"
    )
    full_name: str = Field(min_length=1, max_length=100)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str
    created_at: datetime


class NoteInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1, max_length=10000)


class NoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    content: str
    created_at: datetime


class NoteWithOwner(NoteRead):
    owner_username: str


class UserWithNotes(UserRead):
    notes: list[NoteRead]
