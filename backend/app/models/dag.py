import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DagNode(Base):
    __tablename__ = "dag_nodes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requirement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("requirements.id", ondelete="CASCADE"), index=True
    )
    node_type: Mapped[str] = mapped_column(String(100))
    label: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    config: Mapped[dict] = mapped_column(JSONB, default=dict)
    model_policy: Mapped[dict] = mapped_column(JSONB, default=dict)
    position_x: Mapped[float] = mapped_column(Float, default=0)
    position_y: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    requirement = relationship("Requirement", back_populates="dag_nodes")
    outgoing_edges = relationship(
        "DagEdge",
        foreign_keys="DagEdge.source_node_id",
        back_populates="source_node",
        cascade="all, delete-orphan",
    )
    incoming_edges = relationship(
        "DagEdge",
        foreign_keys="DagEdge.target_node_id",
        back_populates="target_node",
        cascade="all, delete-orphan",
    )


class DagEdge(Base):
    __tablename__ = "dag_edges"
    __table_args__ = (UniqueConstraint("source_node_id", "target_node_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requirement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("requirements.id", ondelete="CASCADE"), index=True
    )
    source_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dag_nodes.id", ondelete="CASCADE")
    )
    target_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dag_nodes.id", ondelete="CASCADE")
    )
    edge_type: Mapped[str] = mapped_column(String(50), default="sequential")
    condition_expr: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    requirement = relationship("Requirement")
    source_node = relationship("DagNode", foreign_keys=[source_node_id], back_populates="outgoing_edges")
    target_node = relationship("DagNode", foreign_keys=[target_node_id], back_populates="incoming_edges")
