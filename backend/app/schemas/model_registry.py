from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ModelProviderCreate(BaseModel):
    name: str
    api_base: str | None = None
    is_enabled: bool = True


class ModelProviderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    api_base: str | None
    is_enabled: bool
    created_at: datetime


class ModelCreate(BaseModel):
    provider_id: UUID
    model_key: str
    name: str
    capabilities: list[str] = []
    context_window: int | None = None
    cost_per_1k_input: float | None = None
    cost_per_1k_output: float | None = None
    supports_vision: bool = False
    supports_function_calling: bool = True
    is_enabled: bool = True


class ModelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    provider_id: UUID
    model_key: str
    name: str
    capabilities: list[str]
    context_window: int | None
    cost_per_1k_input: float | None
    cost_per_1k_output: float | None
    supports_vision: bool
    supports_function_calling: bool
    is_enabled: bool
    created_at: datetime
