# AI 自动化开发团队 — MVP 实施落地规划

> **关联方案**: `AI开发团队完整方案.md`  
> **方案状态**: v1.0 Freeze  
> **规划版本**: v1.0  
> **制定日期**: 2026-06-01  
> **目标**: 将完整方案收敛为可执行 MVP，优先跑通“需求 → 任务拆解 → Agent 执行 → 验证 → 报告”的最小闭环。

---

## 1. 实施总目标

MVP 阶段的目标不是一次性实现完整 AI 开发团队系统，而是先完成一个可运行、可验证、可扩展的最小版本。

核心闭环：

```text
用户创建项目
  → 提交自然语言需求
  → Requirement Engine 结构化需求
  → DAG Engine 生成任务节点
  → Agent Runtime 调度 Lightweight Agent
  → Tool Registry 调用文件/搜索/命令工具
  → Policy Guard 做基础权限检查
  → Agent 修改代码或生成结果
  → 执行测试/校验
  → 输出运行日志、Diff、执行报告
```

MVP 成功标准：

```text
系统能够在一个本地示例项目中，完成一次端到端自动化开发任务。
```

---

## 2. MVP 范围边界

### 2.1 MVP 必须做

| 模块 | 必做内容 |
|------|----------|
| 项目管理 | 创建项目、配置本地路径、查看项目列表 |
| 需求管理 | 创建需求、需求结构化、需求状态流转 |
| DAG 编排 | 自动生成基础任务节点、节点状态管理、串行执行 |
| Agent Runtime | 调度 Lightweight Agent 执行 DAG 节点 |
| Lightweight Agent | 支持读取文件、搜索代码、生成计划、修改文件、运行验证命令 |
| Tool Registry | 注册基础工具：文件读写、代码搜索、命令执行 |
| Policy Guard | 控制文件写入路径、命令白名单、危险操作拦截 |
| Model Registry | 管理模型供应商、模型能力标签、默认模型选择 |
| LiteLLM 集成 | 统一 LLM 调用入口 |
| Qdrant 检索 | 支持基础代码片段索引和检索 |
| Agent 日志 | 记录 Agent Run、Action、工具调用、错误信息 |
| Web UI | 项目列表、需求工作台、DAG 视图、运行日志、Diff 查看 |
| CLI | 支持项目、需求、运行状态的基础命令 |

### 2.2 MVP 简化做

| 模块 | 简化策略 |
|------|----------|
| Skill 管理 | 只做 Skill 注册、启用、Agent 绑定，不做复杂版本治理 |
| MCP 管理 | 先预留表和接口，不接入真实复杂 MCP Server |
| Constraint 管理 | 只实现基础规则：文件路径、命令、Git 禁止项 |
| Shared Knowledge | 先实现手动沉淀和基础检索，不做自动评分 |
| Browser Debug | 先支持打开页面、截图、采集 Console 错误 |
| 审批流 | 先用阻断和日志代替复杂审批中心 |

### 2.3 MVP 暂不做

```text
- 多 Agent 并行协作
- OpenHands / Aider / SWE-agent 接入
- Neo4j 知识图谱
- 生产部署 Agent
- 完整 MCP 生态治理
- Skill 灰度发布和评分系统
- 复杂审批流
- 自动优化 Prompt / Skill
- 多租户 SaaS 化
```

---

## 3. 总体实施阶段

建议 MVP 分为 6 个实施阶段，预计 10-12 周完成第一个可用版本。

```text
阶段 0：方案冻结与工程初始化
阶段 1：基础设施与项目骨架
阶段 2：核心数据模型与基础 API
阶段 3：Requirement + DAG 最小闭环
阶段 4：Agent Runtime + Tool Registry + Policy Guard
阶段 5：前端工作台 + CLI + 端到端验证
阶段 6：增强体系基础版 + 文档验收
```

---

## 4. 阶段 0：方案冻结与工程初始化

### 4.1 目标

完成方案冻结，明确 MVP 边界，准备进入工程落地。

### 4.2 任务清单

