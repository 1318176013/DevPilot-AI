from __future__ import annotations


def structure_requirement(title: str, raw_requirement: str) -> dict[str, object]:
    normalized = raw_requirement.strip()
    acceptance_criteria = [
        "需求已被结构化保存",
        "可基于结构化需求生成 DAG 节点",
        "后续执行结果可被验证和追踪",
    ]

    if any(keyword in normalized.lower() for keyword in ["ui", "页面", "前端", "界面"]):
        acceptance_criteria.append("相关界面可完成主要用户操作")
    if any(keyword in normalized.lower() for keyword in ["api", "接口", "后端"]):
        acceptance_criteria.append("相关 API 可被调用并返回预期结果")
    if any(keyword in normalized.lower() for keyword in ["test", "测试", "验证", "lint"]):
        acceptance_criteria.append("提供可重复执行的验证方式")

    return {
        "title": title.strip(),
        "goal": normalized,
        "scope": "MVP 自动结构化结果：聚焦可实现、可验证、可追踪的最小交付范围",
        "out_of_scope": ["复杂多 Agent 并行协作", "生产级审批流", "自动部署到生产环境"],
        "acceptance_criteria": acceptance_criteria,
        "clarification_questions": [],
        "suitability_score": 0.82,
        "risk_assessment": {
            "level": "medium",
            "items": ["需求细节可能不足，执行前需要结合项目上下文确认影响范围"],
        },
    }
