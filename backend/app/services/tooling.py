from __future__ import annotations

import asyncio
import difflib
from pathlib import Path
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_run import AgentAction, AgentRun
from app.models.project import Project
from app.models.requirement import Requirement
from app.models.tooling import ConstraintRule, ConstraintViolationLog, ToolCallLog, ToolDefinition

DEFAULT_TOOLS = [
    {
        "name": "file.read",
        "description": "读取项目目录内的文本文件。",
        "category": "file",
        "input_schema": {"path": "string"},
    },
    {
        "name": "file.write",
        "description": "写入项目目录内的文本文件。",
        "category": "file",
        "input_schema": {"path": "string", "content": "string"},
    },
    {
        "name": "code.search",
        "description": "在项目目录内搜索代码文本。",
        "category": "code",
        "input_schema": {"query": "string", "query_path": "string"},
    },
    {
        "name": "shell.run",
        "description": "执行白名单内的本地命令。",
        "category": "shell",
        "input_schema": {"command": "string"},
    },
    {
        "name": "git.diff",
        "description": "查看项目工作区 Diff。",
        "category": "git",
        "input_schema": {},
    },
    {
        "name": "test.run",
        "description": "执行测试或 lint 命令。",
        "category": "test",
        "input_schema": {"command": "string"},
    },
]

DEFAULT_COMMANDS = ["npm test", "npm run lint", "npm run test", "pytest", "python -m pytest"]
DANGEROUS_GIT_KEYWORDS = [" push", " reset", " clean", " rebase", " commit", " checkout"]
MAX_FILE_READ_CHARS = 20_000
MAX_COMMAND_OUTPUT_CHARS = 20_000


async def ensure_default_tools(db: AsyncSession) -> list[ToolDefinition]:
    tools: list[ToolDefinition] = []
    for item in DEFAULT_TOOLS:
        tool = await db.scalar(select(ToolDefinition).where(ToolDefinition.name == item["name"]))
        if not tool:
            tool = ToolDefinition(**item)
            db.add(tool)
        tools.append(tool)
    await db.commit()
    return await list_tools(db)


async def list_tools(db: AsyncSession) -> list[ToolDefinition]:
    result = await db.scalars(select(ToolDefinition).order_by(ToolDefinition.category, ToolDefinition.name))
    return list(result)


async def list_rules(db: AsyncSession, project_id: UUID | None = None) -> list[ConstraintRule]:
    stmt = select(ConstraintRule).order_by(ConstraintRule.created_at.desc())
    if project_id:
        stmt = stmt.where(ConstraintRule.project_id == project_id)
    result = await db.scalars(stmt)
    return list(result)


async def check_policy(
    db: AsyncSession, action_type: str, payload: dict, project_id: UUID | None = None
) -> tuple[bool, str | None]:
    project = await db.get(Project, project_id) if project_id else None
    rules = await _active_rules(db, project_id)

    allowed, reason = _evaluate_builtin_policy(action_type, payload, project, rules)
    if not allowed:
        db.add(
            ConstraintViolationLog(
                project_id=project_id,
                rule_type=action_type,
                message=reason or "Policy denied",
                payload=payload,
            )
        )
        await db.commit()
    return allowed, reason


async def execute_tool(
    db: AsyncSession,
    tool_name: str,
    payload: dict,
    project_id: UUID | None = None,
    run_id: UUID | None = None,
) -> ToolCallLog:
    tool = await db.scalar(select(ToolDefinition).where(ToolDefinition.name == tool_name))
    if not tool:
        await ensure_default_tools(db)
        tool = await db.scalar(select(ToolDefinition).where(ToolDefinition.name == tool_name))
    if not tool or not tool.is_enabled:
        return await _record_tool_call(
            db, tool_name, payload, project_id, run_id, {}, "failed", "工具不存在或未启用"
        )

    allowed, reason = await check_policy(db, tool_name, payload, project_id)
    if not allowed:
        return await _record_tool_call(db, tool_name, payload, project_id, run_id, {}, "blocked", reason)

    try:
        project = await db.get(Project, project_id) if project_id else None
        output = await _execute_tool_impl(tool_name, payload, project)
        return await _record_tool_call(db, tool_name, payload, project_id, run_id, output, "success", None)
    except Exception as exc:
        return await _record_tool_call(db, tool_name, payload, project_id, run_id, {}, "failed", str(exc))


