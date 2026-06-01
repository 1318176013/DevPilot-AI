from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.agent_run import AgentAction, AgentRun
from app.models.dag import DagNode
from app.models.requirement import Requirement
from app.models.tooling import ToolCallLog
from app.services.tooling import execute_tool


async def start_lightweight_run(
    db: AsyncSession, requirement: Requirement, dag_node_id: UUID | None = None
) -> AgentRun:
    node = await _resolve_node(db, requirement.id, dag_node_id)
    run = AgentRun(
        requirement_id=requirement.id,
        dag_node_id=node.id if node else None,
        backend="lightweight",
        status="running",
        started_at=datetime.now(UTC),
        summary="Lightweight Agent 正在执行 DAG 节点。",
    )
    db.add(run)
    await db.flush()

    if node:
        node.status = "running"
        node.started_at = run.started_at

    actions = _build_initial_actions(run, requirement, node)
    db.add_all(actions)
    await db.commit()

    tool_calls = await _execute_run_tools(db, run, requirement, node)
    final_action = AgentAction(
        run_id=run.id,
        sequence=len(actions) + 1,
        action_type="result.report",
        message="生成本次 Lightweight Agent 真实工具调用报告。",
        payload={"tool_calls": len(tool_calls), "failed_calls": _count_failed_calls(tool_calls)},
        status="success" if all(call.status == "success" for call in tool_calls) else "warning",
    )
    db.add(final_action)

    if node:
        node.status = "success" if all(call.status != "failed" for call in tool_calls) else "failed"
        node.finished_at = datetime.now(UTC)

    run.status = "success" if all(call.status != "failed" for call in tool_calls) else "failed"
    run.finished_at = datetime.now(UTC)
    run.summary = _build_summary(node, tool_calls)
    run.result = {
        "requirement_title": requirement.title,
        "dag_node": node.node_type if node else None,
        "actions": len(actions) + 1,
        "tool_calls": len(tool_calls),
        "tool_call_statuses": {call.tool_name: call.status for call in tool_calls},
        "delivery_report": _delivery_report_path(run.id),
        "next_step": "可继续扩展代码补丁生成，让 Agent 在 Policy Guard 保护下修改目标源码。",
    }
    requirement.status = "planned"

    await db.commit()
    return await get_run(db, run.id)


async def get_run(db: AsyncSession, run_id: UUID) -> AgentRun:
    run = await db.scalar(
        select(AgentRun)
        .options(selectinload(AgentRun.actions), selectinload(AgentRun.tool_calls))
        .where(AgentRun.id == run_id)
    )
    if not run:
        raise ValueError("Agent run not found")
    run.actions.sort(key=lambda action: action.sequence)
    run.tool_calls.sort(key=lambda call: call.created_at, reverse=True)
    return run


async def list_runs(db: AsyncSession, requirement_id: UUID | None = None) -> list[AgentRun]:
    stmt = select(AgentRun).order_by(AgentRun.created_at.desc())
    if requirement_id:
        stmt = stmt.where(AgentRun.requirement_id == requirement_id)
    result = await db.scalars(stmt)
    return list(result)


async def list_actions(db: AsyncSession, run_id: UUID) -> list[AgentAction]:
    result = await db.scalars(
        select(AgentAction).where(AgentAction.run_id == run_id).order_by(AgentAction.sequence)
    )
    return list(result)


async def _resolve_node(
    db: AsyncSession, requirement_id: UUID, dag_node_id: UUID | None
) -> DagNode | None:
    if dag_node_id:
        node = await db.get(DagNode, dag_node_id)
        if not node or node.requirement_id != requirement_id:
            raise ValueError("DAG node not found for requirement")
        return node

    return await db.scalar(
        select(DagNode)
        .where(DagNode.requirement_id == requirement_id, DagNode.status.in_(["pending", "blocked"]))
        .order_by(DagNode.position_x)
    )


def _build_initial_actions(run: AgentRun, requirement: Requirement, node: DagNode | None) -> list[AgentAction]:
    node_label = node.label if node else "未选择 DAG 节点"
    return [
        AgentAction(
            run_id=run.id,
            sequence=1,
            action_type="context.prepare",
            message="加载项目、需求和 DAG 节点上下文。",
            payload={"requirement_id": str(requirement.id), "dag_node_id": str(node.id) if node else None},
        ),
        AgentAction(
            run_id=run.id,
            sequence=2,
            action_type="plan.generate",
            message=f"为节点“{node_label}”生成最小执行计划。",
            payload={"structured_requirement": requirement.structured_requirement},
        ),
        AgentAction(
            run_id=run.id,
            sequence=3,
            action_type="tool.execute",
            message="调用 Tool Registry 中的真实基础工具并记录 Tool Call Log。",
            payload={"tools": ["code.search", "git.diff", "file.write"]},
        ),
    ]


async def _execute_run_tools(
    db: AsyncSession, run: AgentRun, requirement: Requirement, node: DagNode | None
) -> list[ToolCallLog]:
    query = _search_query(requirement, node)
    report_path = _delivery_report_path(run.id)
    calls = [
        await execute_tool(
            db,
            "code.search",
            {"query": query, "query_path": "."},
            requirement.project_id,
            run.id,
        ),
        await execute_tool(db, "git.diff", {}, requirement.project_id, run.id),
        await execute_tool(
            db,
            "file.write",
            {"path": report_path, "content": _build_delivery_report(run, requirement, node)},
            requirement.project_id,
            run.id,
        ),
        await execute_tool(db, "git.diff", {}, requirement.project_id, run.id),
    ]
    return calls


def _delivery_report_path(run_id: UUID) -> str:
    return f".devpilot/runs/{run_id}/delivery-report.md"


def _build_delivery_report(run: AgentRun, requirement: Requirement, node: DagNode | None) -> str:
    node_label = node.label if node else "未选择 DAG 节点"
    node_type = node.node_type if node else "none"
    return "\n".join(
        [
            "# DevPilot Agent Delivery Report",
            "",
            f"- Run ID: {run.id}",
            f"- Requirement: {requirement.title}",
            f"- Requirement ID: {requirement.id}",
            f"- DAG Node: {node_label}",
            f"- Node Type: {node_type}",
            f"- Generated At: {datetime.now(UTC).isoformat()}",
            "",
            "## Summary",
            "",
            "Lightweight Agent 已完成本轮受控工具调用，并在 Policy Guard 保护下写入此交付报告。",
            "",
            "## Structured Requirement",
            "",
            str(requirement.structured_requirement),
            "",
        ]
    )


def _search_query(requirement: Requirement, node: DagNode | None) -> str:
    if node:
        return node.node_type
    return requirement.title.split()[0] if requirement.title.split() else requirement.title


def _count_failed_calls(tool_calls: list[ToolCallLog]) -> int:
    return sum(1 for call in tool_calls if call.status in {"failed", "blocked"})


def _build_summary(node: DagNode | None, tool_calls: list[ToolCallLog]) -> str:
    node_label = node.label if node else "未选择 DAG 节点"
    failed = _count_failed_calls(tool_calls)
    if failed:
        return f"节点“{node_label}”已执行真实工具调用，{failed} 个调用失败或被策略拦截。"
    return f"节点“{node_label}”已完成真实工具调用，共记录 {len(tool_calls)} 条 Tool Call Log。"
