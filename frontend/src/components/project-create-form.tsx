"use client";

import { useState } from "react";
import { apiPost } from "@/lib/api";
import type { Project } from "@/lib/types";

export function ProjectCreateForm({ onCreated }: { onCreated: (project: Project) => void }) {
  const [name, setName] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [localPath, setLocalPath] = useState("");
  const [language, setLanguage] = useState("");
  const [framework, setFramework] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const project = await apiPost<Project>("/api/projects", {
        name,
        display_name: displayName || null,
        local_path: localPath,
        language: language || null,
        framework: framework || null,
      });
      onCreated(project);
      setName("");
      setDisplayName("");
      setLocalPath("");
      setLanguage("");
      setFramework("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建项目失败");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="grid gap-3 rounded-2xl border border-slate-800 bg-slate-950 p-5">
      <h2 className="text-lg font-medium">创建项目</h2>
      <input className="input" placeholder="项目标识，例如 admin-dashboard" value={name} onChange={(e) => setName(e.target.value)} required />
      <input className="input" placeholder="显示名称" value={displayName} onChange={(e) => setDisplayName(e.target.value)} />
      <input className="input" placeholder="本地路径" value={localPath} onChange={(e) => setLocalPath(e.target.value)} required />
      <div className="grid gap-3 md:grid-cols-2">
        <input className="input" placeholder="语言，例如 TypeScript" value={language} onChange={(e) => setLanguage(e.target.value)} />
        <input className="input" placeholder="框架，例如 Next.js" value={framework} onChange={(e) => setFramework(e.target.value)} />
      </div>
      {error ? <p className="text-sm text-rose-300">{error}</p> : null}
      <button disabled={submitting} className="rounded-lg bg-blue-500 px-4 py-2 font-medium text-white disabled:opacity-60">
        {submitting ? "创建中..." : "创建项目"}
      </button>
    </form>
  );
}
