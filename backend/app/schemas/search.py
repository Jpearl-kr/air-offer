from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class SearchCreateRequest(BaseModel):
    origin: str = Field(min_length=3, max_length=3)
    destination: str = Field(min_length=3, max_length=3)
    depart_date: date
    return_date: date | None = None
    adults: int = Field(default=1, ge=1)
    children: int = Field(default=0, ge=0)


class SearchCreateResponse(BaseModel):
    search_id: UUID


class SearchStatusResponse(BaseModel):
    status: str
