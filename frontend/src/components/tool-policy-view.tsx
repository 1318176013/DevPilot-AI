"use client";

import { useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import type { PolicyCheckResponse, Project, ToolDefinition } from "@/lib/types";

export function ToolPolicyView({ projects }: { projects: Project[] }) {
  const [tools, setTools] = useState<ToolDefinition[]>([]);
  const [projectId, setProjectId] = useState(projects[0]?.id ?? "");
  const [command, setCommand] = useState("npm run lint");
  const [path, setPath] = useState(projects[0]?.local_path ?? "");
  const [policyResult, setPolicyResult] = useState<PolicyCheckResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function seedTools() {
    setLoading(true);
    setError(null);
    try {
      setTools(await apiPost<ToolDefinition[]>("/api/tools/defaults"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "初始化工具失败");
    } finally {
      setLoading(false);
    }
  }

  async function loadTools() {
    setLoading(true);
    setError(null);
    try {
      setTools(await apiGet<ToolDefinition[]>("/api/tools"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载工具失败");
    } finally {
      setLoading(false);
    }
  }

  async function checkCommand() {
    setLoading(true);
    setError(null);
    try {
      setPolicyResult(await apiPost<PolicyCheckResponse>("/api/tools/policy/check", {
        project_id: projectId || null,
        action_type: "shell.run",
        payload: { command },
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "策略检查失败");
    } finally {
      setLoading(false);
    }
  }

  async function checkPath() {
    setLoading(true);
    setError(null);
    try {
      setPolicyResult(await apiPost<PolicyCheckResponse>("/api/tools/policy/check", {
        project_id: projectId || null,
        action_type: "file.write",
        payload: { path },
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "策略检查失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-950 p-5 lg:col-span-2">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-lg font-medium">工具与策略</h2>
          <p className="mt-1 text-sm text-slate-500">管理 MVP 基础工具，并验证命令白名单和项目路径约束。</p>
        </div>
        <div className="flex gap-2">
          <button disabled={loading} className="rounded-lg bg-slate-800 px-4 py-2 text-sm font-medium text-white disabled:opacity-60" onClick={loadTools}>查看工具</button>
          <button disabled={loading} className="rounded-lg bg-blue-500 px-4 py-2 text-sm font-medium text-white disabled:opacity-60" onClick={seedTools}>初始化工具</button>
        </div>
      </div>

      {error ? <p className="mt-4 text-sm text-rose-300">{error}</p> : null}
      {policyResult ? (
        <p className={`mt-4 text-sm ${policyResult.allowed ? "text-emerald-300" : "text-rose-300"}`}>
          {policyResult.allowed ? "允许执行" : `已拦截：${policyResult.reason}`}
        </p>
      ) : null}

      <div className="mt-5 grid gap-4 lg:grid-cols-3">
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-4 lg:col-span-2">
          <h3 className="font-medium">工具列表</h3>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            {tools.length === 0 ? <p className="text-sm text-slate-500">暂无工具，请初始化或查看工具。</p> : null}
            {tools.map((tool) => (
              <div key={tool.id} className="rounded-lg bg-slate-950 p-3">
                <div className="text-sm font-medium">{tool.name}</div>
                <div className="mt-1 text-xs text-blue-300">{tool.category} · {tool.is_enabled ? "enabled" : "disabled"}</div>
                <p className="mt-2 text-xs text-slate-400">{tool.description}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
          <h3 className="font-medium">策略检查</h3>
          <select
            className="input mt-3 w-full"
            value={projectId}
            onChange={(event) => {
              const nextProject = projects.find((project) => project.id === event.target.value);
              setProjectId(event.target.value);
              setPath(nextProject?.local_path ?? "");
            }}
          >
            <option value="">全局策略</option>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>{project.display_name || project.name}</option>
            ))}
          </select>
          <input className="input mt-3 w-full" value={command} onChange={(event) => setCommand(event.target.value)} placeholder="命令，例如 npm run lint" />
          <button disabled={loading} className="mt-2 w-full rounded-lg bg-emerald-500 px-4 py-2 text-sm font-medium text-white disabled:opacity-60" onClick={checkCommand}>检查命令</button>
          <input className="input mt-3 w-full" value={path} onChange={(event) => setPath(event.target.value)} placeholder="文件路径" />
          <button disabled={loading} className="mt-2 w-full rounded-lg bg-emerald-500 px-4 py-2 text-sm font-medium text-white disabled:opacity-60" onClick={checkPath}>检查路径</button>
        </div>
      </div>
    </section>
  );
}
