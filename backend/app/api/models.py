from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.model_registry import ModelConfig, ModelProvider
from app.schemas.model_registry import (
    ModelCreate,
    ModelProviderCreate,
    ModelProviderRead,
    ModelRead,
)

router = APIRouter(prefix="/api/models", tags=["models"])


@router.post("/providers", response_model=ModelProviderRead, status_code=status.HTTP_201_CREATED)
async def create_provider(
    payload: ModelProviderCreate, db: AsyncSession = Depends(get_db)
) -> ModelProvider:
    provider = ModelProvider(**payload.model_dump())
    db.add(provider)
    await db.commit()
    await db.refresh(provider)
    return provider


@router.get("/providers", response_model=list[ModelProviderRead])
async def list_providers(db: AsyncSession = Depends(get_db)) -> list[ModelProvider]:
    result = await db.scalars(select(ModelProvider).order_by(ModelProvider.created_at.desc()))
    return list(result)


@router.post("", response_model=ModelRead, status_code=status.HTTP_201_CREATED)
async def create_model(payload: ModelCreate, db: AsyncSession = Depends(get_db)) -> ModelConfig:
    provider = await db.get(ModelProvider, payload.provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Model provider not found")

    exists = await db.scalar(select(ModelConfig).where(ModelConfig.model_key == payload.model_key))
    if exists:
        raise HTTPException(status_code=409, detail="Model key already exists")

    model = ModelConfig(**payload.model_dump())
    db.add(model)
    await db.commit()
    await db.refresh(model)
    return model


@router.get("", response_model=list[ModelRead])
async def list_models(db: AsyncSession = Depends(get_db)) -> list[ModelConfig]:
    result = await db.scalars(select(ModelConfig).order_by(ModelConfig.created_at.desc()))
    return list(result)
