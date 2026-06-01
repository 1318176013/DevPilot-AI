from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RequirementCreate(BaseModel):
    project_id: UUID
    title: str
    raw_requirement: str
    priority: int = 0


class RequirementUpdate(BaseModel):
    title: str | None = None
    raw_requirement: str | None = None
    structured_requirement: dict | None = None
    status: str | None = None
    priority: int | None = None


class RequirementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    title: str
    raw_requirement: str
    structured_requirement: dict
    status: str
    priority: int
    created_at: datetime
    updated_at: datetime