| 编号 | 任务 | 产出 |
|------|------|------|
| 0.1 | 冻结完整技术方案 | `AI开发团队完整方案.md` 标记为 v1.0 Freeze |
| 0.2 | 形成 MVP 实施规划 | `AI开发团队MVP实施落地规划.md` |
| 0.3 | 明确不做范围 | MVP 边界清单 |
| 0.4 | 确认本地运行环境 | Python、Node、Docker、pnpm、Poetry |
| 0.5 | 确定初始示例项目 | 用于端到端验证的本地项目 |

### 4.3 验收标准

```text
- 完整方案已冻结
- MVP 计划已形成
- 第一阶段开发任务明确
```

---

## 5. 阶段 1：基础设施与项目骨架

### 5.1 目标

搭建系统基础运行环境，形成前后端工程骨架。

### 5.2 后端任务

| 编号 | 任务 | 说明 |
|------|------|------|
| 1.1 | 创建 `backend/` 工程 | FastAPI + Python 3.12 |
| 1.2 | 配置 Poetry / requirements | 管理后端依赖 |
| 1.3 | 配置 FastAPI 基础结构 | app、api、core、schemas、services |
| 1.4 | 配置 SQLAlchemy / Alembic | 数据库 ORM 和迁移 |
| 1.5 | 配置 Redis 客户端 | 缓存、锁预留 |
| 1.6 | 配置 Qdrant 客户端 | 向量检索预留 |
| 1.7 | 配置 LiteLLM 客户端 | LLM Gateway 调用封装 |

### 5.3 前端任务

| 编号 | 任务 | 说明 |
|------|------|------|
| 1.8 | 创建 `frontend/` 工程 | Next.js 14 App Router |
| 1.9 | 集成 Tailwind CSS | 样式基础 |
| 1.10 | 集成 shadcn/ui | UI 组件基础 |
| 1.11 | 配置 TanStack Query | API 请求状态管理 |
| 1.12 | 配置 Zustand | 客户端状态管理 |
| 1.13 | 配置基础布局 | Sidebar + Header + Content |

### 5.4 基础设施任务

| 编号 | 任务 | 说明 |
|------|------|------|
| 1.14 | 编写 Docker Compose | PostgreSQL、Redis、Qdrant |
| 1.15 | 编写 `.env.example` | 环境变量模板 |
| 1.16 | 编写启动脚本 | 本地一键启动 |
| 1.17 | 编写健康检查接口 | `/health`、`/ready` |

### 5.5 验收标准

```text
- Docker Compose 可启动 PostgreSQL、Redis、Qdrant
- FastAPI `/health` 可访问
- Next.js 首页可访问
- 后端可连接 PostgreSQL
- 前端可调用后端健康检查接口
```

---

## 6. 阶段 2：核心数据模型与基础 API

### 6.1 目标

建立 MVP 必需的数据表和基础 API。

### 6.2 数据库建表顺序

第一批：项目与模型

```text
projects
project_policies
model_providers
models
model_bindings
```

第二批：需求与 DAG

```text
requirements
requirement_clarifications
dag_nodes
dag_edges
```

第三批：Agent 执行

```text
agent_backends
agent_runs
agent_actions
tool_call_logs
```

第四批：工具与策略

```text
tool_registry
agent_profiles
agent_tool_permissions
constraint_rules
constraint_violation_logs
```

第五批：知识与报告

```text
knowledge_items
knowledge_usages
browser_reports
```

### 6.3 API 任务

| 编号 | API 模块 | 主要接口 |
|------|----------|----------|
| 2.1 | Project API | 创建、列表、详情、更新 |
| 2.2 | Model API | 供应商、模型、默认模型配置 |
| 2.3 | Requirement API | 创建需求、列表、详情、状态更新 |
| 2.4 | DAG API | 生成 DAG、查询 DAG、更新节点状态 |
| 2.5 | Agent Run API | 创建运行、查询运行、查询日志 |
| 2.6 | Tool API | 工具注册、工具列表、调用日志 |
| 2.7 | Policy API | 项目策略、命令白名单 |

### 6.4 验收标准

