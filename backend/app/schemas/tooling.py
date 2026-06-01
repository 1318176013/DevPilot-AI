from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ToolDefinitionCreate(BaseModel):
    name: str
    description: str
    category: str = "general"
    input_schema: dict = {}
    is_enabled: bool = True


class ToolDefinitionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str
    category: str
    input_schema: dict
    is_enabled: bool
    created_at: datetime


class ConstraintRuleCreate(BaseModel):
    project_id: UUID | None = None
    rule_type: str
    config: dict = {}
    is_enabled: bool = True


class ConstraintRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID | None
    rule_type: str
    config: dict
    is_enabled: bool
    created_at: datetime


class PolicyCheckRequest(BaseModel):
    project_id: UUID | None = None
    action_type: str
    payload: dict = {}


class PolicyCheckResponse(BaseModel):
    allowed: bool
    reason: str | None = None


class ToolCallRequest(BaseModel):
    tool_name: str
    payload: dict = {}
    project_id: UUID | None = None
    run_id: UUID | None = None


class ToolCallLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    run_id: UUID | None
    project_id: UUID | None
    tool_name: str
    input_payload: dict
    output_payload: dict
    status: str
    error_message: str | None
    created_at: datetime


class PatchPreviewRequest(BaseModel):
    project_id: UUID
    path: str
    new_content: str


class PatchPreviewResponse(BaseModel):
    path: str
    diff: str
    has_changes: bool
    original_content: str
    new_content: str


class PatchApplyRequest(PatchPreviewRequest):
    expected_original_content: str | None = None
    run_id: UUID | None = None
    validation_command: str | None = None


class PatchAuditActionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    run_id: UUID
    sequence: int
    action_type: str
    message: str
    payload: dict
    status: str
    created_at: datetime


class PatchApplyResponse(BaseModel):
    write_call: ToolCallLogRead
    preview: PatchPreviewResponse
    git_diff_call: ToolCallLogRead | None = None
    validation_call: ToolCallLogRead | None = None
    audit_action: PatchAuditActionRead | None = None


class ConstraintViolationLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID | None
    rule_type: str
    message: str
    payload: dict
    created_at: datetime
