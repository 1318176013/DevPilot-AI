"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPatch, apiPost } from "@/lib/api";
import type { Dag, DagGenerateResponse, DagNode, Requirement } from "@/lib/types";

const NODE_STATUSES = ["pending", "running", "success", "failed", "blocked"];

export function DagView({ requirements }: { requirements: Requirement[] }) {
  const [selectedRequirementId, setSelectedRequirementId] = useState(requirements[0]?.id ?? "");
  const [dag, setDag] = useState<Dag | null>(null);
  const [loading, setLoading] = useState(false);
  const [updatingNodeId, setUpdatingNodeId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!requirements.some((requirement) => requirement.id === selectedRequirementId)) {
      setSelectedRequirementId(requirements[0]?.id ?? "");
      setDag(null);
      setError(null);
    }
  }, [requirements, selectedRequirementId]);

  async function loadDag(requirementId = selectedRequirementId) {
    if (!requirementId) return;
    setLoading(true);
    setError(null);
    try {
      const result = await apiGet<Dag>(`/api/requirements/${requirementId}/dag`);
      setDag(result);
    } catch (err) {
      setDag(null);
      setError(err instanceof Error ? err.message : "加载 DAG 失败");
    } finally {
      setLoading(false);
    }
  }

  async function generateDag() {
    if (!selectedRequirementId) return;
    setLoading(true);
    setError(null);
    try {
      const result = await apiPost<DagGenerateResponse>(
        `/api/requirements/${selectedRequirementId}/dag/generate`,
      );
      setDag(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "生成 DAG 失败");
    } finally {
      setLoading(false);
    }
  }

  async function updateNodeStatus(nodeId: string, status: string) {
    setUpdatingNodeId(nodeId);
    setError(null);
    try {
      const updatedNode = await apiPatch<DagNode>(`/api/dag/nodes/${nodeId}/status`, { status });
      setDag((current) => current
        ? {
            ...current,
            nodes: current.nodes.map((node) => (node.id === nodeId ? updatedNode : node)),
          }
        : current,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "更新节点状态失败");
    } finally {
      setUpdatingNodeId(null);
    }
  }

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-950 p-5 lg:col-span-2">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-lg font-medium">DAG 任务编排</h2>
          <p className="mt-1 text-sm text-slate-500">基于结构化需求生成 analysis → review 串行节点。</p>
        </div>
        <div className="flex flex-col gap-2 md:flex-row">
          <select
            className="input min-w-64"
            value={selectedRequirementId}
            onChange={(event) => {
              setSelectedRequirementId(event.target.value);
              setDag(null);
              setError(null);
            }}
          >
            <option value="" disabled>选择需求</option>
            {requirements.map((requirement) => (
              <option key={requirement.id} value={requirement.id}>{requirement.title}</option>
            ))}
          </select>
          <button disabled={!selectedRequirementId || loading} className="rounded-lg bg-slate-800 px-4 py-2 text-sm font-medium text-white disabled:opacity-60" onClick={() => loadDag()}>
            查看 DAG
          </button>
          <button disabled={!selectedRequirementId || loading} className="rounded-lg bg-blue-500 px-4 py-2 text-sm font-medium text-white disabled:opacity-60" onClick={generateDag}>
            生成 DAG
          </button>
        </div>
      </div>

      {requirements.length === 0 ? <p className="mt-4 text-sm text-slate-500">暂无需求，请先创建需求。</p> : null}
      {error ? <p className="mt-4 text-sm text-rose-300">{error}</p> : null}
      {loading ? <p className="mt-4 text-sm text-slate-400">处理中...</p> : null}

      <div className="mt-5 grid gap-3 md:grid-cols-5">
        {dag?.nodes.map((node, index) => (
          <div key={node.id} className="rounded-xl border border-slate-800 bg-slate-900 p-4">
            <div className="text-xs text-blue-300">Step {index + 1} · {node.node_type}</div>
            <div className="mt-2 font-medium">{node.label}</div>
            <p className="mt-2 min-h-16 text-sm text-slate-400">{node.description}</p>
            <select
              className="input mt-3 w-full text-xs"
              value={node.status}
              disabled={updatingNodeId === node.id}
              onChange={(event) => updateNodeStatus(node.id, event.target.value)}
            >
              {NODE_STATUSES.map((status) => (
                <option key={status} value={status}>{status}</option>
              ))}
            </select>
          </div>
        ))}
      </div>

      {dag && dag.nodes.length === 0 ? <p className="mt-4 text-sm text-slate-500">暂无 DAG 节点，请先生成。</p> : null}
      {dag && dag.edges.length > 0 ? (
        <div className="mt-5 rounded-xl bg-slate-900 p-4 text-sm text-slate-400">
          依赖边：{dag.edges.map((edge) => `${edge.source_node_id.slice(0, 8)} → ${edge.target_node_id.slice(0, 8)}`).join("，")}
        </div>
      ) : null}
    </section>
  );
}