```text
- Alembic 可完成数据库初始化
- Project / Requirement / DAG / Agent Run 基础 API 可用
- Swagger 文档可查看
- 能通过 API 创建一个项目和一个需求
```

---

## 7. 阶段 3：Requirement + DAG 最小闭环

### 7.1 目标

实现从自然语言需求到 DAG 任务节点的自动拆解。

### 7.2 Requirement Engine 任务

| 编号 | 任务 | 说明 |
|------|------|------|
| 3.1 | 需求结构化 Prompt | 输出标题、目标、范围、验收标准 |
| 3.2 | 澄清问题生成 | 判断需求不清晰时生成问题 |
| 3.3 | 适合度评分 | 判断是否适合 Agent 自动开发 |
| 3.4 | 需求状态机 | draft / clarifying / ready / planned |
| 3.5 | 需求结果落库 | 保存结构化需求 JSON |

### 7.3 DAG Engine 任务

| 编号 | 任务 | 说明 |
|------|------|------|
| 3.6 | DAG 节点模板 | analysis、design、coding、testing、review |
| 3.7 | DAG 生成 Prompt | 根据结构化需求生成任务节点 |
| 3.8 | DAG 校验 | 检查节点类型、依赖关系、是否有环 |
| 3.9 | DAG 状态机 | pending / running / success / failed / blocked |
| 3.10 | DAG 落库 | 保存节点和边 |

### 7.4 验收标准

```text
- 输入一段自然语言需求，可以生成结构化需求
- 可以根据结构化需求生成 DAG 节点
- DAG 节点能在数据库中查询
- 前端或 Swagger 能查看 DAG 结果
```

---

## 8. 阶段 4：Agent Runtime + Tool Registry + Policy Guard

### 8.1 目标

跑通 Agent 执行任务的核心能力。

### 8.2 Agent Runtime 任务

| 编号 | 任务 | 说明 |
|------|------|------|
| 4.1 | 定义 AgentBackend 接口 | canHandle / prepare / run / cancel |
| 4.2 | 实现 LightweightAgentBackend | MVP 默认 Agent |
| 4.3 | 实现 ContextPack | 项目、需求、DAG 节点、相关代码 |
| 4.4 | 实现 Agent Run 状态机 | pending / running / success / failed |
| 4.5 | 实现事件日志 | 保存 Agent 执行过程 |
| 4.6 | 实现失败处理 | 失败原因、可重试标记 |

### 8.3 Tool Registry 任务

| 编号 | 工具 | 能力 |
|------|------|------|
| 4.7 | `file.read` | 读取项目文件 |
| 4.8 | `file.write` | 写入项目文件 |
| 4.9 | `code.search` | 基于 ripgrep 搜索代码 |
| 4.10 | `shell.run` | 执行白名单命令 |
| 4.11 | `git.diff` | 查看工作区 Diff |
| 4.12 | `test.run` | 执行测试命令 |

### 8.4 Policy Guard 任务

| 编号 | 规则 | 说明 |
|------|------|------|
| 4.13 | 文件路径白名单 | 只允许写入项目目录 |
| 4.14 | 命令白名单 | 只允许 npm test、pytest、lint 等 |
| 4.15 | Git 禁止项 | 禁止 push、reset、clean 等高危操作 |
| 4.16 | 删除限制 | MVP 默认禁止删除文件 |
| 4.17 | 调用审计 | 每次工具调用写入日志 |

### 8.5 验收标准

```text
- Agent 可以读取项目文件
- Agent 可以搜索代码
- Agent 可以生成修改计划
- Agent 可以修改允许范围内的文件
- Agent 可以执行白名单测试命令
- 被禁止的操作会被 Policy Guard 拦截
- Agent Run 全过程有日志
```

---

## 9. 阶段 5：前端工作台 + CLI + 端到端验证

### 9.1 目标

提供基本可用的 Web UI 和 CLI，完成端到端演示。

### 9.2 Web UI 任务

