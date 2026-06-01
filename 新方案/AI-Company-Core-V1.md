# AI Company Core V1

## 一、项目目标

构建一个基于 AI 的自动化软件开发团队，实现从需求分析到代码交付的完整开发闭环。

核心能力：

* 多轮需求分析
* PRD 自动生成
* 任务自动拆解
* 架构自动设计
* 自动代码开发
* 自动测试验证
* 自动 Bug 修复
* 自动代码 Review
* 自动知识沉淀
* 多项目知识隔离

---

# 二、总体架构

```text
User
 │
 ▼

Requirement Analyst
（需求分析）

 │
 ▼

Requirement Freeze
（需求冻结）

 │
 ▼

Project Planner
（任务拆解）

 │
 ▼

Architect
（架构设计）

 │
 ▼

Memory Search
（知识检索）

 │
 ▼

Builder
（代码开发）

 │
 ▼

QA
（自动测试）

 │
 ▼

Bug Analyzer
（错误分析）

 │
 ├── Retry < 3
 │        │
 │        ▼
 │      Builder
 │
 └── Retry >= 3
          │
          ▼
    Human Review

 │
 ▼

Reviewer
（代码审查）

 │
 ▼

Memory Save
（知识沉淀）

 │
 ▼

DONE
```

---

# 三、核心组件

## 1. Ruflo

系统唯一编排中心。

职责：

* Workflow 管理
* Agent 调度
* 状态管理
* 重试机制
* 上下文传递

---

## 2. OpenHands

系统唯一执行器。

职责：

* 创建代码
* 修改代码
* 执行命令
* 执行测试
* Git 操作

---

## 3. PostgreSQL

系统主数据库。

存储：

* 项目
* PRD
* 任务
* 记忆
* 决策

---

## 4. pgvector

向量检索引擎。

功能：

* 相似知识搜索
* 历史经验召回
* Bug 经验召回

---

## 5. Memory MCP

统一记忆访问层。

提供：

```python
memory.search()
memory.save()
memory.decisions()
```

---

# 四、V1 不引入组件

暂不引入：

* Neo4j
* Redis
* Kafka
* RabbitMQ
* Elasticsearch
* Milvus
* Qdrant
* 分布式 Worker
* Raft 投票
* 多节点集群

原则：

先跑通闭环，再增加复杂度。

---

# 五、Agent 角色设计

## 1. Requirement Analyst

职责：

* 与用户多轮对话
* 需求澄清
* 补充缺失信息
* 发现需求冲突

输出：

PRD Draft

---

## 2. Requirement Freeze

职责：

* 生成正式 PRD
* 生成版本号
* 等待用户确认

输出：

PRD v1.x

---

## 3. Project Planner

职责：

* Epic 拆解
* Task 拆解
* DAG 依赖分析
* 开发顺序规划

工具：

* Memory MCP

---

## 4. Architect

职责：

* 架构设计
* 技术选型
* 模块设计
* 编码规范设计

工具：

* Memory MCP

---

## 5. Builder

职责：

* 开发代码
* 修改代码
* 重构代码

工具：

* OpenHands
* Memory MCP

---

## 6. QA

职责：

* 自动测试
* 功能验证
* 边界测试

工具：

* OpenHands

---

## 7. Bug Analyzer

职责：

* 分析失败原因
* 分析错误日志
* 提供修复建议

输出：

```json
{
  "root_cause": "",
  "location": "",
  "fix_suggestion": ""
}
```

---

## 8. Reviewer

职责：

* Code Review
* 架构检查
* 安全检查
* 规范检查

原则：

只审查，不写代码。

---

## 9. Memory

职责：

* 知识检索
* 知识沉淀
* 经验管理

---

# 六、Workflow 状态机

状态由 Ruflo 独立维护。

```text
Requirement_Analysis

Requirement_Freeze

Planning

Architecture

Building

Testing

Fixing

Reviewing

Done
```

异常状态：

```text
TEST_FAILED

REVIEW_FAILED

HUMAN_REVIEW_REQUIRED
```

---

# 七、自动修复机制

流程：

```text
Builder
 ↓

QA
 ↓

失败
 ↓

Bug Analyzer
 ↓

Builder
```

配置：

```yaml
max_retry: 3
```

超过最大次数：

```text
HUMAN_REVIEW_REQUIRED
```

暂停流程。

等待人工介入。

---

# 八、Git 策略

禁止直接修改主分支。

采用 Feature Branch 模式。

```text
main

feature/task-001

feature/task-002

feature/task-003
```

开发流程：

```text
Builder
 ↓

Feature Branch

 ↓

QA

 ↓

Reviewer

 ↓

Merge Main
```

---

# 九、Memory MCP

统一知识访问入口。

---

## memory.search()

```python
memory.search(
    query,
    project_id,
    top_k=10
)
```

用途：

* Planner 检索历史经验
* Architect 检索架构决策
* Builder 检索实现方案

---

## memory.save()

```python
memory.save(
    type,
    content,
    tags
)
```

保存：

* 架构决策
* Bug 经验
* 最佳实践
* 项目经验

---

## memory.decisions()

```python
memory.decisions(
    project_id
)
```

返回：

```text
统一JWT
统一Redis
统一MyBatis Plus
```

---

# 十、数据库设计

## projects

```sql
id
name
description
created_at
```

---

## requirements

```sql
id
project_id
version
content
created_at
```

---

## tasks

```sql
id
project_id
title
description
created_at
```

---

## memories

```sql
id
project_id
memory_type
content
tags
created_at
```

---

## memory_vectors

```sql
id
memory_id
embedding
```

---

## decisions

```sql
id
project_id
decision
reason
created_at
```

---

# 十一、Memory MCP 实现

目录：

```text
memory-mcp/

├── server
├── memory_service
├── embedding_service
├── vector_store
├── database
└── config
```

---

查询流程：

```text
memory.search()

 ↓

Embedding

 ↓

pgvector

 ↓

TopK

 ↓

返回结果
```

---

保存流程：

```text
memory.save()

 ↓

Embedding

 ↓

PostgreSQL

 ↓

pgvector
```

---

# 十二、项目目录结构

```text
AICompany/

├── projects/
├── workflow/
├── prompts/
├── memory-mcp/
├── database/
├── docker/
├── docs/
├── logs/
└── scripts/
```

---

# 十三、部署组件

基础环境：

* Docker Desktop
* Git
* Node.js 22 LTS

核心服务：

* PostgreSQL 16
* pgvector
* Ruflo
* OpenHands

模型：

* OpenAI API

---

# 十四、V2 演进路线

当达到：

* 10+ 项目
* 5000+ 任务
* 10000+ 知识节点

引入：

* Neo4j
* 知识图谱
* RePlanner
* 多模型路由
* 自动部署 Agent
* 跨项目知识网络

---

# 十五、最终架构总结

```text
Ruflo
+
OpenHands
+
Memory MCP
+
PostgreSQL
+
pgvector
+
Git
```

职责划分：

Ruflo：
负责编排和状态机

OpenHands：
负责代码执行

Memory MCP：
负责知识访问

PostgreSQL + pgvector：
负责长期记忆

Git：
负责代码版本管理

目标：

打造一个可持续迭代、可知识积累、可多项目协作的 AI 自动化开发团队。
