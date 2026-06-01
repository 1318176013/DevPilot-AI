from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.project import Project
from app.models.tooling import ConstraintRule, ConstraintViolationLog, ToolCallLog, ToolDefinition
from app.schemas.tooling import (
    ConstraintRuleCreate,
    ConstraintRuleRead,
    ConstraintViolationLogRead,
    PatchApplyRequest,
    PatchApplyResponse,
    PatchPreviewRequest,
    PatchPreviewResponse,
    PolicyCheckRequest,
    PolicyCheckResponse,
    ToolCallLogRead,
    ToolCallRequest,
    ToolDefinitionCreate,
    ToolDefinitionRead,
)
from app.services.tooling import (
    apply_patch,
    check_policy,
    ensure_default_tools,
    execute_tool,
    list_rules,
    list_tool_call_logs,
    list_tools,
    list_violation_logs,
    preview_patch,
)

router = APIRouter(prefix="/api/tools", tags=["tools"])


@router.post("/defaults", response_model=list[ToolDefinitionRead])
async def seed_default_tools(db: AsyncSession = Depends(get_db)) -> list[ToolDefinition]:
    return await ensure_default_tools(db)


@router.post("/rules", response_model=ConstraintRuleRead, status_code=status.HTTP_201_CREATED)
async def create_rule(payload: ConstraintRuleCreate, db: AsyncSession = Depends(get_db)) -> ConstraintRule:
    if payload.project_id and not await db.get(Project, payload.project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    rule = ConstraintRule(**payload.model_dump())
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.get("/rules", response_model=list[ConstraintRuleRead])
async def get_rules(
    project_id: UUID | None = None, db: AsyncSession = Depends(get_db)
) -> list[ConstraintRule]:
    return await list_rules(db, project_id)


@router.post("/policy/check", response_model=PolicyCheckResponse)
async def check_tool_policy(
    payload: PolicyCheckRequest, db: AsyncSession = Depends(get_db)
) -> PolicyCheckResponse:
    if payload.project_id and not await db.get(Project, payload.project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    allowed, reason = await check_policy(db, payload.action_type, payload.payload, payload.project_id)
    return PolicyCheckResponse(allowed=allowed, reason=reason)


@router.post("/patch/preview", response_model=PatchPreviewResponse)
async def preview_tool_patch(
    payload: PatchPreviewRequest, db: AsyncSession = Depends(get_db)
) -> PatchPreviewResponse:
    try:
        result = await preview_patch(db, payload.project_id, payload.path, payload.new_content)
        return PatchPreviewResponse(**result)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/patch/apply", response_model=PatchApplyResponse)
async def apply_tool_patch(payload: PatchApplyRequest, db: AsyncSession = Depends(get_db)) -> PatchApplyResponse:
    try:
        result = await apply_patch(
            db,
            payload.project_id,
            payload.path,
            payload.new_content,
            payload.expected_original_content,
            payload.run_id,
            payload.validation_command,
        )
        return PatchApplyResponse(**result)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/call", response_model=ToolCallLogRead)
async def call_tool(payload: ToolCallRequest, db: AsyncSession = Depends(get_db)) -> ToolCallLog:
    if payload.project_id and not await db.get(Project, payload.project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    return await execute_tool(db, payload.tool_name, payload.payload, payload.project_id, payload.run_id)


@router.get("/calls", response_model=list[ToolCallLogRead])
async def get_tool_call_logs(
    project_id: UUID | None = None,
    run_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[ToolCallLog]:
    return await list_tool_call_logs(db, project_id, run_id)


@router.get("/violations", response_model=list[ConstraintViolationLogRead])
async def get_violation_logs(
    project_id: UUID | None = None, db: AsyncSession = Depends(get_db)
) -> list[ConstraintViolationLog]:
    return await list_violation_logs(db, project_id)


@router.post("", response_model=ToolDefinitionRead, status_code=status.HTTP_201_CREATED)
async def create_tool(payload: ToolDefinitionCreate, db: AsyncSession = Depends(get_db)) -> ToolDefinition:
    exists = await db.scalar(select(ToolDefinition).where(ToolDefinition.name == payload.name))
    if exists:
        raise HTTPException(status_code=409, detail="Tool name already exists")
    tool = ToolDefinition(**payload.model_dump())
    db.add(tool)
    await db.commit()
    await db.refresh(tool)
    return tool


@router.get("", response_model=list[ToolDefinitionRead])
async def get_tools(db: AsyncSession = Depends(get_db)) -> list[ToolDefinition]:
    return await list_tools(db)