| 编号 | 页面 | 功能 |
|------|------|------|
| 5.1 | 项目列表 | 创建、查看项目 |
| 5.2 | 需求工作台 | 创建需求、查看结构化结果 |
| 5.3 | DAG 可视化 | 展示节点、状态、依赖 |
| 5.4 | Agent 运行监控 | 查看运行状态和事件日志 |
| 5.5 | Diff 页面 | 展示 Agent 修改内容 |
| 5.6 | 模型管理 | 配置供应商、模型、默认模型 |
| 5.7 | 基础设置 | 项目策略、命令白名单 |

### 9.3 CLI 任务

| 编号 | 命令 | 说明 |
|------|------|------|
| 5.8 | `ai-team project list` | 查看项目 |
| 5.9 | `ai-team project add` | 添加项目 |
| 5.10 | `ai-team requirement create` | 创建需求 |
| 5.11 | `ai-team requirement status` | 查看需求状态 |
| 5.12 | `ai-team dag show` | 查看 DAG |
| 5.13 | `ai-team run start` | 启动 Agent Run |
| 5.14 | `ai-team run watch` | 查看运行日志 |

### 9.4 端到端演示任务

选择一个本地示例项目，完成：

```text
1. 在 Web UI 创建项目
2. 输入一个简单开发需求
3. 生成结构化需求
4. 生成 DAG
5. 启动 Agent 执行 coding 节点
6. Agent 修改文件
7. 运行测试或 lint
8. 查看 Diff
9. 查看执行报告
```

### 9.5 验收标准

```text
- Web UI 可完成主要流程操作
- CLI 可完成基础流程操作
- 至少一个端到端演示成功
- 用户能看到 DAG、日志、Diff、报告
```

---

## 10. 阶段 6：增强体系基础版 + 文档验收

### 10.1 目标

接入增强体系的基础维护能力，为后续 Skill / MCP / Constraint 扩展打基础。

### 10.2 增强体系基础任务

| 编号 | 模块 | MVP 内容 |
|------|------|----------|
| 6.1 | Agent Profile | 创建、编辑、绑定工具 |
| 6.2 | Skill Registry | 注册 Skill、启用/禁用、绑定 Agent |
| 6.3 | Constraint Rules | 创建基础约束、绑定项目或 Agent |
| 6.4 | Tool Permissions | 为 Agent 配置可用工具 |
| 6.5 | MCP Registry | 预留 MCP Server 注册页面和表结构 |
| 6.6 | Audit Logs | 展示工具调用和约束命中记录 |

### 10.3 文档任务

| 编号 | 文档 | 内容 |
|------|------|------|
| 6.7 | 本地部署文档 | Docker、后端、前端启动方式 |
| 6.8 | 开发文档 | 后端、前端、数据库、Agent 模块说明 |
| 6.9 | 使用文档 | 如何创建项目、提交需求、运行 Agent |
| 6.10 | 演示文档 | MVP Demo 操作步骤 |
| 6.11 | 已知限制 | MVP 不支持项和风险说明 |

### 10.4 验收标准

```text
- 能在 UI 中维护 Agent Profile、Skill、基础约束
- 能查看工具调用审计日志
- 文档可以指导新机器完成本地启动
- MVP Demo 可重复执行
```

---

## 11. 任务优先级

### P0：必须完成，否则 MVP 不成立

```text
- FastAPI + PostgreSQL 基础后端
- Next.js 基础前端
- Project / Requirement / DAG / Agent Run 数据模型
- Requirement Engine
- DAG Engine
- Agent Runtime
- Lightweight Agent
- Tool Registry 基础工具
- Policy Guard 基础权限
- Agent 日志
- Web UI 主流程
```

### P1：建议完成，增强可用性

```text
- Model Registry UI
- Qdrant 代码检索
- CLI 基础命令
- Diff 页面
- Browser Debug 基础截图
- Skill Registry 基础版
- Constraint Rules 基础版
```

### P2：可延期

```text
- MCP 真实接入
- Shared Knowledge 自动沉淀
- 复杂审批流
- 多 Agent 编排
- Neo4j
- 开源 Agent 后端适配
```

---

## 12. 里程碑计划

