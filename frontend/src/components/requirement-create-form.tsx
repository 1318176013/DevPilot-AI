"use client";

import { useEffect, useState } from "react";
import { apiPost } from "@/lib/api";
import type { Project, Requirement } from "@/lib/types";

export function RequirementCreateForm({
  projects,
  onCreated,
}: {
  projects: Project[];
  onCreated: (requirement: Requirement) => void;
}) {
  const [projectId, setProjectId] = useState(projects[0]?.id ?? "");
  const [title, setTitle] = useState("");
  const [rawRequirement, setRawRequirement] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!projects.some((project) => project.id === projectId)) {
      setProjectId(projects[0]?.id ?? "");
    }
  }, [projectId, projects]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const requirement = await apiPost<Requirement>("/api/requirements", {
        project_id: projectId,
        title,
        raw_requirement: rawRequirement,
      });
      onCreated(requirement);
      setTitle("");
      setRawRequirement("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建需求失败");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="grid gap-3 rounded-2xl border border-slate-800 bg-slate-950 p-5">
      <h2 className="text-lg font-medium">创建需求</h2>
      <select className="input" value={projectId} onChange={(e) => setProjectId(e.target.value)} required>
        <option value="" disabled>选择项目</option>
        {projects.map((project) => (
          <option key={project.id} value={project.id}>{project.display_name || project.name}</option>
        ))}
      </select>
      <input className="input" placeholder="需求标题" value={title} onChange={(e) => setTitle(e.target.value)} required />
      <textarea className="input min-h-28" placeholder="自然语言需求描述" value={rawRequirement} onChange={(e) => setRawRequirement(e.target.value)} required />
      {error ? <p className="text-sm text-rose-300">{error}</p> : null}
      <button disabled={submitting || projects.length === 0} className="rounded-lg bg-emerald-500 px-4 py-2 font-medium text-white disabled:opacity-60">
        {submitting ? "创建中..." : "创建需求"}
      </button>
    </form>
  );
}
