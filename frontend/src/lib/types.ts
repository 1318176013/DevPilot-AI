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

export type DagNode = {
  id: string;
  requirement_id: string;
  node_type: string;
  label: string;
  description: string | null;
  config: Record<string, unknown>;
  model_policy: Record<string, unknown>;
  position_x: number;
  position_y: number;
  status: string;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
};

export type DagEdge = {
  id: string;
  requirement_id: string;
  source_node_id: string;
  target_node_id: string;
  edge_type: string;
  condition_expr: string | null;
};

export type Dag = {
  requirement_id: string;
  nodes: DagNode[];
  edges: DagEdge[];
};

export type DagGenerateResponse = Dag & {
  generated: boolean;
};

export type AgentAction = {
  id: string;
  run_id: string;
  sequence: number;
  action_type: string;
  message: string;
  payload: Record<string, unknown>;
  status: string;
  created_at: string;
};

export type AgentRun = {
  id: string;
  requirement_id: string;
  dag_node_id: string | null;
  backend: string;
  status: string;
  summary: string | null;
  result: Record<string, unknown>;
  error_message: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
};

export type ToolCallLog = {
  id: string;
  run_id: string | null;
  project_id: string | null;
  tool_name: string;
  input_payload: Record<string, unknown>;
  output_payload: Record<string, unknown>;
  status: string;
  error_message: string | null;
  created_at: string;
};

export type AgentRunDetail = AgentRun & {
  actions: AgentAction[];
  tool_calls: ToolCallLog[];
};

export type ToolDefinition = {
  id: string;
  name: string;
  description: string;
  category: string;
  input_schema: Record<string, unknown>;
  is_enabled: boolean;
  created_at: string;
};

export type PatchPreviewResponse = {
  path: string;
  diff: string;
  has_changes: boolean;
  original_content: string;
  new_content: string;
};

export type PatchApplyResponse = {
  write_call: ToolCallLog;
  preview: PatchPreviewResponse;
  git_diff_call: ToolCallLog | null;
  validation_call: ToolCallLog | null;
  audit_action: AgentAction | null;
};

export type PolicyCheckResponse = {
  allowed: boolean;
  reason: string | null;
};

export type ConstraintViolationLog = {
  id: string;
  project_id: string | null;
  rule_type: string;
  message: string;
  payload: Record<string, unknown>;
  created_at: string;
};