async def preview_patch(db: AsyncSession, project_id: UUID, path: str, new_content: str) -> dict:
    project = await db.get(Project, project_id)
    if not project:
        raise ValueError("Project not found")
    allowed, reason = await check_policy(db, "file.write", {"path": path}, project_id)
    if not allowed:
        raise PermissionError(reason or "Policy denied")
    target_path = _resolve_payload_path({"path": path}, project)
    original_content = target_path.read_text(encoding="utf-8", errors="replace") if target_path.exists() else ""
    diff = _build_unified_diff(path, original_content, new_content)
    return {
        "path": path,
        "diff": diff,
        "has_changes": original_content != new_content,
        "original_content": original_content,
        "new_content": new_content,
    }


async def apply_patch(
    db: AsyncSession,
    project_id: UUID,
    path: str,
    new_content: str,
    expected_original_content: str | None = None,
    run_id: UUID | None = None,
    validation_command: str | None = None,
) -> dict:
    await _validate_patch_run_project(db, run_id, project_id)
    preview = await preview_patch(db, project_id, path, new_content)
    if expected_original_content is not None and preview["original_content"] != expected_original_content:
        write_call = await _record_tool_call(
            db,
            "file.write",
            {"path": path, "content": new_content},
            project_id,
            run_id,
            {"diff": preview["diff"], "conflict": True},
            "blocked",
            "文件内容已变化，请重新预览补丁",
        )
        audit_action = await _record_patch_action(
            db,
            run_id,
            path,
            write_call.status,
            "文件内容已变化，补丁应用被冲突保护拦截。",
            [write_call],
        )
        return {
            "write_call": write_call,
            "preview": preview,
            "git_diff_call": None,
            "validation_call": None,
            "audit_action": audit_action,
        }

    write_call = await execute_tool(db, "file.write", {"path": path, "content": new_content}, project_id, run_id)
    git_diff_call = await execute_tool(db, "git.diff", {}, project_id, run_id)
    validation_call = None
    if validation_command and validation_command.strip():
        validation_call = await execute_tool(
            db, "test.run", {"command": validation_command.strip()}, project_id, run_id
        )
    audit_action = await _record_patch_action(
        db,
        run_id,
        path,
        _patch_action_status([write_call, git_diff_call, validation_call]),
        "补丁已确认应用，并完成应用后 Diff 与可选验证。",
        [write_call, git_diff_call, validation_call],
    )
    return {
        "write_call": write_call,
        "preview": preview,
        "git_diff_call": git_diff_call,
        "validation_call": validation_call,
        "audit_action": audit_action,
    }


async def _validate_patch_run_project(db: AsyncSession, run_id: UUID | None, project_id: UUID) -> None:
    if not run_id:
        return
    run = await db.get(AgentRun, run_id)
    if not run:
        raise ValueError("Agent run not found")
    requirement = await db.get(Requirement, run.requirement_id)
    if not requirement or requirement.project_id != project_id:
        raise PermissionError("Agent Run 不属于当前项目，不能关联本次补丁应用")


async def _record_patch_action(
    db: AsyncSession,
    run_id: UUID | None,
    path: str,
    status: str,
    message: str,
    calls: list[ToolCallLog | None],
) -> AgentAction | None:
    if not run_id or not await db.get(AgentRun, run_id):
        return None
    next_sequence = (await db.scalar(select(func.max(AgentAction.sequence)).where(AgentAction.run_id == run_id)) or 0) + 1
    action = AgentAction(
        run_id=run_id,
        sequence=next_sequence,
        action_type="patch.apply",
        message=message,
        payload={
            "path": path,
            "tool_call_ids": [str(call.id) for call in calls if call],
            "tool_call_statuses": {call.tool_name: call.status for call in calls if call},
        },
        status=status,
    )
    db.add(action)
    await db.commit()
    await db.refresh(action)
    return action


