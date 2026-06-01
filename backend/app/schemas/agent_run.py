from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.tooling import ToolCallLogRead


class AgentRunCreate(BaseModel):
    requirement_id: UUID
    dag_node_id: UUID | None = None


class AgentActionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    run_id: UUID
    sequence: int
    action_type: str
    message: str
    payload: dict
    status: str
    created_at: datetime


class AgentRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    requirement_id: UUID
    dag_node_id: UUID | None
    backend: str
    status: str
    summary: str | None
    result: dict
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime


class AgentRunDetail(AgentRunRead):
    actions: list[AgentActionRead] = []
    tool_calls: list[ToolCallLogRead] = []
