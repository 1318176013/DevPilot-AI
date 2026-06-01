from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.project import Project
from app.models.requirement import Requirement
from app.schemas.requirement import RequirementCreate, RequirementRead, RequirementUpdate
from app.services.requirement_engine import structure_requirement

router = APIRouter(prefix="/api/requirements", tags=["requirements"])


@router.post("", response_model=RequirementRead, status_code=status.HTTP_201_CREATED)
async def create_requirement(
    payload: RequirementCreate, db: AsyncSession = Depends(get_db)
) -> Requirement:
    project = await db.get(Project, payload.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    requirement = Requirement(
        **payload.model_dump(),
        structured_requirement=structure_requirement(payload.title, payload.raw_requirement),
        status="draft",
    )
    db.add(requirement)
    await db.commit()
    await db.refresh(requirement)
    return requirement


@router.get("", response_model=list[RequirementRead])
async def list_requirements(
    project_id: UUID | None = None, db: AsyncSession = Depends(get_db)
) -> list[Requirement]:
    stmt = select(Requirement).order_by(Requirement.created_at.desc())
    if project_id:
        stmt = stmt.where(Requirement.project_id == project_id)
    result = await db.scalars(stmt)
    return list(result)


@router.get("/{requirement_id}", response_model=RequirementRead)
async def get_requirement(requirement_id: UUID, db: AsyncSession = Depends(get_db)) -> Requirement:
    requirement = await db.get(Requirement, requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return requirement


@router.patch("/{requirement_id}", response_model=RequirementRead)
async def update_requirement(
    requirement_id: UUID, payload: RequirementUpdate, db: AsyncSession = Depends(get_db)
) -> Requirement:
    requirement = await db.get(Requirement, requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(requirement, key, value)

    if "title" in data or "raw_requirement" in data:
        requirement.structured_requirement = structure_requirement(
            requirement.title, requirement.raw_requirement
        )

    await db.commit()
    await db.refresh(requirement)
    return requirement
