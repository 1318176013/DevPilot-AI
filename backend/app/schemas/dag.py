from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DagNodeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    requirement_id: UUID
    node_type: str
    label: str
    description: str | None
    config: dict
    model_policy: dict
    position_x: float
    position_y: float
    status: str
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime


class DagEdgeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    requirement_id: UUID
    source_node_id: UUID
    target_node_id: UUID
    edge_type: str
    condition_expr: str | None


class DagRead(BaseModel):
    requirement_id: UUID
    nodes: list[DagNodeRead]
    edges: list[DagEdgeRead]


class DagGenerateResponse(DagRead):
    generated: bool


class DagNodeStatusUpdate(BaseModel):
    status: str
