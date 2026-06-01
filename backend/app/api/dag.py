from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.dag import DagNode
from app.models.requirement import Requirement
from app.schemas.dag import DagGenerateResponse, DagNodeRead, DagNodeStatusUpdate, DagRead
from app.services.dag_engine import generate_dag, get_dag, validate_node_status

router = APIRouter(tags=["dag"])


@router.post(
    "/api/requirements/{requirement_id}/dag/generate",
    response_model=DagGenerateResponse,
)
async def generate_requirement_dag(
    requirement_id: UUID, db: AsyncSession = Depends(get_db)
) -> DagGenerateResponse:
    requirement = await db.get(Requirement, requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    nodes, edges = await generate_dag(db, requirement)
    return DagGenerateResponse(
        requirement_id=requirement.id,
        nodes=nodes,
        edges=edges,
        generated=True,
    )


@router.get("/api/requirements/{requirement_id}/dag", response_model=DagRead)
async def get_requirement_dag(requirement_id: UUID, db: AsyncSession = Depends(get_db)) -> DagRead:
    requirement = await db.get(Requirement, requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    nodes, edges = await get_dag(db, requirement_id)
    return DagRead(requirement_id=requirement_id, nodes=nodes, edges=edges)


@router.patch("/api/dag/nodes/{node_id}/status", response_model=DagNodeRead)
async def update_dag_node_status(
    node_id: UUID, payload: DagNodeStatusUpdate, db: AsyncSession = Depends(get_db)
) -> DagNode:
    node = await db.get(DagNode, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="DAG node not found")

    try:
        node.status = validate_node_status(payload.status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await db.commit()
    await db.refresh(node)
    return node
