from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dag import DagEdge, DagNode
from app.models.requirement import Requirement

NODE_TEMPLATES = [
    {
        "node_type": "analysis",
        "label": "需求分析",
        "description": "解析结构化需求，确认目标、范围、风险和验收标准。",
    },
    {
        "node_type": "design",
        "label": "实现设计",
        "description": "根据项目上下文设计代码改动方案和验证策略。",
    },
    {
        "node_type": "coding",
        "label": "编码实现",
        "description": "执行允许范围内的代码修改或文件生成。",
    },
    {
        "node_type": "testing",
        "label": "测试验证",
        "description": "运行白名单验证命令，收集测试或 lint 结果。",
    },
    {
        "node_type": "review",
        "label": "结果复核",
        "description": "汇总代码 Diff、验证结果和后续风险。",
    },
]

ALLOWED_NODE_STATUSES = {"pending", "running", "success", "failed", "blocked"}


async def generate_dag(db: AsyncSession, requirement: Requirement) -> tuple[list[DagNode], list[DagEdge]]:
    await db.execute(delete(DagEdge).where(DagEdge.requirement_id == requirement.id))
    await db.execute(delete(DagNode).where(DagNode.requirement_id == requirement.id))

    nodes: list[DagNode] = []
    for index, template in enumerate(NODE_TEMPLATES):
        node = DagNode(
            requirement_id=requirement.id,
            node_type=template["node_type"],
            label=template["label"],
            description=template["description"],
            config={
                "structured_requirement": requirement.structured_requirement,
                "step_order": index + 1,
            },
            model_policy={"capability": template["node_type"]},
            position_x=float(index * 260),
            position_y=0.0,
            status="pending",
        )
        db.add(node)
        nodes.append(node)

    await db.flush()

    edges: list[DagEdge] = []
    for source, target in zip(nodes, nodes[1:]):
        edge = DagEdge(
            requirement_id=requirement.id,
            source_node_id=source.id,
            target_node_id=target.id,
            edge_type="sequential",
        )
        db.add(edge)
        edges.append(edge)

    requirement.status = "planned"
    await db.commit()

    for node in nodes:
        await db.refresh(node)
    for edge in edges:
        await db.refresh(edge)

    return nodes, edges


async def get_dag(db: AsyncSession, requirement_id: UUID) -> tuple[list[DagNode], list[DagEdge]]:
    nodes_result = await db.scalars(
        select(DagNode).where(DagNode.requirement_id == requirement_id).order_by(DagNode.position_x)
    )
    edges_result = await db.scalars(
        select(DagEdge).where(DagEdge.requirement_id == requirement_id).order_by(DagEdge.id)
    )
    return list(nodes_result), list(edges_result)


def validate_node_status(status: str) -> str:
    if status not in ALLOWED_NODE_STATUSES:
        allowed = ", ".join(sorted(ALLOWED_NODE_STATUSES))
        raise ValueError(f"Unsupported DAG node status: {status}. Allowed: {allowed}")
    return status