def _patch_action_status(calls: list[ToolCallLog | None]) -> str:
    statuses = [call.status for call in calls if call]
    if any(status in {"failed", "blocked"} for status in statuses):
        return "warning"
    return "success"


async def list_tool_call_logs(
    db: AsyncSession, project_id: UUID | None = None, run_id: UUID | None = None
) -> list[ToolCallLog]:
    stmt = select(ToolCallLog).order_by(ToolCallLog.created_at.desc())
    if project_id:
        stmt = stmt.where(ToolCallLog.project_id == project_id)
    if run_id:
        stmt = stmt.where(ToolCallLog.run_id == run_id)
    result = await db.scalars(stmt)
    return list(result)


async def list_violation_logs(
    db: AsyncSession, project_id: UUID | None = None
) -> list[ConstraintViolationLog]:
    stmt = select(ConstraintViolationLog).order_by(ConstraintViolationLog.created_at.desc())
    if project_id:
        stmt = stmt.where(ConstraintViolationLog.project_id == project_id)
    result = await db.scalars(stmt)
    return list(result)


async def _execute_tool_impl(tool_name: str, payload: dict, project: Project | None) -> dict:
    if tool_name == "file.read":
        return _read_file(payload, project)
    if tool_name == "file.write":
        return _write_file(payload, project)
    if tool_name == "code.search":
        return await _search_code(payload, project)
    if tool_name == "git.diff":
        return await _run_command("git diff --stat && git diff --", project)
    if tool_name in {"shell.run", "test.run"}:
        return await _run_command(str(payload.get("command") or ""), project)
    raise ValueError(f"Unsupported tool: {tool_name}")


def _read_file(payload: dict, project: Project | None) -> dict:
    path = _resolve_payload_path(payload, project)
    content = path.read_text(encoding="utf-8", errors="replace")
    truncated = len(content) > MAX_FILE_READ_CHARS
    return {
        "path": str(path),
        "content": content[:MAX_FILE_READ_CHARS],
        "size": path.stat().st_size,
        "truncated": truncated,
    }


def _write_file(payload: dict, project: Project | None) -> dict:
    path = _resolve_payload_path(payload, project)
    content = str(payload.get("content") or "")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return {"path": str(path), "bytes_written": len(content.encode("utf-8"))}


async def _search_code(payload: dict, project: Project | None) -> dict:
    query = str(payload.get("query") or "").strip()
    if not query:
        raise ValueError("搜索关键词不能为空")
    base_path = _resolve_search_path(payload, project)
    command = f"grep -RIn --exclude-dir=.git --exclude-dir=node_modules -- {query!r} ."
    return await _run_command(command, project, cwd=base_path, allow_failure=True)


