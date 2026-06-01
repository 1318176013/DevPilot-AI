import { WorkspaceClient } from "@/components/workspace-client";
import { API_BASE_URL, apiGet } from "@/lib/api";
import type { Project, Requirement } from "@/lib/types";

async function getReadyStatus() {
  try {
    return await apiGet<{
      status: string;
      checks: Record<string, boolean>;
    }>("/ready");
  } catch {
    return null;
  }
}

async function getProjects() {
  try {
    return await apiGet<Project[]>("/api/projects");
  } catch {
    return [];
  }
}

async function getRequirements() {
  try {
    return await apiGet<Requirement[]>("/api/requirements");
  } catch {
    return [];
  }
}

export default async function HomePage() {
  const [ready, projects, requirements] = await Promise.all([
    getReadyStatus(),
    getProjects(),
    getRequirements(),
  ]);
  const checks = ready?.checks ?? {};

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-8 text-slate-100">
      <section className="mx-auto max-w-6xl">
        <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-8 shadow-2xl shadow-blue-950/30">
          <p className="mb-3 text-sm font-medium text-blue-300">DevPilot AI</p>
          <h1 className="text-4xl font-semibold tracking-tight">AI 自动化开发团队控制台</h1>
          <p className="mt-4 max-w-2xl text-slate-400">
            当前 Sprint 目标：项目、模型、需求基础能力。现在可以创建项目和自然语言需求。
          </p>

          <div className="mt-8 grid gap-4 md:grid-cols-4">
            <StatusCard label="Backend" ok={Boolean(ready)} value={ready?.status ?? "offline"} />
            <StatusCard label="PostgreSQL" ok={Boolean(checks.postgres)} />
            <StatusCard label="Redis" ok={Boolean(checks.redis)} />
            <StatusCard label="Qdrant" ok={Boolean(checks.qdrant)} />
          </div>

          <div className="mt-8 rounded-2xl border border-slate-800 bg-slate-950 p-5">
            <h2 className="text-lg font-medium">后端地址</h2>
            <code className="mt-3 block rounded-lg bg-slate-900 px-4 py-3 text-sm text-blue-200">
              {API_BASE_URL}
            </code>
          </div>

          <WorkspaceClient initialProjects={projects} initialRequirements={requirements} />
        </div>
      </section>
    </main>
  );
}

function StatusCard({ label, ok, value }: { label: string; ok: boolean; value?: string }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5">
      <div className="text-sm text-slate-400">{label}</div>
      <div className="mt-3 flex items-center gap-2">
        <span className={`h-2.5 w-2.5 rounded-full ${ok ? "bg-emerald-400" : "bg-rose-400"}`} />
        <span className="font-medium">{value ?? (ok ? "ok" : "failed")}</span>
      </div>
    </div>
  );
}

