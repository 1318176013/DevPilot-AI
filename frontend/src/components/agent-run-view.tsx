"use client";

import { useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import type { AgentRun, AgentRunDetail, Requirement, ToolCallLog } from "@/lib/types";

export function AgentRunView({ requirements }: { requirements: Requirement[] }) {
  const [selectedRequirementId, setSelectedRequirementId] = useState(requirements[0]?.id ?? "");
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [activeRun, setActiveRun] = useState<AgentRunDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadRuns(requirementId = selectedRequirementId) {
    if (!requirementId) return;
    setLoading(true);
    setError(null);
    try {
      const result = await apiGet<AgentRun[]>(`/api/agent-runs?requirement_id=${requirementId}`);
      setRuns(result);
      setActiveRun(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载 Agent Run 失败");
    } finally {
      setLoading(false);
    }
  }

  async function startRun() {
    if (!selectedRequirementId) return;
    setLoading(true);
    setError(null);
    try {
      const run = await apiPost<AgentRunDetail>("/api/agent-runs", {
        requirement_id: selectedRequirementId,
      });
      setActiveRun(run);
      setRuns((items) => [run, ...items.filter((item) => item.id !== run.id)]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "启动 Agent Run 失败");
    } finally {
      setLoading(false);
    }
  }

  async function showRun(runId: string) {
    setLoading(true);
    setError(null);
    try {
      setActiveRun(await apiGet<AgentRunDetail>(`/api/agent-runs/${runId}`));
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载运行详情失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-950 p-5 lg:col-span-2">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-lg font-medium">Agent 运行监控</h2>
          <p className="mt-1 text-sm text-slate-500">启动 Lightweight Agent，查看动作日志和真实工具调用记录。</p>
        </div>
        <div className="flex flex-col gap-2 md:flex-row">
          <select
            className="input min-w-64"
            value={selectedRequirementId}
            onChange={(event) => {
              setSelectedRequirementId(event.target.value);
              setRuns([]);
              setActiveRun(null);
              setError(null);
            }}
          >
            <option value="" disabled>选择需求</option>
            {requirements.map((requirement) => (
              <option key={requirement.id} value={requirement.id}>{requirement.title}</option>
            ))}
          </select>
          <button disabled={!selectedRequirementId || loading} className="rounded-lg bg-slate-800 px-4 py-2 text-sm font-medium text-white disabled:opacity-60" onClick={() => loadRuns()}>
            查看运行
          </button>
          <button disabled={!selectedRequirementId || loading} className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-medium text-white disabled:opacity-60" onClick={startRun}>
            启动 Agent
          </button>
        </div>
      </div>

      {requirements.length === 0 ? <p className="mt-4 text-sm text-slate-500">暂无需求，请先创建需求。</p> : null}
      {error ? <p className="mt-4 text-sm text-rose-300">{error}</p> : null}
      {loading ? <p className="mt-4 text-sm text-slate-400">处理中...</p> : null}

      <div className="mt-5 grid gap-4 lg:grid-cols-3">
        <div className="space-y-3">
          {runs.length === 0 ? <p className="text-sm text-slate-500">暂无运行记录</p> : null}
          {runs.map((run) => (
            <button
              key={run.id}
              className="block w-full rounded-xl border border-slate-800 bg-slate-900 p-4 text-left hover:border-blue-400"
              onClick={() => showRun(run.id)}
            >
              <div className="text-sm font-medium">{run.id.slice(0, 8)}</div>
              <div className="mt-2 text-xs text-emerald-300">{run.status}</div>
              <div className="mt-2 line-clamp-2 text-xs text-slate-400">{run.summary || "无摘要"}</div>
            </button>
          ))}
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900 p-4 lg:col-span-2">
          <h3 className="font-medium">运行详情</h3>
          {activeRun ? (
            <div className="mt-4 space-y-3">
              <div className="rounded-lg bg-slate-950 p-3 text-sm text-slate-300">{activeRun.summary}</div>
              <div className="space-y-2">
                <div className="text-xs font-medium uppercase tracking-wide text-slate-500">动作日志</div>
                {activeRun.actions.map((action) => (
                  <div key={action.id} className={action.action_type === "patch.apply" ? "rounded-lg border border-emerald-500/40 bg-emerald-950/30 p-3" : "rounded-lg bg-slate-950 p-3"}>
                    <div className={action.action_type === "patch.apply" ? "text-xs text-emerald-300" : "text-xs text-blue-300"}>#{action.sequence} · {action.action_type} · {action.status}</div>
                    <div className="mt-1 text-sm text-slate-300">{action.message}</div>
                    {action.action_type === "patch.apply" ? (
                      <pre className="mt-2 max-h-32 overflow-auto rounded bg-slate-950 p-2 text-xs text-slate-400">
                        {JSON.stringify(action.payload, null, 2)}
                      </pre>
                    ) : null}
                  </div>
                ))}
              </div>

              <div className="space-y-2">
                <div className="text-xs font-medium uppercase tracking-wide text-slate-500">工具调用</div>
                {activeRun.tool_calls.length === 0 ? <p className="text-sm text-slate-500">暂无工具调用记录</p> : null}
                {activeRun.tool_calls.map((call) => (
                  <ToolCallCard key={call.id} call={call} />
                ))}
              </div>
            </div>
          ) : (
            <p className="mt-4 text-sm text-slate-500">请选择或启动一次 Agent Run。</p>
          )}
        </div>
      </div>
    </section>
  );
}

function ToolCallCard({ call }: { call: ToolCallLog }) {
  return (
    <div className="rounded-lg bg-slate-950 p-3">
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <span className="text-purple-300">{call.tool_name}</span>
        <span className="text-slate-600">·</span>
        <span className={call.status === "success" ? "text-emerald-300" : "text-amber-300"}>{call.status}</span>
      </div>
      {call.error_message ? <div className="mt-2 text-xs text-rose-300">{call.error_message}</div> : null}
      <pre className="mt-2 max-h-40 overflow-auto rounded bg-slate-900 p-2 text-xs text-slate-400">
        {JSON.stringify(summarizeToolCall(call), null, 2)}
      </pre>
    </div>
  );
}

function summarizeToolCall(call: ToolCallLog) {
  return {
    input: call.input_payload,
    output: {
      command: call.output_payload.command,
      returncode: call.output_payload.returncode,
      path: call.output_payload.path,
      size: call.output_payload.size,
      truncated: call.output_payload.truncated,
    },
  };
}
