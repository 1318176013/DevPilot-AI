
# AI 自动化开发团队 — 完整技术方案

> **运行环境**: Mac mini M4 16GB  
> **核心理念**: 轻量、可扩展、可升级、Agent 后端可插拔  
> **文档版本**: v1.0 Freeze  
> **更新日期**: 2026-06-01  
> **冻结状态**: 已冻结，作为 MVP 实施落地基线

---

## 目录

1. [系统概览](#1-系统概览)
2. [技术栈总览](#2-技术栈总览)
3. [服务部署方案](#3-服务部署方案)
4. [核心架构设计](#4-核心架构设计)
5. [数据库设计（PostgreSQL）](#5-数据库设计postgresql)
6. [向量数据库设计（Qdrant）](#6-向量数据库设计qdrant)
7. [Agent 后端抽象层](#7-agent-后端抽象层)
8. [模型注册中心（Model Registry）](#8-模型注册中心model-registry)
9. [需求引擎（Requirement Engine）](#9-需求引擎requirement-engine)
10. [DAG 任务编排引擎](#10-dag-任务编排引擎)
11. [工具注册中心（Tool Registry）](#11-工具注册中心tool-registry)
12. [浏览器调试 MVP](#12-浏览器调试-mvp)
13. [共享知识库（Shared Knowledge v1）](#13-共享知识库shared-knowledge-v1)
14. [策略守卫（Policy Guard）](#14-策略守卫policy-guard)
15. [前端界面设计](#15-前端界面设计)
16. [CLI 工具设计](#16-cli-工具设计)
17. [开发路线图](#17-开发路线图)
18. [附录](#18-附录)
19. [Agent 增强体系维护中心](#19-agent-增强体系维护中心)

---

## 1. 系统概览

### 1.1 系统定位

一个运行在本地 Mac mini 上的 **多项目 AI 自动化开发团队**，LLM 调用走云端 API，其他所有组件本地部署。核心能力：

- 接收自然语言需求，多轮对话澄清后自动拆解为 DAG 任务
- 多个 Agent 后端可插拔：默认自建轻量 Agent，后期可切换 OpenHands / Aider / SWE-agent
- 跨项目经验共享（Shared Knowledge），避免重复踩坑
- Web UI + CLI 双入口，支持模型编排、工作流可视化
- 浏览器交互调试 MVP（Playwright 驱动）

### 1.2 核心设计原则

| 原则 | 说明 |
|------|------|
| **可插拔 Agent 后端** | `AgentBackend` 抽象接口，默认自建，可切换开源方案 |
| **模型灵活绑定** | Model Registry 支持 5~8+ 模型，按能力标签绑定到工作流节点 |
| **多项目隔离** | PostgreSQL + Qdrant 通过 `project_id` 隔离数据 |
| **事实源单一** | PostgreSQL 是运行时唯一事实源，YAML 仅用于引导导入 |
| **资源可控** | 单任务串行执行、Headless 浏览器、步骤限制，适配 16GB 内存 |

### 1.3 完整工作流

```
用户需求 → Requirement Engine（多轮澄清）
        → DAG Engine（拆解任务）
        → Agent Runtime（调度 AgentBackend 执行）
        → Browser Debug（前端验证）
        → Review + Retry（修复循环）
        → Shared Knowledge（经验沉淀）
```

---

## 2. 技术栈总览

### 2.1 后端

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| Web 框架 | FastAPI (Python 3.12+) | 高性能异步框架 |
| 数据库 | PostgreSQL 16 | 事实源，所有元数据和配置 |
| 向量数据库 | Qdrant | 代码语义检索、共享知识、任务记忆 |
| 缓存/锁 | Redis 7 | 分布式锁、缓存、限流（不做消息队列） |
| 图数据库 | Neo4j（可选远程） | 增强版知识图谱，基础版用 PostgreSQL Graph |
| LLM 网关 | LiteLLM | 统一多模型调用接口 |
| 代码分析 | ripgrep + tree-sitter + ast-grep + semgrep | 代码检索与静态分析 |
| 浏览器调试 | Playwright | Headless 浏览器交互 |

### 2.2 前端

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| 框架 | Next.js 14 (App Router) | React 全栈框架 |
| UI 库 | shadcn/ui | 组件库 |
| 样式 | Tailwind CSS | 原子化 CSS |
| 工作流可视化 | React Flow | DAG 节点编排展示 |
| 代码编辑器 | Monaco Editor | 代码查看与 Diff |
| 状态管理 | Zustand | 轻量状态管理 |
| 数据请求 | TanStack Query | 服务端状态管理 |

### 2.3 DevOps

| 组件 | 技术选型 |
|------|----------|
| 容器化 | Docker Compose |
| 进程管理 | PM2 / supervisord |
| 包管理 | Poetry (Python) / pnpm (Node) |

---

## 3. 服务部署方案

### 3.1 需要部署的服务

| 服务 | 部署方式 | 版本 | 内存预估 | 说明 |
|------|----------|------|----------|------|
| **PostgreSQL** | Docker | 16 | ~256 MB | 主数据库 |
| **Redis** | Docker | 7 | ~100 MB | 缓存/锁/限流 |
| **Qdrant** | Docker | latest | ~500 MB | 向量检索 |
| **Neo4j** | Docker（可选） | 5 | ~512 MB | 增强图能力 |
| **FastAPI 后端** | 本地进程 (PM2) | — | ~500 MB | 核心服务 |
| **Next.js 前端** | 本地进程 (PM2) | — | ~300 MB | Web UI |
| **Playwright** | 随 Agent 调用 | — | ~300 MB | 按需启动 |

**总内存预估**: ~2.5 GB（含 Neo4j）/ ~2 GB（不含），在 16GB Mac mini 上运行充裕。

### 3.2 docker-compose.yml

```yaml
version: "3.9"

services:
  postgres:
    image: postgres:16-alpine
    container_name: ai-team-pg
    environment:
      POSTGRES_USER: aiteam
      POSTGRES_PASSWORD: ${PG_PASSWORD:-aiteam123}
      POSTGRES_DB: ai_dev_team
    ports:
      - "5432:5432"
    volumes:
      - pg_data:/var/lib/postgresql/data
      - ./docker/init-scripts:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U aiteam -d ai_dev_team"]
      interval: 10s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: ai-team-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      retries: 5

  qdrant:
    image: qdrant/qdrant:latest
    container_name: ai-team-qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 10s
      retries: 5

  # 可选：增强知识图谱能力
  neo4j:
    image: neo4j:5-community
    container_name: ai-team-neo4j
    profiles: ["graph"]  # 默认不启动，需要时加 --profile graph
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD:-aiteam123}
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - neo4j_data:/data

volumes:
  pg_data:
  redis_data:
  qdrant_data:
  neo4j_data:
```

---

## 4. 核心架构设计

### 4.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户入口                                  │
│              ┌──────────┐    ┌──────────┐                       │
│              │  Web UI  │    │   CLI    │                       │
│              └────┬─────┘    └────┬─────┘                       │
│                   │               │                              │
│              ┌────┴───────────────┴────┐                         │
│              │     FastAPI Gateway     │                         │
│              └──────────┬──────────────┘                         │
├─────────────────────────┼───────────────────────────────────────┤
│                         │                                        │
│  ┌──────────────────────┼──────────────────────────────────┐    │
│  │            Core Services                                │    │
│  │  ┌───────────┐  ┌────┴──────┐  ┌──────────────────┐    │    │
│  │  │Requirement│  │    DAG    │  │  Model Registry  │    │    │
│  │  │  Engine   │  │  Engine   │  │                  │    │    │
│  │  └───────────┘  └────┬──────┘  └──────────────────┘    │    │
│  │                      │                                   │    │
│  │  ┌───────────────────┴──────────────────────────────┐   │    │
│  │  │              Agent Runtime                       │   │    │
│  │  │  ┌─────────────────────────────────────────┐    │   │    │
│  │  │  │          AgentBackend Interface         │    │   │    │
│  │  │  │  ┌──────────┐ ┌──────────┐ ┌────────┐  │    │   │    │
│  │  │  │  │Lightweight│ │OpenHands │ │ Aider  │  │    │   │    │
│  │  │  │  │(default) │ │(future) │ │(future)│  │    │   │    │
│  │  │  │  └──────────┘ └──────────┘ └────────┘  │    │   │    │
│  │  │  └─────────────────────────────────────────┘    │   │    │
│  │  └─────────────────────────────────────────────────┘   │    │
│  │                                                        │    │
│  │  ┌──────────┐  ┌──────────────┐  ┌───────────────┐    │    │
│  │  │  Policy  │  │ Shared        │  │ Browser Debug │    │    │
│  │  │  Guard   │  │ Knowledge     │  │     MVP       │    │    │
│  │  └──────────┘  └──────────────┘  └───────────────┘    │    │
│  └────────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────────┤
│                      Data Layer                                  │
│  ┌──────────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  PostgreSQL  │  │  Qdrant  │  │  Redis   │  │  Neo4j   │   │
│  │   (事实源)   │  │ (向量)   │  │ (缓存锁) │  │ (可选)   │   │
│  └──────────────┘  └──────────┘  └──────────┘  └──────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                      External                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           LiteLLM Gateway → Cloud LLM APIs               │   │
│  │    GPT-5.5  │  DeepSeek V4 Pro  │  DeepSeek V4 Flash    │   │
│  │             │   ... (5-8+ models)  ...                   │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 模块依赖关系

```
Requirement Engine ──→ DAG Engine ──→ Agent Runtime ──→ AgentBackend
        │                    │               │
        │                    │               ├──→ Tool Registry
        │                    │               ├──→ Policy Guard
        │                    │               ├──→ Browser Debug
        │                    │               └──→ Shared Knowledge
        │                    │
        └────────────────────┴──→ Model Registry (LiteLLM)
```

---

## 5. 数据库设计（PostgreSQL）

PostgreSQL 是整个系统的**唯一运行时事实源**。项目配置、配置文件（如 `projects.yaml`）仅用于系统引导/导入。

### 5.1 核心表结构

#### 项目与配置

```sql
-- 项目表
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(500),
    local_path TEXT NOT NULL,
    repo_url TEXT,
    default_branch VARCHAR(255) DEFAULT 'main',
    language VARCHAR(100),
    framework VARCHAR(200),
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 项目允许执行的命令白名单
CREATE TABLE project_commands (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    command TEXT NOT NULL,                  -- e.g. "npm run test", "pytest"
    category VARCHAR(100) DEFAULT 'shell',  -- shell / git / browser / ...
    is_allowed BOOLEAN DEFAULT TRUE,
    description TEXT,
    UNIQUE(project_id, command)
);

-- 项目级策略配置
CREATE TABLE project_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    policy_type VARCHAR(100) NOT NULL,      -- file_access / network / browser
    config JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### 需求与任务

```sql
-- 需求表（经过 Requirement Engine 澄清后的最终版本）
CREATE TABLE requirements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    raw_requirement TEXT NOT NULL,           -- 用户原始输入
    clarified_requirement TEXT,             -- 多轮澄清后的需求
    conversation_history JSONB DEFAULT '[]',-- 多轮对话记录
    suitability_score DECIMAL(3,2),         -- 适合度评分 0.00-1.00
    risk_assessment JSONB,                  -- 风险评估
    acceptance_criteria JSONB,              -- 验收标准
    status VARCHAR(50) DEFAULT 'draft',     -- draft/clarified/planned/in_progress/done
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 任务表（DAG 拆解后的单个任务）
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requirement_id UUID NOT NULL REFERENCES requirements(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    task_type VARCHAR(100) NOT NULL,         -- plan/implement/test/browser_debug/review
    priority INTEGER DEFAULT 0,
    estimated_complexity VARCHAR(50),        -- low/medium/high
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- DAG 节点（任务依赖关系）
CREATE TABLE dag_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requirement_id UUID NOT NULL REFERENCES requirements(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id),
    node_type VARCHAR(100) NOT NULL,         -- 节点类型
    label VARCHAR(255) NOT NULL,
    config JSONB DEFAULT '{}',
    model_policy JSONB DEFAULT '{}',         -- 该节点使用的模型策略
    position_x FLOAT DEFAULT 0,             -- 可视化位置
    position_y FLOAT DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending',
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- DAG 边
CREATE TABLE dag_edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dag_id UUID NOT NULL REFERENCES dag_nodes(requirement_id),
    source_node_id UUID NOT NULL REFERENCES dag_nodes(id),
    target_node_id UUID NOT NULL REFERENCES dag_nodes(id),
    edge_type VARCHAR(50) DEFAULT 'sequential', -- sequential/conditional/parallel
    condition_expr TEXT,                      -- 条件表达式（JSON 格式）
    UNIQUE(source_node_id, target_node_id)
);
```

#### Agent 运行

```sql
-- 注册的 Agent 后端
CREATE TABLE agent_backends (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,       -- lightweight/openhands/aider/swe-agent
    kind VARCHAR(50) NOT NULL,              -- builtin/external
    capabilities TEXT[] NOT NULL DEFAULT '{}', -- ["file_rw","shell","browser","git"]
    is_enabled BOOLEAN DEFAULT TRUE,
    config JSONB DEFAULT '{}',
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agent 运行记录
CREATE TABLE agent_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requirement_id UUID NOT NULL REFERENCES requirements(id),
    task_id UUID REFERENCES tasks(id),
    dag_node_id UUID REFERENCES dag_nodes(id),
    backend_name VARCHAR(100) NOT NULL,
    project_id UUID NOT NULL REFERENCES projects(id),
    status VARCHAR(50) DEFAULT 'pending',
    summary TEXT,
    modified_files TEXT[] DEFAULT '{}',
    diff TEXT,
    token_usage JSONB,
    risks TEXT[] DEFAULT '{}',
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agent 执行的动作记录
CREATE TABLE agent_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_run_id UUID NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
    action_type VARCHAR(100) NOT NULL,       -- file_read/file_write/shell/browser/git
    action_detail JSONB NOT NULL,
    result JSONB,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### 共享知识

```sql
-- 跨项目共享知识
CREATE TABLE shared_knowledge (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    kind VARCHAR(100) NOT NULL,              -- error_pattern/fix_experience/test_template/review_rule
    content TEXT NOT NULL,
    source_project_id UUID REFERENCES projects(id),
    applicable_languages TEXT[] DEFAULT '{}',
    confidence DECIMAL(3,2) DEFAULT 1.0,     -- 置信度
    usage_count INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 产出物
CREATE TABLE artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_run_id UUID NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
    artifact_type VARCHAR(100) NOT NULL,     -- test_report/browser_screenshot/diff_patch
    file_path TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 浏览器调试记录
CREATE TABLE browser_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_run_id UUID NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
    page_url TEXT NOT NULL,
    steps JSONB DEFAULT '[]',
    screenshots TEXT[] DEFAULT '{}',
    console_errors JSONB DEFAULT '[]',
    network_errors JSONB DEFAULT '[]',
    report JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 向量化文件块记录
CREATE TABLE vector_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id),
    qdrant_point_id TEXT NOT NULL,
    collection VARCHAR(100) NOT NULL,        -- code_chunks/shared_knowledge/task_memory
    file_path TEXT,
    chunk_hash VARCHAR(64),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 5.2 DAG 节点类型枚举

| 节点类型 | 说明 | Agent 类型 |
|----------|------|------------|
| `analyze_requirement` | 需求分析 | 无（Requirement Engine 处理） |
| `plan_implementation` | 实现计划制定 | planner |
| `implement_code` | 代码实现 | coder |
| `browser_debug` | 浏览器交互调试 | browser |
| `retry_fix` | 修复重试 | coder |
| `run_tests` | 运行测试 | tester |
| `code_review` | 代码审查 | reviewer |
| `extract_knowledge` | 提取共享知识 | knowledge |
| `generate_docs` | 生成文档 | writer |

---

## 6. 向量数据库设计（Qdrant）

使用 Qdrant 作为统一向量存储，通过 `project_id` payload 字段实现多项目隔离。

### 6.1 Collection 设计

#### collection 1: `code_chunks`

代码语义检索，提供 Agent 上下文。

```json
{
  "vectors": { "size": 1536, "distance": "Cosine" },
  "payload_schema": {
    "project_id": "uuid",
    "file_path": "keyword",
    "chunk_index": "integer",
    "language": "keyword",
    "symbols": ["keyword"],
    "kind": "keyword",
    "summary": "text"
  }
}
```

**Payload 示例**:
```json
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "file_path": "src/services/auth.py",
  "chunk_index": 0,
  "language": "python",
  "symbols": ["login", "verify_token"],
  "kind": "function",
  "summary": "User login and JWT token verification"
}
```

#### collection 2: `shared_knowledge`

跨项目共享知识检索。

```json
{
  "vectors": { "size": 1536, "distance": "Cosine" },
  "payload_schema": {
    "kind": "keyword",
    "title": "text",
    "applicable_languages": ["keyword"],
    "confidence": "float",
    "status": "keyword",
    "source_project_id": "keyword",
    "usage_count": "integer"
  }
}
```

**Payload 示例**:
```json
{
  "kind": "error_pattern",
  "title": "CORS misconfiguration in FastAPI",
  "applicable_languages": ["python", "javascript"],
  "confidence": 0.95,
  "status": "active",
  "source_project_id": "550e8400-...",
  "usage_count": 12
}
```

#### collection 3: `task_memory`

任务执行记忆，辅助 Agent 上下文构建。

```json
{
  "vectors": { "size": 1536, "distance": "Cosine" },
  "payload_schema": {
    "project_id": "keyword",
    "task_type": "keyword",
    "agent_run_id": "keyword",
    "result": "keyword",
    "summary": "text",
    "created_at": "datetime"
  }
}
```

### 6.2 查询模式

```python
# 跨项目隔离查询示例
qdrant.search(
    collection_name="code_chunks",
    query_vector=embedding,
    query_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="project_id",
                match=models.MatchValue(value=str(project_id))
            )
        ]
    ),
    limit=10
)
```

---

## 7. Agent 后端抽象层

### 7.1 AgentBackend 接口定义

```typescript
// Agent 后端类型
export type AgentBackendKind = "builtin" | "external";

// Agent 能力
export type AgentCapability =
  | "file_read"
  | "file_write"
  | "file_search"
  | "shell_exec"
  | "git_ops"
  | "browser_interact"
  | "code_generate"
  | "test_run"
  | "static_analysis";

// 统一输入：任何后端接收相同的上下文包
export interface AgentRunInput {
  taskId: string;
  projectId: string;
  dagNodeId: string;
  agentType: AgentType;                    // planner / coder / browser / tester / reviewer
  backendPreference?: string;              // 偏好后端
  fallbackBackends?: string[];            // 回退后端列表
  requirement: RequirementSpec;            // 需求描述
  contextPack: ContextPack;                // 上下文包（代码片段、知识等）
  worktree: WorktreeRef;                   // 工作目录引用
  allowedTools: string[];                  // 允许的工具
  allowedCommands: ProjectCommand[];       // 允许的命令
  policies: ProjectPolicy[];               // 策略配置
  modelPolicy: ModelPolicy;                // 模型策略
  limits: AgentRunLimits;                  // 限制
}

// 统一输出：任何后端返回相同结构
export interface AgentRunResult {
  runId: string;
  backend: string;                         // 实际使用的后端名称
  status: "success" | "failed" | "cancelled" | "timeout";
  summary: string;
  modifiedFiles: string[];
  diff?: string;
  commandsExecuted: CommandExecutionResult[];
  testResults: TestResult[];
  browserReport?: BrowserDebugReport;
  risks: string[];
  artifacts: ArtifactRef[];
  tokenUsage?: TokenUsage;
  startedAt: string;
  finishedAt: string;
}

// 上下文包：外部 Agent 不需要重新检索，直接使用我们提供的上下文
export interface ContextPack {
  relevantCodeChunks: CodeChunk[];           // Qdrant 检索的相关代码
  sharedKnowledge: SharedKnowledgeItem[];    // 相关共享知识
  taskMemory: TaskMemoryItem[];             // 相关任务记忆
  graphContext?: GraphContext;               // 知识图谱上下文（可选）
  projectConfig: ProjectConfig;              // 项目配置
}

// Agent 后端实现接口
export interface AgentBackend {
  name: string;
  kind: AgentBackendKind;
  capabilities: AgentCapability[];

  /** 检查是否能处理该任务 */
  canHandle(input: AgentRunInput): Promise<AgentCapabilityCheck>;

  /** 预处理：将统一输入转换为后端特定格式 */
  prepare(input: AgentRunInput): Promise<PreparedAgentRun>;

  /** 执行 Agent 任务 */
  run(input: PreparedAgentRun): Promise<AgentRunResult>;

  /** 流式事件（可选） */
  streamEvents?(runId: string): AsyncIterable<AgentEvent>;

  /** 取消任务 */
  cancel(runId: string): Promise<void>;

  /** 清理资源 */
  cleanup(runId: string): Promise<void>;
}
```

### 7.2 后端实现对比

| 特性 | Lightweight (自建) | OpenHands (未来) | Aider (未来) |
|------|-------------------|------------------|-------------|
| **资源消耗** | 低 (~200MB) | 高 (~2GB+) | 中 (~500MB) |
| **启动速度** | < 1s | 30s-1min | < 5s |
| **代码编辑** | Patch + Test-Aware | 完整自主编辑 | 强大 Diff 编辑 |
| **浏览器交互** | Playwright MVP | ❌ | ❌ |
| **文件检索** | 我们提供的 ContextPack | 自行检索（浪费） | 自行检索 |
| **知识图谱** | 可用 | 不可用 | 不可用 |
| **自包含程度** | 依赖我们编排 | 高度自包含 | 中 |
| **可控性** | 完全可控 | 黑盒 | 中 |

### 7.3 Lightweight Agent 能力分级

| 级别 | 能力 | v1 支持 | 说明 |
|------|------|---------|------|
| **Level 1: Patch** | 理解上下文 → 生成 Diff → 应用补丁 | ✅ | 基础能力 |
| **Level 2: Test-Aware** | Patch + 执行测试 → 根据结果修复 | ✅ | v1 核心 |
| **Level 3: Graph-Aware** | 理解代码结构，跨文件修改 | ⚠️ 部分 | 依赖代码索引 |
| **Level 4: Autonomous** | 自主探索、全面理解项目 | ❌ v2+ | 需要强 Agent |

**v1 自建 Agent 能做的**:
- 文件读写、检索、代码生成
- 执行命令（白名单内）
- Playwright 浏览器调试
- 运行测试并修复
- Git 操作

**v1 自建 Agent 做不了的**（影响有限）:
- 无法自主探索大型未知项目 → 通过 Qdrant ContextPack 弥补
- 无法长时间自主迭代 → DAG 引擎外层编排
- 复杂重构可能不够好 → 人工 Review 兜底

### 7.4 后端选择与切换逻辑

```python
class AgentRuntime:
    """Agent 运行时：负责根据任务选择合适的后端"""

    async def select_backend(self, input: AgentRunInput) -> AgentBackend:
        # 1. 如果有偏好后端且可用，使用偏好后端
        if input.backendPreference:
            backend = self.backends.get(input.backendPreference)
            if backend and await backend.canHandle(input):
                return backend

        # 2. 按优先级遍历已注册后端
        for backend in self.registered_backends:
            if await backend.canHandle(input):
                return backend

        # 3. 尝试回退后端
        for name in (input.fallbackBackends or []):
            backend = self.backends.get(name)
            if backend and await backend.canHandle(input):
                return backend

        raise NoSuitableBackendError(input.taskId)

    async def execute_node(self, input: AgentRunInput) -> AgentRunResult:
        backend = await self.select_backend(input)
        prepared = await backend.prepare(input)
        return await backend.run(prepared)
```

---

## 8. 模型注册中心（Model Registry）

### 8.1 设计目标

- 模型与业务逻辑解耦，后期可扩展至 5~8+ 模型
- UI 可视化编排不同工作流节点使用不同模型
- 支持供应商 → 模型 → 能力标签 → 角色绑定 的层级管理
- 支持回退策略和负载均衡

### 8.2 核心概念

```typescript
interface ModelProvider {
  id: string;
  name: string;              // OpenAI / DeepSeek / Anthropic
  apiBase: string;           // LiteLLM proxy 地址
  models: ModelConfig[];
}

interface ModelConfig {
  id: string;
  name: string;              // gpt-5.5 / deepseek-v4-pro / deepseek-v4-flash
  providerId: string;
  capabilities: ModelCapability[];  // 能力标签
  contextWindow: number;     // Token 上限
  costPer1kInput: number;    // 成本
  costPer1kOutput: number;
  supportsVision: boolean;
  supportsFunctionCalling: boolean;
  maxConcurrency: number;
  isEnabled: boolean;
}

type ModelCapability =
  | "code_generation"
  | "code_review"
  | "planning"
  | "analysis"
  | "browser_understanding"   // 理解截图
  | "test_generation"
  | "documentation"
  | "requirement_clarification";

interface RoleBinding {
  role: AgentType;            // planner / coder / reviewer ...
  preferredModelId: string;
  fallbackModelIds: string[];
  temperature: number;
  maxTokens: number;
}

interface WorkflowNodeModelPolicy {
  nodeType: string;           // implement_code / code_review ...
  roleBinding: RoleBinding;
  retryBinding?: RoleBinding; // 重试时可用不同模型
}
```

### 8.3 模型编排示例

```
工作流节点          →  首选模型              →  回退模型
─────────────────────────────────────────────────────────
analyze_requirement →  deepseek-v4-pro      →  gpt-5.5
plan_implementation →  deepseek-v4-pro      →  gpt-5.5
implement_code      →  deepseek-v4-pro      →  deepseek-v4-flash → gpt-5.5
browser_debug       →  gpt-5.5              →  deepseek-v4-pro
run_tests           →  deepseek-v4-flash    →  (local)  
code_review         →  gpt-5.5              →  deepseek-v4-pro
extract_knowledge   →  deepseek-v4-flash    →  (local)
```

### 8.4 LiteLLM 集成

```python
# LiteLLM 作为统一 LLM 网关
# 所有模型调用通过 LiteLLM proxy，Model Registry 管理调用策略

class ModelGateway:
    """通过 LiteLLM 调用模型"""
    
    def __init__(self, registry: ModelRegistry):
        self.registry = registry
    
    async def call(self, policy: ModelPolicy, messages: list[dict]) -> str:
        """根据策略选择模型并调用"""
        model = policy.preferred
        try:
            return await self._call_litellm(model, messages)
        except Exception as e:
            for fallback in policy.fallbacks:
                try:
                    return await self._call_litellm(fallback, messages)
                except Exception:
                    continue
            raise ModelCallFailedError(policy, e)
```

---

## 9. 需求引擎（Requirement Engine）

### 9.1 设计目标

在正式开发前，通过多轮对话与用户澄清需求，确保需求清晰、适合自动化开发。

### 9.2 工作流程

```
用户输入原始需求
    │
    ▼
┌─────────────────────────────┐
│ 1. 需求解析 (Parse)          │
│    - 提取关键信息            │
│    - 识别需求类型            │
│    - 检测模糊点              │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ 2. 适合度评估 (Suitability)  │
│    - 复杂度评估 (0-1)        │
│    - 技术可行性检查          │
│    - 是否在自动化范围内      │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ 3. 多轮澄清 (Clarify)        │ ◄── 循环直到清晰
│    - 生成澄清问题            │
│    - 等待用户回复            │
│    - 更新需求描述            │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ 4. 风险评估 (Risk Assess)    │
│    - 技术风险点              │
│    - 依赖风险                │
│    - 安全风险                │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ 5. 验收标准生成              │
│    - 功能验收条件            │
│    - 测试用例草案            │
│    - 浏览器验证步骤          │
└──────────┬──────────────────┘
           │
           ▼
      输出 → DAG Engine
```

### 9.3 澄清问题示例

```
用户: "给管理后台加个用户导出功能"

AI 澄清:
1. 导出格式是 CSV / Excel / PDF？
2. 导出哪些字段？（全部 / 自定义选择）
3. 是否需要支持筛选条件导出？
4. 数据量大时是否需要分页/异步导出？
5. 是否需要权限控制？
```

### 9.4 适合度评分维度

| 维度 | 权重 | 说明 |
|------|------|------|
| 需求明确度 | 30% | 需求描述是否清晰完整 |
| 技术可行性 | 25% | 在当前技术栈下可否实现 |
| 范围可控性 | 20% | 改动范围是否可控 |
| 自动化适合度 | 15% | 是否适合 AI 自动实现 |
| 测试可验证性 | 10% | 是否有明确的验证方式 |

---

## 10. DAG 任务编排引擎

### 10.1 设计原则

- **串行执行**（v1）：16GB 内存限制，一次只跑一个任务
- **节点类型可扩展**：通过配置注册新节点类型
- **状态机驱动**：每个节点有明确的状态流转
- **错误恢复**：节点失败后根据策略重试或跳过

### 10.2 节点状态机

```
pending → queued → running → completed
                            → failed → retrying → running
                                     → skipped
                                     → cancelled
```

### 10.3 标准 DAG 工作流

```
┌──────────────────┐
│  analyze_requirement  │  需求分析
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  plan_implementation  │  实施计划
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   implement_code      │  代码实现
└────────┬─────────┘
         │
         ├──────────────┐
         ▼              ▼
┌──────────────┐  ┌──────────────┐
│ run_tests    │  │browser_debug │  测试 + 浏览器调试（并行机会）
└──────┬───────┘  └──────┬───────┘
       │                 │
       └────────┬────────┘
                ▼
         ┌────────────┐
         │ 失败? retry │──→ implement_code (重新实现)
         └─────┬──────┘
               │ 成功
               ▼
         ┌──────────────┐
         │  code_review  │  代码审查
         └──────┬───────┘
                ▼
         ┌──────────────────┐
         │extract_knowledge │  提取共享知识
         └──────────────────┘
```

### 10.4 DAG Engine API

```python
class DAGEngine:
    async def create_from_requirement(self, req: Requirement) -> DAG:
        """根据澄清后的需求自动生成 DAG"""

    async def execute(self, dag: DAG) -> DAGResult:
        """串行执行 DAG 节点"""

    async def get_node_context(self, node: DAGNode) -> ContextPack:
        """为节点构建上下文包（代码、知识、记忆）"""

    async def on_node_complete(self, node: DAGNode, result: AgentRunResult):
        """节点完成后处理：提取知识、更新记忆"""

    async def on_node_failed(self, node: DAGNode, error: Exception):
        """节点失败处理：决定重试/跳过/终止"""
```

---

## 11. 工具注册中心（Tool Registry）

### 11.1 设计

Agent 通过 Tool Registry 获取可用工具，Policy Guard 控制权限。

```typescript
interface Tool {
  name: string;
  description: string;
  category: ToolCategory;
  requiresApproval: boolean;
  execute(params: ToolParams): Promise<ToolResult>;
}

type ToolCategory = "file" | "shell" | "git" | "browser" | "search" | "test";

interface ToolRegistry {
  register(tool: Tool): void;
  getAvailableTools(context: AgentContext): Tool[];
  execute(toolName: string, params: ToolParams): Promise<ToolResult>;
}
```

### 11.2 内置工具列表

| 工具名 | 类别 | 说明 | 需审批 |
|--------|------|------|--------|
| `file_read` | file | 读取文件 | ❌ |
| `file_write` | file | 写入/创建文件 | ❌ |
| `file_search` | search | ripgrep 搜索 | ❌ |
| `code_symbol_search` | search | tree-sitter 符号搜索 | ❌ |
| `semantic_search` | search | Qdrant 语义搜索 | ❌ |
| `shell_exec` | shell | 执行白名单命令 | ⚠️ 白名单 |
| `git_status` | git | 查看状态 | ❌ |
| `git_diff` | git | 查看差异 | ❌ |
| `git_commit` | git | 提交 | ⚠️ |
| `browser_navigate` | browser | 导航到页面 | ⚠️ 白名单域名 |
| `browser_screenshot` | browser | 截图 | ❌ |
| `test_run` | test | 运行测试 | ❌ |

---

## 12. 浏览器调试 MVP

### 12.1 设计目标

v1 实现基础浏览器交互调试能力，验证前端改动效果。

### 12.2 技术方案

- **驱动**: Playwright (Python)
- **模式**: Headless（无 GUI）
- **范围**: 白名单页面 + 白名单域名
- **步骤限制**: 单次最多 20 步
- **产出**: 截图 + Console 错误 + Network 错误 + 结构化报告

### 12.3 架构

```
AgentRuntime
    │
    ├── 实现代码后触发 Browser Debug 节点
    │
    ▼
BrowserDebugService
    │
    ├── 启动 Playwright Headless Browser
    ├── 导航到目标页面（白名单检查）
    ├── 执行预设交互步骤
    ├── 捕获截图序列
    ├── 收集 Console 日志 / Network 错误
    ├── 生成结构化报告
    └── 关闭浏览器，返回 BrowserDebugReport
```

### 12.4 调试报告结构

```typescript
interface BrowserDebugReport {
  runId: string;
  pageUrl: string;
  steps: BrowserStep[];
  screenshots: ScreenshotRef[];
  consoleErrors: ConsoleErrorEntry[];
  networkErrors: NetworkErrorEntry[];
  overallStatus: "pass" | "fail" | "warning";
  summary: string;
  suggestions: string[];
}

interface BrowserStep {
  index: number;
  action: "navigate" | "click" | "type" | "wait" | "assert";
  target: string;        // CSS selector or URL
  value?: string;
  success: boolean;
  screenshotBefore?: string;
  screenshotAfter?: string;
  error?: string;
}
```

### 12.5 安全策略

- 仅允许访问 `project_policies` 中配置的白名单域名
- 仅允许访问项目启动的本地开发服务器（localhost:3xxx）
- 禁止提交表单（`input[type=submit]` 点击需要审批）
- 禁止文件下载
- 单次调试最长 5 分钟超时

---

## 13. 共享知识库（Shared Knowledge v1）

### 13.1 设计目标

跨项目经验共享，避免"同一个坑每个项目都跌倒一次"。

### 13.2 知识类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `error_pattern` | 错误模式及修复 | "FastAPI CORS 配置缺失导致跨域错误" |
| `fix_experience` | 修复经验 | "React useEffect 无限循环的 3 种解法" |
| `test_template` | 测试模板 | "Django Model 单元测试模板" |
| `review_rule` | 审查规则 | "SQL 注入检查清单" |
| `best_practice` | 最佳实践 | "Python async 错误处理最佳实践" |

### 13.3 知识生命周期

```
任务执行中遇到错误
    │
    ▼
Agent 搜索 shared_knowledge 集合
    │
    ├── 找到相关经验 → 注入 ContextPack → 使用经验修复
    │
    ▼
修复成功后
    │
    ▼
extract_knowledge 节点
    │
    ├── 归纳错误模式
    ├── 总结修复方案
    ├── 生成通用知识条目
    └── 写入 PostgreSQL + Qdrant
```

### 13.4 查询策略

```python
async def search_shared_knowledge(
    error_message: str,
    language: str,
    limit: int = 5
) -> list[SharedKnowledgeItem]:
    """根据错误信息语义搜索相关共享知识"""
    
    query_vector = await embedding_service.embed(error_message)
    
    results = qdrant.search(
        collection_name="shared_knowledge",
        query_vector=query_vector,
        query_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="status",
                    match=models.MatchValue(value="active")
                ),
                models.FieldCondition(
                    key="applicable_languages",
                    match=models.MatchAny(any=[language])
                )
            ]
        ),
        limit=limit,
        score_threshold=0.7
    )
    
    # 按 confidence × usage_count 排序
    return sorted(results, key=lambda r: r.confidence * log(r.usage_count + 1))
```

---

## 14. 策略守卫（Policy Guard）

### 14.1 设计目标

控制 Agent 的文件、命令、浏览器、Git 操作权限，防止危险操作。

### 14.2 权限控制维度

| 维度 | 控制内容 | 实现方式 |
|------|----------|----------|
| **文件访问** | 读写路径白名单 | `project_policies` 配置 |
| **命令执行** | 白名单命令列表 | `project_commands` 表 |
| **浏览器访问** | 白名单域名/路径 | `project_policies` 配置 |
| **Git 操作** | 允许的操作类型 | 仅 `status/diff/commit/branch` |
| **网络访问** | 外网访问限制 | 默认仅允许 localhost |

### 14.3 策略检查流程

```python
class PolicyGuard:
    """操作前策略检查"""

    async def check_file_write(self, project_id: UUID, path: str) -> bool:
        """检查是否允许写入该文件"""
        policies = await self.get_policies(project_id, "file_access")
        return self._match_path(path, policies.get("write_allowlist", []))

    async def check_command(self, project_id: UUID, command: str) -> bool:
        """检查命令是否在白名单中"""
        allowed = await self.get_allowed_commands(project_id)
        return any(fnmatch(command, cmd) for cmd in allowed)

    async def check_browser_url(self, project_id: UUID, url: str) -> bool:
        """检查是否允许访问该 URL"""
        policies = await self.get_policies(project_id, "browser")
        allowlist = policies.get("url_allowlist", ["localhost", "127.0.0.1"])
        return any(domain in url for domain in allowlist)

    async def guard(self, project_id: UUID, action: AgentAction) -> GuardResult:
        """统一守卫入口"""
        checks = {
            "file_write": self.check_file_write,
            "shell_exec": self.check_command,
            "browser_navigate": self.check_browser_url,
        }
        checker = checks.get(action.action_type)
        if not checker:
            return GuardResult(allowed=False, reason=f"Unknown action type: {action.action_type}")
        
        allowed = await checker(project_id, action.detail)
        return GuardResult(
            allowed=allowed,
            reason=None if allowed else "Action blocked by policy"
        )
```

---

## 15. 前端界面设计

### 15.1 页面结构

```
┌─────────────────────────────────────────────┐
│  Sidebar (可折叠)          │  主内容区       │
│                            │                │
│  📁 项目列表               │  [页面内容]    │
│   ├── Project A            │                │
│   ├── Project B            │                │
│   └── ...                  │                │
│                            │                │
│  📋 需求列表（当前项目）    │                │
│                            │                │
│  ⚙️ 设置                   │                │
│   ├── 模型管理             │                │
│   ├── Agent 后端           │                │
│   └── 项目配置             │                │
└─────────────────────────────────────────────┘
```

### 15.2 核心页面

| 页面 | 路由 | 功能 |
|------|------|------|
| **项目总览** | `/projects` | 项目列表、创建/导入项目 |
| **需求工作台** | `/projects/[id]/requirements` | 需求列表、创建需求、澄清对话 |
| **DAG 可视化** | `/requirements/[id]/dag` | React Flow DAG 图、节点状态、实时进度 |
| **Agent 运行监控** | `/requirements/[id]/runs` | Agent 运行记录、日志、结果 |
| **代码 Diff 查看** | `/runs/[id]/diff` | Monaco Editor Diff 视图 |
| **浏览器调试报告** | `/runs/[id]/browser` | 截图序列、Console/Network 错误 |
| **共享知识库** | `/knowledge` | 知识条目搜索、查看、管理 |
| **模型管理** | `/settings/models` | 模型供应商、模型管理、角色绑定 |
| **Agent 后端管理** | `/settings/backends` | 后端注册、能力查看、优先级 |

### 15.3 DAG 可视化（React Flow）

```typescript
// 节点自定义渲染
const nodeTypes = {
  dagNode: DagNodeComponent,        // 通用 DAG 节点
  requirement: RequirementNode,     // 需求分析节点
  implement: ImplementNode,         // 实现节点
  browserDebug: BrowserDebugNode,   // 浏览器调试节点
  test: TestNode,                   // 测试节点
  review: ReviewNode,               // 审查节点
};

// 节点状态颜色
const statusColors = {
  pending: "#94a3b8",    // 灰色
  running: "#3b82f6",    // 蓝色（带旋转动画）
  completed: "#22c55e",  // 绿色
  failed: "#ef4444",     // 红色
  retrying: "#f59e0b",   // 橙色
};
```

---

## 16. CLI 工具设计

### 16.1 命令结构

```bash
# 项目管理
ai-team project list                           # 列出所有项目
ai-team project add <name> --path <path>       # 添加项目
ai-team project remove <name>                  # 移除项目

# 需求管理
ai-team requirement create <project> --title "..." --desc "..."
ai-team requirement clarify <req-id>           # 进入澄清模式
ai-team requirement status <req-id>            # 查看需求状态

# 任务执行
ai-team run <req-id>                           # 执行需求
ai-team run <req-id> --watch                   # 执行并实时监控
ai-team run <req-id> --backend openhands       # 指定后端
ai-team run <req-id> --node <node-id>          # 单独执行某个节点

# 结果查看
ai-team result <req-id>                        # 查看执行结果
ai-team diff <run-id>                          # 查看代码变更
ai-team browser-report <run-id>                # 查看浏览器调试报告

# 知识库
ai-team knowledge search "<query>"             # 搜索共享知识
ai-team knowledge list --kind error_pattern    # 按类型列出

# 配置
ai-team config models                          # 查看模型配置
ai-team config backends                        # 查看 Agent 后端
```

### 16.2 输出示例

```bash
$ ai-team run req-abc123 --watch

╔══════════════════════════════════════════════════╗
║  需求: 给管理后台加用户导出功能                    ║
║  项目: admin-dashboard                            ║
║  后端: lightweight (default)                      ║
╚══════════════════════════════════════════════════╝

[1/6] analyze_requirement  ................ ✅ (2.3s)
[2/6] plan_implementation  ................ ✅ (4.1s)
[3/6] implement_code         ................ 🔄 Running...
       ├── 创建 src/export/users.py
       ├── 修改 src/routes/admin.py
       └── 添加测试 test_export.py
[3/6] implement_code         ................ ✅ (45.2s)
[4/6] run_tests              ................ ✅ (12.7s)
[5/6] code_review            ................ ✅ (8.3s)
[6/6] extract_knowledge      ................ ✅ (3.1s)

═══════════════════════════════════════════════════
  总耗时: 1m 15.7s
  状态: ✅ SUCCESS
  修改文件: 3
  Token 用量: 12,450 input / 3,210 output
  风险: 无
═══════════════════════════════════════════════════
```

---

## 17. 开发路线图

### Phase 1: 基础设施（预计 2 周）

- [ ] Docker Compose 环境搭建（PostgreSQL + Redis + Qdrant）
- [ ] FastAPI 项目骨架 + 数据库迁移
- [ ] Next.js 前端骨架 + shadcn/ui 集成
- [ ] LiteLLM Gateway 配置
- [ ] 基础 CLI 框架

### Phase 2: 核心引擎（预计 3 周）

- [ ] Model Registry（模型管理 API + UI）
- [ ] Requirement Engine（需求解析、澄清、评估）
- [ ] DAG Engine（节点定义、状态机、串行执行）
- [ ] Policy Guard（权限检查）

### Phase 3: Agent 实现（预计 3 周）

- [ ] AgentBackend 接口定义
- [ ] LightweightAgentBackend 实现
  - [ ] ContextPack 构建（Qdrant 检索集成）
  - [ ] Tool Registry 实现
  - [ ] Level 1 Patch + Level 2 Test-Aware
- [ ] Agent Runtime（后端选择与任务调度）
- [ ] 代码分析工具集成（ripgrep / tree-sitter）

### Phase 4: 浏览器调试 + 共享知识（预计 2 周）

- [ ] Browser Debug MVP（Playwright 集成）
- [ ] Shared Knowledge（知识提取 + 检索）
- [ ] 知识生命周期管理

### Phase 5: UI 完善 + CLI（预计 2 周）

- [ ] DAG 可视化（React Flow）
- [ ] Agent 运行监控页面
- [ ] 代码 Diff 页面（Monaco Editor）
- [ ] 模型管理页面（可视化编排）
- [ ] CLI 全功能实现

### Phase 6: 集成测试 + 文档（预计 1 周）

- [ ] 端到端集成测试
- [ ] 使用文档
- [ ] 自建 Agent 与开源方案对比评测

### 未来规划（v2+）

- [ ] OpenHands / Aider 后端适配器
- [ ] Neo4j 知识图谱增强
- [ ] 并行任务执行
- [ ] Level 3 Graph-Aware Agent
- [ ] WebSocket 实时推送

---

## 18. 附录

### 18.1 项目目录结构

```
ai-dev-team/
├── backend/
│   ├── app/
│   │   ├── api/                    # FastAPI 路由
│   │   │   ├── projects.py
│   │   │   ├── requirements.py
│   │   │   ├── tasks.py
│   │   │   ├── agents.py
│   │   │   └── knowledge.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── security.py
│   │   ├── engine/
│   │   │   ├── requirement_engine.py
│   │   │   ├── dag_engine.py
│   │   │   ├── agent_runtime.py
│   │   │   └── policy_guard.py
│   │   ├── agents/
│   │   │   ├── base.py              # AgentBackend 接口
│   │   │   ├── lightweight.py       # 自建 Agent
│   │   │   ├── tools.py             # Tool Registry
│   │   │   └── context_builder.py   # ContextPack 构建
│   │   ├── browser/
│   │   │   └── debug_service.py     # Playwright 封装
│   │   ├── knowledge/
│   │   │   ├── shared_knowledge.py
│   │   │   └── extractor.py
│   │   ├── models/
│   │   │   ├── registry.py          # Model Registry
│   │   │   ├── gateway.py           # LiteLLM 网关
│   │   │   └── embeddings.py        # 向量化服务
│   │   ├── search/
│   │   │   ├── qdrant_client.py
│   │   │   ├── code_search.py
│   │   │   └── semantic_search.py
│   │   └── schemas/                 # Pydantic 模型
│   ├── alembic/                     # 数据库迁移
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/                     # Next.js App Router
│   │   │   ├── projects/
│   │   │   ├── requirements/
│   │   │   ├── runs/
│   │   │   ├── knowledge/
│   │   │   └── settings/
│   │   ├── components/
│   │   │   ├── ui/                  # shadcn/ui 组件
│   │   │   ├── dag/                 # React Flow 节点
│   │   │   ├── diff/                # Monaco Editor Diff
│   │   │   └── browser-debug/       # 浏览器报告
│   │   ├── lib/
│   │   │   ├── api-client.ts
│   │   │   └── websocket.ts
│   │   └── stores/                  # Zustand stores
│   ├── package.json
│   └── next.config.js
├── cli/
│   ├── ai_team/
│   │   ├── main.py
│   │   ├── commands/
│   │   └── formatters.py
│   └── setup.py
├── docker/
│   ├── docker-compose.yml
│   └── init-scripts/
├── projects.yaml                    # 仅用于引导/导入
└── README.md
```

### 18.2 关键配置示例

#### `projects.yaml`（引导用，非事实源）

```yaml
# 仅用于系统初始化时导入，运行时事实源在 PostgreSQL
projects:
  - name: admin-dashboard
    display_name: 管理后台
    local_path: /Users/dev/projects/admin-dashboard
    repo_url: https://github.com/org/admin-dashboard.git
    language: typescript
    framework: Next.js
    default_branch: main
```

#### 模型注册配置

```json
{
  "providers": [
    {
      "id": "openai",
      "name": "OpenAI",
      "apiBase": "http://localhost:4000/openai",
      "models": [
        {
          "id": "gpt-5.5",
          "name": "gpt-5.5",
          "capabilities": [
            "code_generation", "code_review", "planning",
            "analysis", "browser_understanding", "test_generation",
            "documentation", "requirement_clarification"
          ],
          "contextWindow": 128000,
          "supportsVision": true,
          "supportsFunctionCalling": true
        }
      ]
    },
    {
      "id": "deepseek",
      "name": "DeepSeek",
      "apiBase": "http://localhost:4000/deepseek",
      "models": [
        {
          "id": "deepseek-v4-pro",
          "name": "deepseek-v4-pro",
          "capabilities": [
            "code_generation", "code_review", "planning",
            "analysis", "test_generation", "requirement_clarification"
          ],
          "contextWindow": 128000,
          "supportsVision": false,
          "supportsFunctionCalling": true
        },
        {
          "id": "deepseek-v4-flash",
          "name": "deepseek-v4-flash",
          "capabilities": [
            "code_generation", "test_generation", "documentation"
          ],
          "contextWindow": 32000,
          "supportsVision": false,
          "supportsFunctionCalling": true
        }
      ]
    }
  ]
}
```

### 18.3 术语表

| 术语 | 说明 |
|------|------|
| **Requirement Engine** | 需求引擎：多轮对话澄清需求、适合度评估 |
| **DAG Engine** | DAG 任务编排引擎：自动拆解需求为任务节点 |
| **Agent Runtime** | Agent 运行时：根据任务选择合适后端并调度执行 |
| **AgentBackend** | Agent 后端抽象接口：可插拔的 Agent 实现 |
| **Lightweight Agent** | 自建轻量 Agent：v1 默认后端 |
| **ContextPack** | 上下文包：注入给 Agent 的代码、知识、记忆集合 |
| **Model Registry** | 模型注册中心：管理模型供应商、能力标签、角色绑定 |
| **Policy Guard** | 策略守卫：文件/命令/浏览器/Git 权限控制 |
| **Shared Knowledge** | 共享知识库：跨项目经验沉淀与复用 |
| **Browser Debug** | 浏览器调试：Playwright 驱动的 Headless 前端验证 |
| **Tool Registry** | 工具注册中心：Agent 可用工具的注册与分发 |

---

## 19. Agent 增强体系维护中心

### 19.1 模块定位

`Agent Enhancement Management Center` 是系统的能力治理层，负责维护 Agent 可使用的 Skill、MCP、工具、规范约束、知识库、工作流模板和能力边界。

该模块的核心目标是把 Agent 从“依赖模型训练知识的执行器”升级为：

```text
可配置、可扩展、可约束、可审计、可评估、可持续演进的 AI 开发成员
```

在整体架构中的位置：

```text
用户任务
  ↓
Requirement Engine
  ↓
DAG Engine
  ↓
Agent Selector
  ↓
Agent Profile Loader
  ↓
Capability Loader
  ├── Skill Loader
  ├── MCP Loader
  ├── Tool Loader
  ├── Constraint Loader
  ├── Knowledge Loader
  └── Workflow Loader
  ↓
Prompt Builder
  ↓
Agent Runtime
  ↓
Policy Guard / Constraint Engine
  ↓
Tool Gateway / MCP Gateway
  ↓
Verification / Audit / Evaluation
```

### 19.2 设计原则

| 原则 | 说明 |
|------|------|
| **能力显式化** | Agent 的能力不隐含在 Prompt 中，而是通过 Profile、Skill、Tool、MCP、Constraint 显式声明 |
| **配置事实源统一** | PostgreSQL 作为运行时事实源，Skill YAML / MCP JSON 只用于导入和版本归档 |
| **最小权限** | Agent 默认只获得完成任务所需的最小工具和数据访问权限 |
| **工具调用可审计** | 所有 Tool / MCP 调用都记录请求、结果、耗时、错误和约束命中情况 |
| **约束前置** | 高风险操作在执行前由 Policy Guard 和 Constraint Engine 拦截 |
| **版本可回滚** | Skill、规范、工作流模板均支持版本化和回滚 |
| **项目隔离** | 不同项目可绑定不同的 Skill、MCP、知识库和约束包 |

### 19.3 核心功能范围

增强体系维护中心包含八类能力：

```text
1. Agent Profile 管理
2. Skill 管理
3. MCP Server 管理
4. Tool Registry 管理
5. Constraint 规范约束管理
6. Knowledge 知识库绑定管理
7. Workflow 工作流模板管理
8. Audit & Evaluation 审计评估管理
```

### 19.4 Agent Profile 管理

Agent Profile 用于定义每类 Agent 的职责、能力边界、可用模型、可用 Skill、可用工具和审批策略。

#### 19.4.1 典型 Agent 类型

| Agent | 职责 | 推荐权限等级 |
|------|------|-------------|
| Requirement Agent | 需求澄清、需求结构化、验收标准生成 | L0-L1 |
| Architect Agent | 技术方案、模块划分、接口设计 | L0-L1 |
| Frontend Agent | 页面、组件、交互、前端测试 | L2-L3 |
| Backend Agent | API、数据库、业务逻辑、后端测试 | L2-L3 |
| Tester Agent | 测试用例、自动化测试、缺陷复现 | L2-L3 |
| Reviewer Agent | 代码审查、安全审查、规范检查 | L0-L1 |
| DevOps Agent | 构建、部署、发布、环境排查 | L3-L5，强审批 |

#### 19.4.2 能力等级

| 等级 | 能力范围 | 示例 |
|------|----------|------|
| L0 Readonly | 只读分析 | 读取需求、代码、日志 |
| L1 Suggest | 生成建议和补丁 | 生成方案、生成 Diff |
| L2 Workspace Write | 修改工作区文件 | 写代码、改配置 |
| L3 Verify | 可运行验证命令 | 执行测试、Lint、构建 |
| L4 Commit | 可执行 Git 提交 | 创建分支、提交代码 |
| L5 Deploy | 可执行部署发布 | 预发部署、生产发布 |

#### 19.4.3 Profile 示例

```yaml
id: backend_agent
name: 后端开发 Agent
type: backend
level: L3
model_policy:
  preferred_capabilities:
    - code_generation
    - api_design
    - test_generation
allowed_skills:
  - fastapi-backend
  - database-design
  - api-testing
allowed_tools:
  - file.read
  - file.write
  - code.search
  - shell.run
  - test.run
denied_tools:
  - deploy.production
approval_required:
  - database.migration
  - git.commit
  - shell.run:dangerous
context_policy:
  include_project_standards: true
  include_related_code: true
  include_shared_knowledge: true
```

### 19.5 Skill 管理

Skill 是面向特定领域的能力包，包含领域知识、标准流程、工具依赖、约束规则、示例和输出格式。

```text
Skill = 领域知识 + SOP + 工具依赖 + 约束规则 + 示例 + 输出格式
```

#### 19.5.1 Skill 生命周期

```text
Draft → Published → Enabled → Deprecated → Archived
```

#### 19.5.2 Skill 维护功能

| 功能 | 说明 |
|------|------|
| Skill 注册 | 新增 Skill 元数据和版本 |
| Skill 编辑 | 修改说明、触发条件、工具依赖、约束绑定 |
| Skill 启用/禁用 | 控制是否可被 Agent 加载 |
| Skill 版本管理 | 支持多版本、灰度、回滚 |
| Skill 测试 | 使用标准任务验证 Skill 效果 |
| Agent 绑定 | 限定哪些 Agent 可使用该 Skill |
| 约束绑定 | 绑定代码规范、安全规范、流程规范 |
| 质量统计 | 统计调用次数、成功率、失败原因、评分 |

#### 19.5.3 Skill 结构建议

```text
skills/
  react-frontend/
    skill.yaml
    instructions.md
    constraints.md
    examples/
    checklists.md
  fastapi-backend/
    skill.yaml
    instructions.md
    constraints.md
    examples/
    checklists.md
```

#### 19.5.4 Skill 配置示例

```yaml
id: react-frontend
name: React Frontend Development
version: 1.0.0
status: enabled
description: React 前端开发能力包
triggers:
  keywords:
    - React
    - component
    - frontend
  file_patterns:
    - "src/**/*.tsx"
    - "src/**/*.jsx"
required_tools:
  - file.read
  - file.write
  - code.search
  - npm.test
constraints:
  - use_project_component_library
  - avoid_duplicate_components
  - run_lint_after_change
output_contract:
  require_plan: true
  require_diff_summary: true
  require_verification_result: true
```

### 19.6 MCP Server 管理

MCP 用于连接外部工具、服务和数据源。系统不应让 Agent 直接裸连 MCP，而应通过 MCP Gateway、Policy Guard 和审计层访问。

推荐链路：

```text
Agent Runtime
  → Tool Registry
  → Policy Guard
  → MCP Gateway
  → MCP Server
  → External System
```

#### 19.6.1 MCP 类型

| 类型 | 示例 | 用途 |
|------|------|------|
| filesystem | 本地文件系统 MCP | 文件读写、目录遍历 |
| git | Git MCP | 状态、Diff、分支、提交 |
| database | PostgreSQL / MySQL MCP | 数据查询、Schema 分析 |
| browser | Playwright MCP | 页面访问、截图、交互测试 |
| design | Figma MCP | 设计稿读取、标注提取 |
| issue | Jira / GitHub Issues MCP | 需求、缺陷、任务同步 |
| cloud | 云服务 MCP | 部署、日志、资源查询 |
| docs | 内部文档 MCP | API 文档、规范文档检索 |

#### 19.6.2 MCP 维护功能

| 功能 | 说明 |
|------|------|
| Server 注册 | 维护名称、类型、启动命令、连接参数 |
| 健康检查 | 定时检查可用性、版本和延迟 |
| 权限配置 | 控制读、写、删除、提交、部署等动作 |
| Agent 绑定 | 指定哪些 Agent 可访问该 MCP |
| 项目绑定 | 指定 MCP 适用项目 |
| 密钥管理 | API Key、Token、连接串加密存储 |
| 调用审计 | 记录请求、结果、耗时、错误 |
| 熔断禁用 | 异常率过高时自动禁用 |

#### 19.6.3 MCP 配置示例

```yaml
id: git-local
name: Local Git MCP
type: git
status: enabled
command: uvx
args:
  - mcp-server-git
permissions:
  status: true
  diff: true
  branch: true
  commit: false
  push: false
allowed_agents:
  - reviewer_agent
  - backend_agent
approval_required:
  - commit
  - push
```

### 19.7 Tool Registry 管理

Tool Registry 统一管理本地工具和 MCP 工具，是 Agent 可调用能力的统一入口。

#### 19.7.1 工具分类

| 分类 | 工具示例 |
|------|----------|
| 文件工具 | `file.read`、`file.write`、`file.delete` |
| 代码工具 | `code.search`、`ast.parse`、`semgrep.scan` |
| 命令工具 | `shell.run`、`npm.test`、`pytest.run` |
| Git 工具 | `git.status`、`git.diff`、`git.commit` |
| 浏览器工具 | `browser.open`、`browser.click`、`browser.screenshot` |
| 数据库工具 | `db.query`、`db.schema`、`db.migration` |
| 部署工具 | `deploy.preview`、`deploy.production` |

#### 19.7.2 工具风险等级

| 等级 | 说明 | 示例 |
|------|------|------|
| low | 只读或无副作用 | `file.read`、`git.status` |
| medium | 修改工作区但可回滚 | `file.write`、`npm.install` |
| high | 影响数据、Git、环境 | `db.migration`、`git.commit` |
| critical | 生产或不可逆操作 | `deploy.production`、`file.delete` |

### 19.8 Constraint 规范约束管理

Constraint Engine 负责加载、合并、校验和执行项目规范、角色规范、安全规范和流程规范。

#### 19.8.1 约束类型

| 类型 | 说明 |
|------|------|
| project | 项目规范，如目录结构、框架约定 |
| architecture | 架构规范，如分层、依赖方向、模块边界 |
| code_style | 代码规范，如命名、格式、组件复用 |
| security | 安全规范，如禁止明文密钥、禁止危险命令 |
| workflow | 流程规范，如必须先设计再编码 |
| approval | 审批规范，如提交、部署、迁移需确认 |
| output | 输出规范，如必须包含验证结果和变更摘要 |

#### 19.8.2 约束等级

```text
soft      建议遵守，不阻断
hard      必须遵守，违规阻断
approval  需要人工审批
audit     不阻断，但记录审计
```

#### 19.8.3 约束执行时机

| 阶段 | 校验内容 |
|------|----------|
| 任务开始前 | Agent 是否有权限接任务，是否需要审批 |
| Plan 生成后 | 是否符合工作流规范和架构边界 |
| 工具调用前 | Tool / MCP 是否允许调用，参数是否安全 |
| 文件修改后 | 是否违反代码、目录、安全规范 |
| 验证完成后 | 是否满足测试、Lint、构建要求 |
| 任务结束时 | 是否生成报告、审计记录、知识沉淀 |

#### 19.8.4 约束示例

```yaml
id: no_direct_main_branch_commit
name: 禁止直接提交 main 分支
type: git_policy
level: hard
description: Agent 不允许直接向 main/master 分支提交代码
scope:
  agents:
    - frontend_agent
    - backend_agent
    - devops_agent
action:
  deny:
    - git.commit_to_main
    - git.push_to_main
```

### 19.9 Knowledge 绑定管理

知识库维护不只负责文档存储，还要负责把不同知识源绑定到项目、Agent、Skill 和工作流。

#### 19.9.1 知识类型

```text
项目知识库
技术规范库
API 文档库
历史决策库
问题经验库
代码索引库
测试用例库
运维手册库
```

#### 19.9.2 绑定策略

| 绑定对象 | 示例 |
|----------|------|
| 项目绑定 | 某项目只能检索本项目文档和共享知识 |
| Agent 绑定 | Backend Agent 优先检索接口、数据库、后端规范 |
| Skill 绑定 | React Skill 绑定组件库文档和前端规范 |
| Workflow 绑定 | 发布流程绑定发布手册、回滚手册 |

### 19.10 Workflow 模板管理

工作流模板用于规范多 Agent 协作顺序，避免 Agent 自由发挥。

#### 19.10.1 典型模板

| 模板 | 步骤 |
|------|------|
| 功能开发流程 | 需求分析 → 技术设计 → 任务拆分 → 编码 → 测试 → 审查 → 交付 |
| Bug 修复流程 | 复现 → 定位 → 修复 → 回归测试 → 总结 |
| 前端页面流程 | 原型分析 → 组件设计 → 页面实现 → 浏览器验证 → Review |
| 后端 API 流程 | 接口设计 → Schema 设计 → 实现 → 单测 → 接口测试 |
| 发布流程 | 构建 → 预发部署 → 验证 → 审批 → 生产发布 → 监控 |

#### 19.10.2 Workflow 配置示例

```yaml
id: feature_development_workflow
name: 功能开发流程
version: 1.0.0
steps:
  - id: requirement_analysis
    agent: requirement_agent
    required_output: requirement_spec
  - id: technical_design
    agent: architect_agent
    required_output: technical_design
  - id: implementation
    agent: backend_agent
    required_skills:
      - fastapi-backend
  - id: verification
    agent: tester_agent
    required_tools:
      - test.run
  - id: review
    agent: reviewer_agent
    gate: required
```

### 19.11 数据库设计补充

建议在 PostgreSQL 中新增以下表，作为增强体系运行时事实源。

#### Agent Profile

```sql
CREATE TABLE agent_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    type VARCHAR(50) NOT NULL,
    level VARCHAR(20) NOT NULL,
    description TEXT,
    model_policy JSONB DEFAULT '{}',
    context_policy JSONB DEFAULT '{}',
    output_contract JSONB DEFAULT '{}',
    status VARCHAR(20) NOT NULL DEFAULT 'enabled',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### Skill Registry

```sql
CREATE TABLE skill_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_key VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE skill_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_id UUID NOT NULL REFERENCES skill_registry(id) ON DELETE CASCADE,
    version VARCHAR(50) NOT NULL,
    instructions TEXT NOT NULL,
    triggers JSONB DEFAULT '{}',
    required_tools JSONB DEFAULT '[]',
    constraints JSONB DEFAULT '[]',
    output_contract JSONB DEFAULT '{}',
    changelog TEXT,
    is_active BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(skill_id, version)
);

CREATE TABLE agent_skill_bindings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_profile_id UUID NOT NULL REFERENCES agent_profiles(id) ON DELETE CASCADE,
    skill_id UUID NOT NULL REFERENCES skill_registry(id) ON DELETE CASCADE,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(agent_profile_id, skill_id)
);
```

#### MCP 与 Tool

```sql
CREATE TABLE mcp_servers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    type VARCHAR(50) NOT NULL,
    command TEXT,
    args JSONB DEFAULT '[]',
    env JSONB DEFAULT '{}',
    permissions JSONB DEFAULT '{}',
    health_status VARCHAR(20) DEFAULT 'unknown',
    status VARCHAR(20) DEFAULT 'disabled',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE tool_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tool_key VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    provider VARCHAR(50) NOT NULL, -- local / mcp / external
    risk_level VARCHAR(20) NOT NULL DEFAULT 'low',
    input_schema JSONB DEFAULT '{}',
    output_schema JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'enabled',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE agent_tool_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_profile_id UUID NOT NULL REFERENCES agent_profiles(id) ON DELETE CASCADE,
    tool_id UUID NOT NULL REFERENCES tool_registry(id) ON DELETE CASCADE,
    permission JSONB DEFAULT '{}',
    approval_required BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(agent_profile_id, tool_id)
);
```

#### Constraint 与审计

```sql
CREATE TABLE constraint_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_key VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    type VARCHAR(50) NOT NULL,
    level VARCHAR(20) NOT NULL,
    description TEXT,
    condition JSONB DEFAULT '{}',
    action JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'enabled',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE constraint_bindings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    constraint_id UUID NOT NULL REFERENCES constraint_rules(id) ON DELETE CASCADE,
    target_type VARCHAR(50) NOT NULL, -- project / agent / skill / workflow
    target_id UUID NOT NULL,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE tool_call_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_run_id UUID REFERENCES agent_runs(id) ON DELETE CASCADE,
    tool_key VARCHAR(100) NOT NULL,
    request JSONB DEFAULT '{}',
    response JSONB DEFAULT '{}',
    status VARCHAR(20) NOT NULL,
    latency_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE constraint_violation_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_run_id UUID REFERENCES agent_runs(id) ON DELETE CASCADE,
    constraint_key VARCHAR(100) NOT NULL,
    level VARCHAR(20) NOT NULL,
    action_taken VARCHAR(50) NOT NULL, -- allow / block / approval_required / audit
    detail JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### Workflow 与审批

```sql
CREATE TABLE workflow_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_key VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    version VARCHAR(50) NOT NULL,
    definition JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'enabled',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE approval_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_run_id UUID REFERENCES agent_runs(id) ON DELETE CASCADE,
    request_type VARCHAR(50) NOT NULL,
    summary TEXT NOT NULL,
    payload JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'pending',
    requested_by VARCHAR(100),
    approved_by VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);
```

### 19.12 API 设计

#### Agent Profile API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/agent-profiles` | 查询 Agent Profile 列表 |
| POST | `/api/agent-profiles` | 创建 Agent Profile |
| GET | `/api/agent-profiles/{id}` | 查看详情 |
| PUT | `/api/agent-profiles/{id}` | 更新配置 |
| POST | `/api/agent-profiles/{id}/bind-skills` | 绑定 Skill |
| POST | `/api/agent-profiles/{id}/permissions` | 配置工具权限 |

#### Skill API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/skills` | Skill 列表 |
| POST | `/api/skills` | 注册 Skill |
| POST | `/api/skills/import` | 从目录或 YAML 导入 |
| GET | `/api/skills/{id}/versions` | 查看版本 |
| POST | `/api/skills/{id}/versions` | 新增版本 |
| POST | `/api/skills/{id}/enable` | 启用 |
| POST | `/api/skills/{id}/test` | 测试 Skill |

#### MCP / Tool API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/mcp-servers` | MCP 列表 |
| POST | `/api/mcp-servers` | 注册 MCP |
| POST | `/api/mcp-servers/{id}/health-check` | 健康检查 |
| PUT | `/api/mcp-servers/{id}/permissions` | 更新权限 |
| GET | `/api/tools` | 工具列表 |
| PUT | `/api/tools/{id}/risk-level` | 更新风险等级 |
| GET | `/api/tool-call-logs` | 工具调用日志 |

#### Constraint / Workflow API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/constraints` | 约束列表 |
| POST | `/api/constraints` | 创建约束 |
| POST | `/api/constraints/{id}/bind` | 绑定约束 |
| POST | `/api/constraints/check` | 手动执行约束检查 |
| GET | `/api/workflows/templates` | 工作流模板列表 |
| POST | `/api/workflows/templates` | 创建模板 |
| POST | `/api/workflows/templates/{id}/validate` | 校验模板 |
| GET | `/api/approvals` | 审批请求列表 |
| POST | `/api/approvals/{id}/approve` | 审批通过 |
| POST | `/api/approvals/{id}/reject` | 审批拒绝 |

### 19.13 前端页面设计补充

在设置中心新增“增强体系”菜单组：

```text
设置
  ├── 模型管理
  ├── Agent 后端
  ├── Agent Profile
  ├── Skill 管理
  ├── MCP 管理
  ├── Tool Registry
  ├── 规范约束
  ├── 知识库绑定
  ├── 工作流模板
  └── 审计评估
```

核心页面：

| 页面 | 路由 | 功能 |
|------|------|------|
| Agent Profile | `/settings/agent-profiles` | 角色、等级、模型、能力边界配置 |
| Skill 管理 | `/settings/skills` | Skill 注册、版本、绑定、测试 |
| MCP 管理 | `/settings/mcp` | MCP Server 注册、健康检查、权限配置 |
| Tool Registry | `/settings/tools` | 工具清单、风险等级、权限配置 |
| 规范约束 | `/settings/constraints` | 约束规则、绑定范围、冲突检测 |
| 知识库绑定 | `/settings/knowledge-bindings` | 项目/Agent/Skill 与知识库绑定 |
| 工作流模板 | `/settings/workflows` | 流程模板、节点、审批门禁 |
| 审计评估 | `/settings/audit` | 工具调用、约束命中、Agent 质量评分 |

### 19.14 执行期集成流程

Agent 执行任务前，Runtime 应动态装配增强能力：

```python
class CapabilityLoader:
    async def load_for_task(self, project_id, agent_type, task):
        agent_profile = await self.agent_profiles.get_by_type(agent_type)
        skills = await self.skills.match(agent_profile, task)
        tools = await self.tools.get_allowed_tools(agent_profile, skills)
        mcp_servers = await self.mcp.get_allowed_servers(agent_profile, project_id)
        constraints = await self.constraints.resolve(
            project_id=project_id,
            agent_profile=agent_profile,
            skills=skills,
            tools=tools,
        )
        knowledge = await self.knowledge.retrieve_policy(project_id, agent_profile, skills)

        return CapabilityPack(
            agent_profile=agent_profile,
            skills=skills,
            tools=tools,
            mcp_servers=mcp_servers,
            constraints=constraints,
            knowledge=knowledge,
        )
```

工具调用前必须经过统一守卫：

```python
class GuardedToolGateway:
    async def call(self, run_id, agent_profile, tool_key, payload):
        guard_result = await self.policy_guard.check_tool_call(
            agent_profile=agent_profile,
            tool_key=tool_key,
            payload=payload,
        )

        if guard_result.requires_approval:
            return await self.approval_center.create_request(run_id, tool_key, payload)

        if not guard_result.allowed:
            await self.audit.log_blocked(run_id, tool_key, guard_result.reason)
            raise PermissionError(guard_result.reason)

        result = await self.tool_registry.call(tool_key, payload)
        await self.audit.log_tool_call(run_id, tool_key, payload, result)
        return result
```

### 19.15 Prompt Builder 集成

Prompt 不再是固定模板，而是由增强体系动态生成：

```text
System Prompt =
  基础系统身份
  + Agent Profile 职责边界
  + 当前任务说明
  + 已加载 Skill 指令
  + 项目规范约束
  + 可用工具清单
  + 禁止操作清单
  + 审批要求
  + 相关知识上下文
  + 输出格式要求
```

这可以避免把所有规则硬编码进一个超大 Prompt，同时便于按项目、Agent、任务类型动态调整。

### 19.16 MVP 落地路线

#### MVP-1：基础维护能力

目标：先让系统能显式维护 Agent 能力和工具权限。

```text
- Agent Profile CRUD
- Skill Registry CRUD
- Tool Registry CRUD
- MCP Server Registry CRUD
- Constraint Rule CRUD
- Agent 与 Skill / Tool / MCP 绑定
- 工具调用日志
```

#### MVP-2：执行期集成

目标：Agent 执行任务时可以动态加载增强能力。

```text
- Capability Loader
- Skill 自动匹配
- Constraint Resolver
- Guarded Tool Gateway
- Prompt Builder 集成
- 审批请求机制
- 约束命中日志
```

#### MVP-3：治理与评估

目标：让增强体系可持续优化。

```text
- Skill 成功率统计
- MCP 健康检查与熔断
- 约束冲突检测
- Agent 质量评分
- 工作流模板版本管理
- 执行报告与复盘知识沉淀
```

### 19.17 与现有模块关系

| 现有模块 | 增强方式 |
|----------|----------|
| Agent Runtime | 执行前加载 CapabilityPack |
| AgentBackend | 接收已裁剪的 Skill、Tool、Constraint、Knowledge |
| Tool Registry | 扩展风险等级、权限、审计和 MCP 工具代理 |
| Policy Guard | 扩展为 Tool + Constraint 双重守卫 |
| Shared Knowledge | 支持与 Agent、Skill、Workflow 绑定 |
| DAG Engine | 节点可声明所需 Skill、工具、审批门禁 |
| Model Registry | Agent Profile 根据能力标签选择模型 |
| 前端设置中心 | 新增增强体系维护页面 |

### 19.18 结论

Agent 增强体系维护中心应作为 v1.5 至 v2 的核心能力建设。它不是单纯的后台配置页，而是 Agent Runtime 的能力治理基础设施。

最终系统形态应从：

```text
用户任务 → Agent → 模型 → 输出
```

升级为：

```text
用户任务
  → 任务分析
  → Agent 选择
  → 能力装配
  → 规范约束
  → 工具/MCP 调用
  → 验证审计
  → 经验沉淀
```

这样才能支撑长期可控、可复用、可审计的 AI 自动化开发团队。

> **下一步**: 按开发路线图 Phase 1 开始搭建基础设施，同时继续细化各模块的接口定义和数据结构。