async def _run_command(
    command: str,
    project: Project | None,
    cwd: Path | None = None,
    allow_failure: bool = False,
) -> dict:
    if not command.strip():
        raise ValueError("命令不能为空")
    working_dir = cwd or (Path(project.local_path).expanduser().resolve() if project else Path.cwd())
    process = await asyncio.create_subprocess_shell(
        command,
        cwd=str(working_dir),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout_bytes, stderr_bytes = await asyncio.wait_for(process.communicate(), timeout=60)
    stdout = stdout_bytes.decode("utf-8", errors="replace")
    stderr = stderr_bytes.decode("utf-8", errors="replace")
    output = {
        "command": command,
        "cwd": str(working_dir),
        "returncode": process.returncode,
        "stdout": stdout[:MAX_COMMAND_OUTPUT_CHARS],
        "stderr": stderr[:MAX_COMMAND_OUTPUT_CHARS],
        "truncated": len(stdout) > MAX_COMMAND_OUTPUT_CHARS or len(stderr) > MAX_COMMAND_OUTPUT_CHARS,
    }
    if process.returncode != 0 and not allow_failure:
        raise RuntimeError(stderr.strip() or stdout.strip() or f"命令执行失败：{process.returncode}")
    return output


async def _record_tool_call(
    db: AsyncSession,
    tool_name: str,
    payload: dict,
    project_id: UUID | None,
    run_id: UUID | None,
    output: dict,
    status: str,
    error_message: str | None,
) -> ToolCallLog:
    log = ToolCallLog(
        run_id=run_id,
        project_id=project_id,
        tool_name=tool_name,
        input_payload=payload,
        output_payload=output,
        status=status,
        error_message=error_message,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


async def _active_rules(db: AsyncSession, project_id: UUID | None) -> list[ConstraintRule]:
    stmt = select(ConstraintRule).where(ConstraintRule.is_enabled.is_(True))
    if project_id:
        stmt = stmt.where((ConstraintRule.project_id == project_id) | (ConstraintRule.project_id.is_(None)))
    else:
        stmt = stmt.where(ConstraintRule.project_id.is_(None))
    result = await db.scalars(stmt)
    return list(result)


def _evaluate_builtin_policy(
    action_type: str, payload: dict, project: Project | None, rules: list[ConstraintRule]
) -> tuple[bool, str | None]:
    if action_type in {"file.write", "file.read", "code.search"}:
        path = str(payload.get("path") or payload.get("query_path") or "")
        if action_type != "code.search" and not path:
            return False, "文件路径不能为空"
        if project and path and not _is_inside_project(_resolve_project_path(path, project), project.local_path):
            return False, "文件路径超出项目目录"

    if action_type == "file.delete":
        return False, "MVP 默认禁止删除文件"

    if action_type in {"shell.run", "test.run"}:
        command = str(payload.get("command") or "").strip()
        if not command:
            return False, "命令不能为空"
        if command.startswith("git") and any(keyword in f" {command}" for keyword in DANGEROUS_GIT_KEYWORDS):
            return False, "禁止执行高危 Git 命令"
        allowed_commands = _allowed_commands(rules)
        if not any(command == allowed or command.startswith(f"{allowed} ") for allowed in allowed_commands):
            return False, "命令不在白名单中"

    return True, None


def _allowed_commands(rules: list[ConstraintRule]) -> list[str]:
    commands = list(DEFAULT_COMMANDS)
    for rule in rules:
        if rule.rule_type == "command_whitelist":
            commands.extend(str(command) for command in rule.config.get("commands", []))
    return commands


def _resolve_payload_path(payload: dict, project: Project | None) -> Path:
    raw_path = str(payload.get("path") or "")
    if not raw_path:
        raise ValueError("文件路径不能为空")
    path = _resolve_project_path(raw_path, project)
    if project and not _is_inside_project(path, project.local_path):
        raise ValueError("文件路径超出项目目录")
    return path


def _resolve_search_path(payload: dict, project: Project | None) -> Path:
    raw_path = str(payload.get("query_path") or payload.get("path") or ".")
    path = _resolve_project_path(raw_path, project)
    if project and not _is_inside_project(path, project.local_path):
        raise ValueError("搜索路径超出项目目录")
    return path


def _resolve_project_path(path: str | Path, project: Project | None) -> Path:
    resolved = Path(path).expanduser()
    if project and not resolved.is_absolute():
        resolved = Path(project.local_path).expanduser() / resolved
    return resolved.resolve()


def _is_inside_project(path: str | Path, project_path: str) -> bool:
    try:
        resolved_path = Path(path).expanduser().resolve()
        resolved_project = Path(project_path).expanduser().resolve()
        return resolved_path == resolved_project or resolved_project in resolved_path.parents
    except OSError:
        return False


def _build_unified_diff(path: str, original_content: str, new_content: str) -> str:
    return "".join(
        difflib.unified_diff(
            original_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
        )
    )
