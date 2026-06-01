# Ruflo-Workflow-Design.md

# AI Company Core V1

## Ruflo 工作流与多 Agent 编排设计文档

---

# 一、设计目标

Ruflo 是整个 AI Company Core 的唯一编排中心。

职责：

* Workflow 管理
* Agent 调度
* 状态管理
* 上下文传递
* 重试机制
* Human Review 管理

不负责：

* 代码执行（OpenHands）
* 知识存储（Memory MCP）
* 数据存储（PostgreSQL）

---

# 二、总体架构

```text id="r6q1w9"
User
 │
 ▼

Requirement Analyst

 │
 ▼

Requirement Freeze

 │
 ▼

Project Planner

 │
 ▼

Architect

 │
 ▼

Builder

 │
 ▼

QA

 │
 ▼

Bug Analyzer

 │
 ├──── Retry < 3 ────► Builder
 │
 └──── Retry >= 3 ───► Human Review

 │
 ▼

Reviewer

 │
 ▼

Memory Save

 │
 ▼

Done
```

---

# 三、核心状态机

所有状态由 Ruflo 管理。

---

## Requirement Analysis

需求分析阶段

负责人：

```text id="6hdz1o"
Requirement Analyst
```

目标：

```text id="yujxii"
需求完整度 >= 90%
```

未达到：

```text id="nrmh98"
继续提问
```

达到：

```text id="buz2oe"
进入 Requirement Freeze
```

---

## Requirement Freeze

负责人：

```text id="0qck08"
Requirement Freeze
```

输出：

```text id="l5yxqj"
PRD v1.0
```

等待：

```text id="y5v4s1"
用户确认
```

确认后：

```text id="f8qebx"
进入 Planning
```

---

## Planning

负责人：

```text id="6vwg0l"
Project Planner
```

执行：

```python id="b2h55r"
memory.search()
```

查询：

* 历史项目
* 历史任务
* 历史经验

输出：

```json id="fokg77"
{
  "epics": [],
  "tasks": [],
  "dependencies": []
}
```

进入：

```text id="k87z49"
Architecture
```

---

## Architecture

负责人：

```text id="e7i6ya"
Architect
```

执行：

```python id="6a5sov"
memory.decisions()
```

查询：

* 历史架构决策
* 技术规范

输出：

```json id="lf0kew"
{
  "architecture": {},
  "modules": [],
  "database": {}
}
```

进入：

```text id="sbmduw"
Building
```

---

## Building

负责人：

```text id="7z7f1v"
Builder
```

工具：

```text id="mp3mra"
OpenHands
Memory MCP
```

执行：

```text id="5zxdt9"
代码开发
代码修改
代码重构
```

输出：

```json id="y05wqy"
{
  "status":"SUCCESS",
  "files_changed":[]
}
```

进入：

```text id="yj91zr"
Testing
```

---

## Testing

负责人：

```text id="8jq3p8"
QA
```

工具：

```text id="r9h9jh"
OpenHands
```

执行：

```text id="lwx0w6"
单元测试
集成测试
功能验证
边界测试
```

---

测试通过：

```text id="0t22j0"
进入 Reviewing
```

---

测试失败：

```text id="u6b1jd"
进入 Fixing
```

---

## Fixing

负责人：

```text id="w6dr26"
Bug Analyzer
```

输入：

```text id="k0ehjr"
测试日志
错误日志
Stack Trace
```

输出：

```json id="ob0djs"
{
  "root_cause":"",
  "location":"",
  "fix_suggestion":"",
  "confidence":0.95
}
```

---

# 四、自动修复机制

---

## Retry Counter

由 Ruflo 管理：

```json id="0dmpm6"
{
  "retry_count": 0
}
```

---

## 修复流程

```text id="t2v1h6"
Builder

 ↓

QA

 ↓

Fail

 ↓

Bug Analyzer

 ↓

Builder
```

---

## 最大重试次数

```yaml id="8fzskl"
max_retry: 3
```

---

条件：

```text id="apikjl"
retry_count < 3
```

返回：

```text id="c6lrj9"
Builder
```

继续修复。

---

条件：

```text id="r0vsk0"
retry_count >= 3
```

进入：

```text id="vjlwmv"
Human Review
```

---

# 五、Human Review

状态：

```text id="v9mzha"
HUMAN_REVIEW_REQUIRED
```

---

Ruflo保存：

```text id="8yv4xv"
任务上下文
错误日志
测试结果
修复历史
```

---

等待人工处理。

---

人工处理完成：

```text id="yplb3x"
Resume Workflow
```

恢复流程。

---

# 六、Reviewing

负责人：

```text id="wq3oel"
Reviewer
```

职责：

* Code Review
* 架构 Review
* 安全检查
* 规范检查

