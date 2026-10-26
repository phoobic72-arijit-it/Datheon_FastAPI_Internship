"""Request and response models for webhook jobs."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WebhookInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    event: str = Field(
        min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9_.-]+$"
    )
    message: str = Field(min_length=1, max_length=1000)


class JobRead(BaseModel):
    id: UUID
    status: Literal["queued", "processing", "succeeded", "failed"]
    attempts: int
    created_at: datetime
    updated_at: datetime
    response_status: int | None = None
    error: str | None = None


class DeliveryRead(BaseModel):
    job_id: UUID
    event: str
    message: str
    received_at: datetime
