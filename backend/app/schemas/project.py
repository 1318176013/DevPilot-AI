from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ProjectCreate(BaseModel):
    name: str
    display_name: str | None = None
    local_path: str
    repo_url: str | None = None
    default_branch: str = "main"
    language: str | None = None
    framework: str | None = None
    description: str | None = None


class ProjectUpdate(BaseModel):
    display_name: str | None = None
    local_path: str | None = None
    repo_url: str | None = None
    default_branch: str | None = None
    language: str | None = None
    framework: str | None = None
    description: str | None = None
    status: str | None = None


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    display_name: str | None
    local_path: str
    repo_url: str | None
    default_branch: str
    language: str | None
    framework: str | None
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime
