export type Project = {
  id: string;
  name: string;
  display_name: string | null;
  local_path: string;
  repo_url: string | null;
  default_branch: string;
  language: string | null;
  framework: string | null;
  description: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type Requirement = {
  id: string;
  project_id: string;
  title: string;
  raw_requirement: string;
  structured_requirement: Record<string, unknown>;
  status: string;
  priority: number;
  created_at: string;
  updated_at: string;
};
