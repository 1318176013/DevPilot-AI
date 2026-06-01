# Memory-MCP-Design.md

# AI Company Core V1

## Memory MCP 技术设计文档

---

# 一、设计目标

Memory MCP 是整个 AI Company Core 的统一知识访问层。

目标：

* 为所有 Agent 提供统一知识访问接口
* 实现项目知识隔离
* 实现历史经验复用
* 实现 Bug 经验复用
* 实现架构决策沉淀
* 为未来 Neo4j 知识图谱升级预留接口

---

# 二、架构设计

```text
Planner
Architect
Builder
Reviewer
Memory Agent

        │

        ▼

     Memory MCP

        │

        ▼

 PostgreSQL + pgvector
```

未来升级：

```text
Planner
Architect
Builder
Reviewer

        │

        ▼

     Memory MCP

      ┌───┴────┐

      ▼        ▼

PostgreSQL   Neo4j
```

Agent 永远不直接访问数据库。

统一通过 Memory MCP。

---

# 三、职责边界

## Memory MCP 负责

* 知识查询
* 知识保存
* 向量检索
* 决策查询
* 标签管理
* 项目隔离

---

## Memory MCP 不负责

* Workflow
* Agent 调度
* 状态管理
* 代码执行

这些职责属于 Ruflo。

---

# 四、项目隔离机制

每条知识必须绑定：

```json
{
  "project_id":"renqing",
  "namespace":"renqing",
  "content":"..."
}
```

---

## 检索规则

默认：

```python
memory.search(
    project_id="renqing"
)
```

仅检索当前项目。

---

## 未来跨项目

支持：

```python
memory.search(
    project_id="renqing",
    include_shared=True
)
```

检索：

* 当前项目
* 公共知识

---

# 五、数据库设计

## projects

```sql
CREATE TABLE projects
(
    id UUID PRIMARY KEY,
    name VARCHAR(200),
    description TEXT,
    created_at TIMESTAMP
);
```

---

## memories

```sql
CREATE TABLE memories
(
    id UUID PRIMARY KEY,

    project_id UUID,

    namespace VARCHAR(100),

    memory_type VARCHAR(50),

    title VARCHAR(500),

    content TEXT,

    tags JSONB,

    importance INTEGER DEFAULT 5,

    created_by VARCHAR(100),

    created_at TIMESTAMP
);
```

---

## memory_vectors

```sql
CREATE TABLE memory_vectors
(
    memory_id UUID PRIMARY KEY,

    embedding VECTOR(1536)
);
```

---

## decisions

```sql
CREATE TABLE decisions
(
    id UUID PRIMARY KEY,

    project_id UUID,

    category VARCHAR(50),

    decision TEXT,

    reason TEXT,

    created_at TIMESTAMP
);
```

---

## bug_patterns

```sql
CREATE TABLE bug_patterns
(
    id UUID PRIMARY KEY,

    project_id UUID,

    error_signature TEXT,

    root_cause TEXT,

    solution TEXT,

    created_at TIMESTAMP
);
```

---

# 六、知识分类

建议统一分类。

## architecture

架构设计

例如：

```text
统一JWT认证
统一REST风格API
统一DDD架构
```

---

## decision

架构决策

例如：

```text
选择MyBatis Plus
选择Redis缓存
```

---

## best_practice

最佳实践

例如：

```text
Controller禁止直接访问Mapper
```

---

## bug_fix

Bug经验

例如：

```text
JWT过期导致401
```

---

## implementation

实现方案

例如：

```text
微信登录实现方案
```

---

# 七、Embedding 策略

推荐模型：

OpenAI Embedding API

推荐：

```text
text-embedding-3-small
```

优点：

* 成本低
* 效果稳定
* 检索足够

---

# 八、Memory API 设计

## search

查询知识

### 请求

```json
{
  "query":"微信登录",
  "project_id":"renqing",
  "top_k":10
}
```

---

### 返回

```json
{
  "results":[
    {
      "type":"decision",
      "content":"统一采用JWT"
    }
  ]
}
```

---

## save

保存知识

### 请求

```json
{
  "project_id":"renqing",
  "type":"bug_fix",
  "content":"JWT过期导致401"
}
```

---

### 返回

```json
{
  "success":true
}
```

---

## decisions

查询决策

### 请求

```json
{
  "project_id":"renqing"
}
```

---

### 返回

```json
{
  "decisions":[]
}
```

---

## related

预留接口

未来 Neo4j 使用

### 请求

```json
{
  "memory_id":"xxx"
}
```

---

# 九、memory.search() 实现

## Step1

接收查询

```text
微信登录设计
```

---

## Step2

生成向量

```python
embedding = client.embeddings.create(
    model="text-embedding-3-small",
    input=query
)
```

---

## Step3

向量检索

```sql
SELECT
    m.*
FROM memories m
JOIN memory_vectors v
ON m.id = v.memory_id

ORDER BY
v.embedding <=> :query_embedding

LIMIT 10;
```

---

## Step4

结果排序

排序依据：

```text
向量相似度
+
importance
+
时间衰减
```

---

## Step5

返回结果

```json
{
  "results":[]
}
```

---

# 十、memory.save() 实现

## 输入

```json
{
  "type":"bug_fix",
  "content":"JWT过期导致401"
}
```

---

## Step1

生成 Embedding

```python
embedding = create_embedding(content)
```

---

## Step2

写 memories

```sql
INSERT INTO memories(...)
```

---

## Step3

写 memory_vectors

```sql
INSERT INTO memory_vectors(...)
```

---

## Step4

完成

---

# 十一、知识沉淀策略

任务完成后：

Reviewer 通过

↓

Memory Agent 触发

↓

提取：

```text
关键决策

关键Bug

关键实现方案

最佳实践
```

↓

保存 Memory

---

# 十二、知识召回策略

Planner：

```python
memory.search()
```

查询：

```text
历史类似需求
```

---

Architect：

```python
memory.decisions()
```

查询：

```text
架构决策
```

---

Builder：

```python
memory.search()
```

查询：

```text
历史实现方案
```

---

Reviewer：

```python
memory.search()
```

查询：

```text
历史规范
```

---

# 十三、MCP Server 实现

目录：

```text
memory-mcp/

├── app/
│
├── api/
│   ├── search.py
│   ├── save.py
│   ├── decisions.py
│
├── services/
│   ├── embedding_service.py
│   ├── memory_service.py
│
├── repositories/
│   ├── memory_repository.py
│
├── models/
│
├── config/
│
└── main.py
```

---

# 十四、服务接口

建议：

```text
http://localhost:8001
```

提供：

```text
POST /memory/search

POST /memory/save

POST /memory/decisions

POST /memory/related
```

---

# 十五、未来升级路线

V1：

```text
PostgreSQL
+
pgvector
```

---

V2：

增加：

Neo4j

```text
PostgreSQL
+
pgvector
+
Neo4j
```

---

升级后：

memory.search()

内部流程：

```text
向量召回

↓

知识节点

↓

Neo4j关系扩展

↓

返回增强结果
```

对 Ruflo 和 Agent 无需改动。

---

# 十六、最终原则

Memory MCP 是唯一知识入口。

所有 Agent：

```text
Planner
Architect
Builder
Reviewer
```

只能通过：

```python
memory.search()

memory.save()

memory.decisions()
```

访问知识。

不得直接访问：

```text
PostgreSQL

Neo4j
```

从而保证：

* 统一接口
* 统一权限
* 统一检索逻辑
* 后续平滑升级知识图谱
