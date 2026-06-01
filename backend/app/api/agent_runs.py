from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.agent_run import AgentAction, AgentRun
from app.models.requirement import Requirement
from app.schemas.agent_run import AgentActionRead, AgentRunCreate, AgentRunDetail, AgentRunRead
from app.services.agent_runtime import get_run, list_actions, list_runs, start_lightweight_run

router = APIRouter(prefix="/api/agent-runs", tags=["agent-runs"])


@router.post("", response_model=AgentRunDetail, status_code=status.HTTP_201_CREATED)
async def create_agent_run(
    payload: AgentRunCreate, db: AsyncSession = Depends(get_db)
) -> AgentRun:
    requirement = await db.get(Requirement, payload.requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    try:
        return await start_lightweight_run(db, requirement, payload.dag_node_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("", response_model=list[AgentRunRead])
async def get_agent_runs(
    requirement_id: UUID | None = None, db: AsyncSession = Depends(get_db)
) -> list[AgentRun]:
    return await list_runs(db, requirement_id)


@router.get("/{run_id}", response_model=AgentRunDetail)
async def get_agent_run(run_id: UUID, db: AsyncSession = Depends(get_db)) -> AgentRun:
    try:
        return await get_run(db, run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{run_id}/actions", response_model=list[AgentActionRead])
async def get_agent_run_actions(run_id: UUID, db: AsyncSession = Depends(get_db)) -> list[AgentAction]:
    run = await db.get(AgentRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return await list_actions(db, run_id)
