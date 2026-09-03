from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class HealthValue(BaseModel):
    sleep_hours: float = Field(ge=0, le=24, examples=[7.5])
    exercise_minutes: int = Field(ge=0, le=1440, examples=[45])


class HealthRecordIn(BaseModel):
    date: date
    value: HealthValue
    memo: str = Field(default="", max_length=300)

    @field_validator("date")
    @classmethod
    def reject_future_date(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("미래 날짜는 기록할 수 없습니다.")
        return value


class HealthRecord(HealthRecordIn):
    id: str


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=5000)


class ConversationIn(BaseModel):
    title: str = Field(default="건강 상담", min_length=1, max_length=80)
    messages: list[Message] = Field(min_length=1, max_length=50)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    conversation_id: str | None = None

