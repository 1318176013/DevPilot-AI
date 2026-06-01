"use client";

import { useState } from "react";
import { AgentRunView } from "@/components/agent-run-view";
import { DagView } from "@/components/dag-view";
import { PatchWorkflowView } from "@/components/patch-workflow-view";
import { ProjectCreateForm } from "@/components/project-create-form";
import { RequirementCreateForm } from "@/components/requirement-create-form";
import { ToolPolicyView } from "@/components/tool-policy-view";
import type { Project, Requirement } from "@/lib/types";

export function WorkspaceClient({
  initialProjects,
  initialRequirements,
}: {
  initialProjects: Project[];
  initialRequirements: Requirement[];
}) {
  const [projects, setProjects] = useState(initialProjects);
  const [requirements, setRequirements] = useState(initialRequirements);

  return (
    <div className="mt-8 grid gap-6 lg:grid-cols-2">
      <ProjectCreateForm onCreated={(project) => setProjects((items) => [project, ...items])} />
      <RequirementCreateForm
        projects={projects}
        onCreated={(requirement) => setRequirements((items) => [requirement, ...items])}
      />

      <section className="rounded-2xl border border-slate-800 bg-slate-950 p-5">
        <h2 className="text-lg font-medium">项目列表</h2>
        <div className="mt-4 space-y-3">
          {projects.length === 0 ? <p className="text-sm text-slate-500">暂无项目</p> : null}
          {projects.map((project) => (
            <div key={project.id} className="rounded-xl bg-slate-900 p-4">
              <div className="font-medium">{project.display_name || project.name}</div>
              <div className="mt-1 text-sm text-slate-400">{project.local_path}</div>
              <div className="mt-2 text-xs text-blue-300">{project.language || "unknown"} / {project.framework || "unknown"}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-2xl border border-slate-800 bg-slate-950 p-5">
        <h2 className="text-lg font-medium">需求列表</h2>
        <div className="mt-4 space-y-3">
          {requirements.length === 0 ? <p className="text-sm text-slate-500">暂无需求</p> : null}
          {requirements.map((requirement) => (
            <div key={requirement.id} className="rounded-xl bg-slate-900 p-4">
              <div className="font-medium">{requirement.title}</div>
              <div className="mt-1 line-clamp-2 text-sm text-slate-400">{requirement.raw_requirement}</div>
              <div className="mt-2 text-xs text-emerald-300">{requirement.status}</div>
            </div>
          ))}
        </div>
      </section>

      <DagView requirements={requirements} />
      <AgentRunView requirements={requirements} />
      <ToolPolicyView projects={projects} />
      <PatchWorkflowView projects={projects} requirements={requirements} />
    </div>
  );
}