| 里程碑 | 周期 | 目标 | 可验收产物 |
|--------|------|------|------------|
| M0 | 第 0 周 | 方案冻结 | 完整方案 Freeze + MVP 规划 |
| M1 | 第 1-2 周 | 基础工程可运行 | 后端、前端、数据库启动成功 |
| M2 | 第 3-4 周 | 数据模型和 API 完成 | 项目、需求、DAG、Agent Run API 可用 |
| M3 | 第 5-6 周 | 需求到 DAG 闭环 | 自然语言需求可生成 DAG |
| M4 | 第 7-8 周 | Agent 执行闭环 | Agent 可读写文件、运行验证、输出日志 |
| M5 | 第 9-10 周 | UI + CLI 可演示 | Web UI 和 CLI 可完成主流程 |
| M6 | 第 11-12 周 | MVP 验收 | Demo 可重复执行，文档齐全 |

---

## 13. 首轮开发任务拆分

### 13.1 Backend Epic

```text
BE-01 后端工程初始化
BE-02 数据库连接与 Alembic 迁移
BE-03 Project API
BE-04 Model Registry API
BE-05 Requirement API
BE-06 Requirement Engine
BE-07 DAG 数据模型与 API
BE-08 DAG Engine
BE-09 AgentBackend 接口
BE-10 Agent Runtime
BE-11 Lightweight Agent
BE-12 Tool Registry
BE-13 Policy Guard
BE-14 Agent Run 日志
BE-15 Qdrant 检索服务
BE-16 Browser Debug 服务
BE-17 Skill / Constraint 基础 API
```

### 13.2 Frontend Epic

```text
FE-01 前端工程初始化
FE-02 基础 Layout 和导航
FE-03 API Client 封装
FE-04 项目列表页面
FE-05 需求工作台页面
FE-06 DAG 可视化页面
FE-07 Agent 运行监控页面
FE-08 Diff 查看页面
FE-09 模型管理页面
FE-10 设置：项目策略
FE-11 设置：Agent Profile
FE-12 设置：Skill / Constraint 基础维护
```

### 13.3 CLI Epic

```text
CLI-01 CLI 工程初始化
CLI-02 配置后端地址
CLI-03 project 命令组
CLI-04 requirement 命令组
CLI-05 dag 命令组
CLI-06 run 命令组
CLI-07 日志 watch 输出
```

### 13.4 Infra Epic

```text
INFRA-01 Docker Compose
INFRA-02 PostgreSQL 初始化
INFRA-03 Redis 初始化
INFRA-04 Qdrant 初始化
INFRA-05 LiteLLM 配置
INFRA-06 环境变量模板
INFRA-07 本地启动脚本
```

### 13.5 QA / Docs Epic

```text
QA-01 API 单元测试
QA-02 Requirement Engine 测试样例
QA-03 DAG Engine 测试样例
QA-04 Tool / Policy Guard 测试
QA-05 端到端 Demo 脚本
DOC-01 本地部署文档
DOC-02 使用手册
DOC-03 开发说明
DOC-04 MVP 限制说明
```

---

## 14. 第一批 Sprint 建议

### Sprint 1：工程骨架与基础设施 ✅ 已完成

目标：系统能启动。

完成时间：2026-06-01

任务：

```text
[x] INFRA-01 Docker Compose
[x] INFRA-02 PostgreSQL 初始化
[x] INFRA-03 Redis 初始化
[x] INFRA-04 Qdrant 初始化
[x] BE-01 后端工程初始化
[x] BE-02 数据库连接与基础健康检查
[x] FE-01 前端工程初始化
[x] FE-02 基础 Layout 和导航
```

验收：

```text
[x] docker compose up 成功
[x] 后端 /health 成功
[x] 后端 /ready 成功，PostgreSQL / Redis / Qdrant 全部 ready
[x] 前端首页成功
[x] 前端可调用后端 health API
```

验收结果：

```json
{
  "status": "ready",
  "checks": {
    "postgres": true,
    "redis": true,
    "qdrant": true
  }
}
```


### Sprint 2：项目、模型、需求基础能力 ✅ 已完成

目标：能创建项目和需求。

完成时间：2026-06-01

任务：

