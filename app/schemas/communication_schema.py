from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class AnnouncementCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    message: str = Field(min_length=1)
    target_audience: str
    created_by: UUID


class AnnouncementUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    message: str | None = Field(None, min_length=1)
    target_audience: str | None = None


class AnnouncementResponse(AnnouncementCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime


class NotificationCreate(BaseModel):
    user_id: UUID | None = None
    audience: str | None = None
    title: str = Field(min_length=1, max_length=255)
    message: str = Field(min_length=1)
    sent_on: datetime | None = None
    is_read: bool = False


class NotificationUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    message: str | None = Field(None, min_length=1)
    is_read: bool | None = None


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID
    title: str
    message: str
    sent_on: datetime
    is_read: bool
    created_at: datetime
    updated_at: datetime


class MessageCreate(BaseModel):
    sender_id: UUID
    receiver_id: UUID
    message: str = Field(min_length=1)
    sent_on: datetime | None = None


class MessageUpdate(BaseModel):
    message: str | None = Field(None, min_length=1)
    is_read: bool | None = None


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    sender_id: UUID
    receiver_id: UUID
    message: str
    sent_on: datetime
    is_read: bool
    created_at: datetime
    updated_at: datetime
