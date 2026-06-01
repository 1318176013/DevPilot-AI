import argparse
import json
import os
import sys
from typing import Any

import httpx

DEFAULT_API_BASE_URL = "http://localhost:8000"


def get_api_base_url() -> str:
    return os.getenv("DEVPILOT_API_BASE_URL", DEFAULT_API_BASE_URL).rstrip("/")


def request_json(method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
    url = f"{get_api_base_url()}{path}"
    try:
        response = httpx.request(method, url, json=payload, timeout=10.0)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        print(f"请求失败：{exc.response.status_code} {exc.response.text}", file=sys.stderr)
        raise SystemExit(1) from exc
    except httpx.HTTPError as exc:
        print(f"无法连接 DevPilot API：{exc}", file=sys.stderr)
        raise SystemExit(1) from exc


def print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def list_projects(_: argparse.Namespace) -> None:
    projects = request_json("GET", "/api/projects")
    if not projects:
        print("暂无项目")
        return

    for project in projects:
        display_name = project.get("display_name") or project.get("name")
        local_path = project.get("local_path") or "-"
        status = project.get("status") or "unknown"
        print(f"{project['id']}  {display_name}  {status}  {local_path}")


def create_project(args: argparse.Namespace) -> None:
    payload = {
        "name": args.name,
        "display_name": args.display_name,
        "local_path": args.local_path,
        "language": args.language,
        "framework": args.framework,
    }
    print_json(request_json("POST", "/api/projects", payload))


def list_requirements(args: argparse.Namespace) -> None:
    path = "/api/requirements"
    if args.project_id:
        path = f"{path}?project_id={args.project_id}"
    requirements = request_json("GET", path)
    if not requirements:
        print("暂无需求")
        return

    for requirement in requirements:
        print(
            f"{requirement['id']}  {requirement['title']}  "
            f"{requirement['status']}  project={requirement['project_id']}"
        )


def create_requirement(args: argparse.Namespace) -> None:
    payload = {
        "project_id": args.project_id,
        "title": args.title,
        "raw_requirement": args.raw_requirement,
        "priority": args.priority,
    }
    print_json(request_json("POST", "/api/requirements", payload))


def show_requirement(args: argparse.Namespace) -> None:
    print_json(request_json("GET", f"/api/requirements/{args.requirement_id}"))


def generate_dag(args: argparse.Namespace) -> None:
    print_json(request_json("POST", f"/api/requirements/{args.requirement_id}/dag/generate"))


def show_dag(args: argparse.Namespace) -> None:
    print_json(request_json("GET", f"/api/requirements/{args.requirement_id}/dag"))


def start_run(args: argparse.Namespace) -> None:
    payload = {
        "requirement_id": args.requirement_id,
        "dag_node_id": args.dag_node_id,
    }
    print_json(request_json("POST", "/api/agent-runs", payload))


def list_runs(args: argparse.Namespace) -> None:
    path = "/api/agent-runs"
    if args.requirement_id:
        path = f"{path}?requirement_id={args.requirement_id}"
    runs = request_json("GET", path)
    if not runs:
        print("暂无 Agent Run")
        return

    for run in runs:
        print(
            f"{run['id']}  {run['status']}  {run['backend']}  "
            f"requirement={run['requirement_id']}"
        )


def show_run(args: argparse.Namespace) -> None:
    print_json(request_json("GET", f"/api/agent-runs/{args.run_id}"))


def seed_tools(_: argparse.Namespace) -> None:
    print_json(request_json("POST", "/api/tools/defaults"))


def list_tools(_: argparse.Namespace) -> None:
    tools = request_json("GET", "/api/tools")
    if not tools:
        print("暂无工具")
        return

    for tool in tools:
        print(f"{tool['name']}  {tool['category']}  enabled={tool['is_enabled']}")


def check_policy(args: argparse.Namespace) -> None:
    payload = {"command": args.command} if args.action_type in {"shell.run", "test.run"} else {"path": args.path}
    print_json(
        request_json(
            "POST",
            "/api/tools/policy/check",
            {
                "project_id": args.project_id,
                "action_type": args.action_type,
                "payload": payload,
            },
        )
    )


def call_tool(args: argparse.Namespace) -> None:
    payload = json.loads(args.payload) if args.payload else {}
    print_json(
        request_json(
            "POST",
            "/api/tools/call",
            {
                "project_id": args.project_id,
                "run_id": args.run_id,
                "tool_name": args.tool_name,
                "payload": payload,
            },
        )
    )


def list_tool_calls(args: argparse.Namespace) -> None:
    query = []
    if args.project_id:
        query.append(f"project_id={args.project_id}")
    if args.run_id:
        query.append(f"run_id={args.run_id}")
    path = "/api/tools/calls"
    if query:
        path = f"{path}?{'&'.join(query)}"
    print_json(request_json("GET", path))


def preview_patch(args: argparse.Namespace) -> None:
    print_json(
        request_json(
            "POST",
            "/api/tools/patch/preview",
            {
                "project_id": args.project_id,
                "path": args.path,
                "new_content": args.new_content,
            },
        )
    )


def apply_patch(args: argparse.Namespace) -> None:
    print_json(
        request_json(
            "POST",
            "/api/tools/patch/apply",
            {
                "project_id": args.project_id,
                "run_id": args.run_id,
                "path": args.path,
                "new_content": args.new_content,
                "expected_original_content": args.expected_original_content,
                "validation_command": args.validation_command,
            },
        )
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="devpilot", description="DevPilot AI MVP CLI")
    subparsers = parser.add_subparsers(dest="resource", required=True)

    project_parser = subparsers.add_parser("project", aliases=["projects"], help="项目管理")
    project_subparsers = project_parser.add_subparsers(dest="action", required=True)

    list_parser = project_subparsers.add_parser("list", help="查看项目列表")
    list_parser.set_defaults(func=list_projects)

    create_parser = project_subparsers.add_parser("create", help="创建项目")
    create_parser.add_argument("--name", required=True, help="项目唯一名称")
    create_parser.add_argument("--local-path", required=True, help="项目本地路径")
    create_parser.add_argument("--display-name", default=None, help="项目显示名称")
    create_parser.add_argument("--language", default=None, help="主要语言")
    create_parser.add_argument("--framework", default=None, help="主要框架")
    create_parser.set_defaults(func=create_project)

    requirement_parser = subparsers.add_parser(
        "requirement", aliases=["requirements"], help="需求管理"
    )
    requirement_subparsers = requirement_parser.add_subparsers(dest="action", required=True)

    requirement_list_parser = requirement_subparsers.add_parser("list", help="查看需求列表")
    requirement_list_parser.add_argument("--project-id", default=None, help="按项目过滤")
    requirement_list_parser.set_defaults(func=list_requirements)

    requirement_create_parser = requirement_subparsers.add_parser("create", help="创建需求")
    requirement_create_parser.add_argument("--project-id", required=True, help="项目 ID")
    requirement_create_parser.add_argument("--title", required=True, help="需求标题")
    requirement_create_parser.add_argument("--raw-requirement", required=True, help="自然语言需求")
    requirement_create_parser.add_argument("--priority", type=int, default=0, help="优先级")
    requirement_create_parser.set_defaults(func=create_requirement)

    requirement_show_parser = requirement_subparsers.add_parser("show", help="查看需求详情")
    requirement_show_parser.add_argument("requirement_id", help="需求 ID")
    requirement_show_parser.set_defaults(func=show_requirement)

    dag_parser = subparsers.add_parser("dag", help="DAG 管理")
    dag_subparsers = dag_parser.add_subparsers(dest="action", required=True)

    dag_generate_parser = dag_subparsers.add_parser("generate", help="生成需求 DAG")
    dag_generate_parser.add_argument("requirement_id", help="需求 ID")
    dag_generate_parser.set_defaults(func=generate_dag)

    dag_show_parser = dag_subparsers.add_parser("show", help="查看需求 DAG")
    dag_show_parser.add_argument("requirement_id", help="需求 ID")
    dag_show_parser.set_defaults(func=show_dag)

    run_parser = subparsers.add_parser("run", aliases=["runs"], help="Agent Run 管理")
    run_subparsers = run_parser.add_subparsers(dest="action", required=True)

    run_start_parser = run_subparsers.add_parser("start", help="启动 Agent Run")
    run_start_parser.add_argument("requirement_id", help="需求 ID")
    run_start_parser.add_argument("--dag-node-id", default=None, help="指定 DAG 节点 ID")
    run_start_parser.set_defaults(func=start_run)

    run_list_parser = run_subparsers.add_parser("list", help="查看 Agent Run 列表")
    run_list_parser.add_argument("--requirement-id", default=None, help="按需求过滤")
    run_list_parser.set_defaults(func=list_runs)

    run_show_parser = run_subparsers.add_parser("show", help="查看 Agent Run 详情")
    run_show_parser.add_argument("run_id", help="Agent Run ID")
    run_show_parser.set_defaults(func=show_run)

    tools_parser = subparsers.add_parser("tools", aliases=["tool"], help="工具与策略管理")
    tools_subparsers = tools_parser.add_subparsers(dest="action", required=True)

    tools_seed_parser = tools_subparsers.add_parser("seed", help="初始化默认工具")
    tools_seed_parser.set_defaults(func=seed_tools)

    tools_list_parser = tools_subparsers.add_parser("list", help="查看工具列表")
    tools_list_parser.set_defaults(func=list_tools)

    policy_check_parser = tools_subparsers.add_parser("check", help="执行策略检查")
    policy_check_parser.add_argument(
        "action_type",
        choices=["file.read", "file.write", "code.search", "shell.run", "test.run", "file.delete"],
        help="动作类型",
    )
    policy_check_parser.add_argument("--project-id", default=None, help="项目 ID")
    policy_check_parser.add_argument("--command", default="", help="待检查命令")
    policy_check_parser.add_argument("--path", default="", help="待检查文件路径")
    policy_check_parser.set_defaults(func=check_policy)

    tool_call_parser = tools_subparsers.add_parser("call", help="执行一次真实工具调用")
    tool_call_parser.add_argument("tool_name", help="工具名称，如 code.search、git.diff")
    tool_call_parser.add_argument("--project-id", default=None, help="项目 ID")
    tool_call_parser.add_argument("--run-id", default=None, help="Agent Run ID")
    tool_call_parser.add_argument("--payload", default="{}", help="JSON 格式工具输入")
    tool_call_parser.set_defaults(func=call_tool)

    tool_calls_parser = tools_subparsers.add_parser("calls", help="查看工具调用日志")
    tool_calls_parser.add_argument("--project-id", default=None, help="项目 ID")
    tool_calls_parser.add_argument("--run-id", default=None, help="Agent Run ID")
    tool_calls_parser.set_defaults(func=list_tool_calls)

    patch_parser = tools_subparsers.add_parser("patch", help="补丁预览与确认应用")
    patch_subparsers = patch_parser.add_subparsers(dest="patch_action", required=True)

    patch_preview_parser = patch_subparsers.add_parser("preview", help="预览文件补丁 Diff")
    patch_preview_parser.add_argument("--project-id", required=True, help="项目 ID")
    patch_preview_parser.add_argument("--path", required=True, help="项目内文件路径")
    patch_preview_parser.add_argument("--new-content", required=True, help="新文件内容")
    patch_preview_parser.set_defaults(func=preview_patch)

    patch_apply_parser = patch_subparsers.add_parser("apply", help="确认应用文件补丁")
    patch_apply_parser.add_argument("--project-id", required=True, help="项目 ID")
    patch_apply_parser.add_argument("--path", required=True, help="项目内文件路径")
    patch_apply_parser.add_argument("--new-content", required=True, help="新文件内容")
    patch_apply_parser.add_argument("--expected-original-content", default=None, help="可选的原始内容冲突检查")
    patch_apply_parser.add_argument("--run-id", default=None, help="Agent Run ID")
    patch_apply_parser.add_argument("--validation-command", default=None, help="应用补丁后执行的可选验证命令")
    patch_apply_parser.set_defaults(func=apply_patch)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
