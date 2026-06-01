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
    project = request_json("POST", "/api/projects", payload)
    print(json.dumps(project, ensure_ascii=False, indent=2))


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

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
