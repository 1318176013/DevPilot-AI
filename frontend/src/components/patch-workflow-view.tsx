"use client";

import { useEffect, useMemo, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import type { AgentRun, PatchApplyResponse, PatchPreviewResponse, Project, Requirement } from "@/lib/types";

export function PatchWorkflowView({ projects, requirements }: { projects: Project[]; requirements: Requirement[] }) {
  const [projectId, setProjectId] = useState(projects[0]?.id ?? "");
  const projectRequirements = useMemo(
    () => requirements.filter((requirement) => requirement.project_id === projectId),
    [projectId, requirements],
  );
  const [requirementId, setRequirementId] = useState(projectRequirements[0]?.id ?? "");
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [runId, setRunId] = useState("");
  const [path, setPath] = useState(".devpilot/patch-preview.md");
  const [newContent, setNewContent] = useState("# DevPilot Patch Preview\n\n在这里输入希望写入文件的新内容。\n");
  const [preview, setPreview] = useState<PatchPreviewResponse | null>(null);
  const [validationCommand, setValidationCommand] = useState("");
  const [applyResult, setApplyResult] = useState<PatchApplyResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!projects.some((project) => project.id === projectId)) {
      setProjectId(projects[0]?.id ?? "");
    }
  }, [projectId, projects]);

  useEffect(() => {
    if (!projectRequirements.some((requirement) => requirement.id === requirementId)) {
      setRequirementId(projectRequirements[0]?.id ?? "");
      setRuns([]);
      setRunId("");
    }
  }, [projectRequirements, requirementId]);


  async function loadRuns() {
    if (!requirementId) return;
    setLoading(true);
    setError(null);
    try {
      const result = await apiGet<AgentRun[]>(`/api/agent-runs?requirement_id=${requirementId}`);
      setRuns(result);
      setRunId((current) => result.some((run) => run.id === current) ? current : result[0]?.id ?? "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载 Agent Run 失败");
    } finally {
      setLoading(false);
    }
  }

  async function previewPatch() {
    if (!projectId || !path) return;
    setLoading(true);
    setError(null);
    setApplyResult(null);
    try {
      setPreview(await apiPost<PatchPreviewResponse>("/api/tools/patch/preview", {
        project_id: projectId,
        path,
        new_content: newContent,
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "补丁预览失败");
    } finally {
      setLoading(false);
    }
  }

  async function applyPatch() {
    if (!projectId || !preview) return;
    setLoading(true);
    setError(null);
    try {
      setApplyResult(await apiPost<PatchApplyResponse>("/api/tools/patch/apply", {
        project_id: projectId,
        path: preview.path,
        new_content: preview.new_content,
        expected_original_content: preview.original_content,
        run_id: runId || null,
        validation_command: validationCommand || null,
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "应用补丁失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-950 p-5 lg:col-span-2">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-lg font-medium">补丁预览与确认应用</h2>
          <p className="mt-1 text-sm text-slate-500">先生成 Diff 预览，再通过 Policy Guard 确认写入项目文件。</p>
        </div>
        <div className="flex gap-2">
          <button disabled={!projectId || loading} className="rounded-lg bg-blue-500 px-4 py-2 text-sm font-medium text-white disabled:opacity-60" onClick={previewPatch}>预览 Diff</button>
          <button disabled={!preview?.has_changes || loading} className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-medium text-white disabled:opacity-60" onClick={applyPatch}>确认应用</button>
        </div>
      </div>

      {projects.length === 0 ? <p className="mt-4 text-sm text-slate-500">暂无项目，请先创建项目。</p> : null}
      {error ? <p className="mt-4 text-sm text-rose-300">{error}</p> : null}
      {loading ? <p className="mt-4 text-sm text-slate-400">处理中...</p> : null}
      {applyResult ? (
        <div className="mt-4 space-y-2">
          <p className={applyResult.write_call.status === "success" ? "text-sm text-emerald-300" : "text-sm text-amber-300"}>
            应用结果：{applyResult.write_call.status}{applyResult.write_call.error_message ? ` · ${applyResult.write_call.error_message}` : ""}
          </p>
          {applyResult.audit_action ? (
            <div className="rounded-lg border border-emerald-500/40 bg-emerald-950/30 p-3 text-sm text-slate-300">
              <div className="text-xs text-emerald-300">审计动作 #{applyResult.audit_action.sequence} · {applyResult.audit_action.status}</div>
              <div className="mt-1">{applyResult.audit_action.message}</div>
            </div>
          ) : runId ? (
            <p className="text-xs text-amber-300">未生成审计动作，请确认关联的 Agent Run 是否存在。</p>
          ) : null}
        </div>
      ) : null}

      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        <div className="space-y-3 rounded-xl border border-slate-800 bg-slate-900 p-4">
          <h3 className="font-medium">补丁输入</h3>
          <select className="input w-full" value={projectId} onChange={(event) => setProjectId(event.target.value)}>
            <option value="" disabled>选择项目</option>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>{project.display_name || project.name}</option>
            ))}
          </select>
          <div className="grid gap-2 md:grid-cols-[1fr_auto]">
            <select
              className="input w-full"
              value={requirementId}
              onChange={(event) => {
                setRequirementId(event.target.value);
                setRuns([]);
                setRunId("");
              }}
            >
              <option value="" disabled>选择需求以加载运行</option>
              {projectRequirements.map((requirement) => (
                <option key={requirement.id} value={requirement.id}>{requirement.title}</option>
              ))}
            </select>
            <button disabled={!requirementId || loading} className="rounded-lg bg-slate-800 px-4 py-2 text-sm font-medium text-white disabled:opacity-60" onClick={loadRuns}>加载运行</button>
          </div>
          <select className="input w-full" value={runId} onChange={(event) => setRunId(event.target.value)}>
            <option value="">不关联 Agent Run</option>
            {runs.map((run) => (
              <option key={run.id} value={run.id}>{run.id.slice(0, 8)} · {run.status}</option>
            ))}
          </select>
          <p className="text-xs text-slate-500">关联的 Agent Run 必须来自当前项目下的需求，否则后端会拒绝补丁应用。</p>
          <input className="input w-full" value={path} onChange={(event) => setPath(event.target.value)} placeholder="项目内文件路径" />
          <input className="input w-full" value={validationCommand} onChange={(event) => setValidationCommand(event.target.value)} placeholder="可选验证命令，如 npm run lint" />
          <textarea className="input min-h-64 w-full font-mono text-xs" value={newContent} onChange={(event) => setNewContent(event.target.value)} placeholder="新文件内容" />
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
          <div className="flex items-center justify-between gap-3">
            <h3 className="font-medium">Diff 预览</h3>
            {preview ? <span className="text-xs text-slate-500">{preview.has_changes ? "有变更" : "无变更"}</span> : null}
          </div>
          {preview ? (
            <pre className="mt-3 max-h-96 overflow-auto rounded-lg bg-slate-950 p-3 text-xs text-slate-300">
              {preview.diff || "无差异"}
            </pre>
          ) : (
            <p className="mt-3 text-sm text-slate-500">输入目标路径和新内容后，点击“预览 Diff”。</p>
          )}
        </div>
      </div>
      {applyResult ? (
        <div className="mt-5 grid gap-4 lg:grid-cols-2">
          <ToolCallResult title="应用后工作区 Diff" call={applyResult.git_diff_call} emptyText="暂无应用后 Diff。" />
          <ToolCallResult title="验证命令结果" call={applyResult.validation_call} emptyText="未配置验证命令。" />
        </div>
      ) : null}
    </section>
  );
}

function ToolCallResult({ title, call, emptyText }: { title: string; call: PatchApplyResponse["git_diff_call"]; emptyText: string }) {
  const output = call?.output_payload;
  const stdout = typeof output?.stdout === "string" ? output.stdout : "";
  const stderr = typeof output?.stderr === "string" ? output.stderr : "";

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
      <div className="flex items-center justify-between gap-3">
        <h3 className="font-medium">{title}</h3>
        {call ? <span className={call.status === "success" ? "text-xs text-emerald-300" : "text-xs text-amber-300"}>{call.status}</span> : null}
      </div>
      {call ? (
        <pre className="mt-3 max-h-80 overflow-auto rounded-lg bg-slate-950 p-3 text-xs text-slate-300">
          {stdout || stderr || call.error_message || "无输出"}
        </pre>
      ) : (
        <p className="mt-3 text-sm text-slate-500">{emptyText}</p>
      )}
    </div>
  );
}