---

原则：

```text id="rjlwm4"
只审查

不修改代码
```

---

输出：

```json id="7nn2z0"
{
  "approved": true,
  "comments":[]
}
```

---

通过：

```text id="styk3q"
Memory Save
```

---

拒绝：

```text id="v0y2d9"
返回 Builder
```

---

# 七、Memory Save

负责人：

```text id="s1v9q4"
Memory Agent
```

---

触发条件：

```text id="k03j40"
Reviewer Approved
```

---

提取：

```text id="qwe7gf"
关键架构决策

关键实现方案

最佳实践

关键Bug经验
```

---

调用：

```python id="p7yds6"
memory.save()
```

---

保存到：

```text id="3zdh3n"
PostgreSQL
pgvector
```

---

完成：

```text id="53h8m6"
Done
```

---

# 八、多项目隔离机制

每个项目必须存在：

```text id="z9q6j5"
PROJECT_CONTEXT.md
```

---

示例：

```yaml id="jtx5wq"
project_id: renqing

project_name: 人情往来

tech_stack:
  - SpringBoot
  - MyBatisPlus
  - MySQL

shared_tags:
  - auth
  - user
```

---

作用：

* 项目标识
* 技术栈说明
* 共享知识范围

---

# 九、上下文传递机制

Ruflo负责传递上下文。

统一格式：

```json id="u5g67v"
{
  "project": {},
  "requirements": {},
  "architecture": {},
  "task": {},
  "memory": []
}
```

---

每个 Agent 只能看到：

```text id="jsqxwb"
当前任务需要的信息
```

避免上下文污染。

---

# 十、Memory 检索规则

---

## Planner

调用：

```python id="z0w4cm"
memory.search()
```

检索：

```text id="6u8u0g"
类似项目
历史经验
历史任务
```

---

## Architect

调用：

```python id="y7b8do"
memory.decisions()
```

检索：

```text id="1jpl5r"
历史架构决策
```

---

## Builder

调用：

```python id="e8ajql"
memory.search()
```

检索：

```text id="jlwmsh"
实现方案
最佳实践
历史Bug
```

---

## Reviewer

调用：

```python id="o16tvx"
memory.search()
```

检索：

```text id="n8vopn"
历史规范
Review经验
```

---

# 十一、Git Workflow

采用 Git Flow 简化版。

---

禁止：

```text id="o64jij"
直接修改 main
```

---

允许：

```text id="4w30qt"
feature/task-001

feature/task-002

feature/task-003
```

---

流程：

```text id="sh7k20"
Builder

 ↓

Feature Branch

 ↓

Commit

 ↓

QA

 ↓

Reviewer

 ↓

Merge Main
```

---

# 十二、Builder 权限控制

允许：

```text id="n1i3wh"
读代码

写代码

执行测试

Git Commit
```

---

禁止：

```text id="9g9pqz"
修改Workflow

修改Memory MCP

修改Ruflo配置
```

---

# 十三、QA 权限控制

允许：

```text id="dcew3q"
运行测试

读取日志
```

---

禁止：

```text id="a0mjlwm"
修改代码
```

---

# 十四、Reviewer 权限控制

允许：

```text id="q2gk7k"
读取代码

读取架构
```

---

禁止：

```text id="ypti9v"
修改代码
```

---

# 十五、失败恢复机制

Ruflo 保存：

```json id="zfj1v8"
{
  "workflow_id":"",
  "current_state":"",
  "retry_count":0,
  "context":{}
}
```

---

异常退出：

```text id="jnnuk6"
恢复最近状态
```

继续执行。

---

# 十六、V2 演进路线

增加：

## RePlanner

职责：

```text id="0jig7u"
自动重新规划任务
```

---

## Neo4j

职责：

```text id="0upjxg"
知识图谱
关系推理
```

---

## DevOps Agent

职责：

```text id="hzj6ca"
自动部署
自动发布
```

---

## Multi Model Router

职责：

```text id="s6y7iy"
GPT
Claude
Gemini
DeepSeek

自动选择
```

---

# 十七、最终原则

## Ruflo

负责：

```text id="9wfsq7"
Workflow
状态机
Agent编排
重试控制
```

---

## OpenHands

负责：

```text id="tih6vw"
代码执行
测试执行
Git操作
```

---

## Memory MCP

负责：

```text id="ecg0mz"
知识查询
知识保存
知识召回
```

---

## PostgreSQL + pgvector

负责：

```text id="5bmeq0"
长期记忆
向量检索
```

---

## Git

负责：

```text id="p6tbk3"
代码唯一事实源
(Source of Truth)
```

---

最终形成：

```text id="wpcxj7"
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

构建一个可持续演进、支持多项目协同、具备知识积累能力的 AI 自动化开发团队。