```text
[x] BE-03 Project API
[x] BE-04 Model Registry API
[x] BE-05 Requirement API
[x] FE-03 API Client 封装
[x] FE-04 项目列表页面
[x] FE-05 需求工作台页面基础版
[x] CLI-01 CLI 工程初始化
[x] CLI-03 project 命令组
```

验收：

```text
[x] UI 可创建项目
[x] UI 可创建需求
[x] CLI 可查看项目列表
[x] Swagger 可查看接口
```

验收结果：

```text
- Project API / Requirement API / Model Registry API 已挂载到 FastAPI
- 首页工作台已支持创建项目和需求，并展示列表
- `python -m app.cli project list` 可查看项目列表
- `http://localhost:8000/docs` 返回 200
```

### Sprint 3：Requirement Engine + DAG Engine

目标：自然语言需求可生成 DAG。

任务：

```text
BE-06 Requirement Engine
BE-07 DAG 数据模型与 API
BE-08 DAG Engine
FE-06 DAG 可视化页面
CLI-04 requirement 命令组
CLI-05 dag 命令组
QA-02 Requirement Engine 测试样例
QA-03 DAG Engine 测试样例
```

验收：

```text
- 输入需求后生成结构化结果
- 结构化需求可生成 DAG
- UI 可展示 DAG
- CLI 可查看 DAG
```

### Sprint 4：Agent Runtime + Tool + Policy

目标：Agent 可执行一个编码节点。

任务：

```text
BE-09 AgentBackend 接口
BE-10 Agent Runtime
BE-11 Lightweight Agent
BE-12 Tool Registry
BE-13 Policy Guard
BE-14 Agent Run 日志
FE-07 Agent 运行监控页面
FE-08 Diff 查看页面
QA-04 Tool / Policy Guard 测试
```

验收：

```text
- Agent Run 可启动
- Agent 可读取和搜索项目文件
- Agent 可修改允许范围内文件
- Agent 可执行白名单命令
- UI 可查看日志和 Diff
```

---

## 15. 关键风险与降级方案

| 风险 | 影响 | 降级方案 |
|------|------|----------|
| Agent 自主编码不稳定 | 端到端 Demo 失败 | 先让 Agent 输出 Patch，由系统应用补丁 |
| LLM 输出 DAG 不稳定 | 节点格式错误 | 使用 JSON Schema 校验，不合格自动重试 |
| 本地命令执行风险 | 文件或环境被破坏 | 默认命令白名单，禁止删除和 Git 高危命令 |
| Qdrant 检索效果不稳定 | 上下文质量差 | MVP 先用 ripgrep + 文件摘要兜底 |
| 前端页面开发耗时 | 影响演示 | 先以表格和 JSON 视图替代复杂可视化 |
| Skill / MCP 范围过大 | 拖慢 MVP | 只做注册和绑定，不做复杂执行治理 |

---

## 16. MVP 最终验收清单

MVP 完成时必须满足：

```text
[ ] 可以创建本地项目
[ ] 可以配置模型供应商和默认模型
[ ] 可以创建自然语言需求
[ ] 可以生成结构化需求
[ ] 可以生成 DAG 任务节点
[ ] 可以启动 Agent Run
[ ] Agent 可以读取、搜索、修改项目文件
[ ] Agent 可以执行白名单验证命令
[ ] Policy Guard 可以拦截危险操作
[ ] 可以查看 Agent 日志
[ ] 可以查看代码 Diff
[ ] 可以生成执行报告
[ ] 可以通过 Web UI 完成主流程
[ ] 可以通过 CLI 查看关键状态
[ ] 有本地部署文档
[ ] 有 MVP Demo 文档
```

---

## 17. 结论

当前完整方案已经冻结为 `v1.0 Freeze`，下一步正式进入 MVP 落地阶段。

实施策略是：

```text
先闭环，后增强；
先可控，后自主；
先单 Agent，后多 Agent；
先基础 Tool，后完整 MCP；
先基础约束，后治理体系。
```

当前 `Sprint 1` 与 `Sprint 2` 已完成，下一阶段建议进入 `Sprint 3：Requirement Engine + DAG Engine`，跑通“自然语言需求 → 结构化需求 → DAG 任务节点”的最小闭环。
