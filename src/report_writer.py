"""Markdown report helpers for Campus Agent Lab."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any


OUTPUT_DIR = Path("outputs")


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def save_report(prefix: str, markdown: str) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{prefix}_{timestamp()}.md"
    path.write_text(markdown, encoding="utf-8")
    return path


def readme_report(data: dict[str, Any], source: str = "") -> str:
    lines = [
        "# GitHub README 速读报告",
        "",
        f"- 来源：{source or '手动输入 / 示例数据'}",
        f"- 项目一句话总结：{data.get('one_sentence', '')}",
        f"- 项目解决的问题：{data.get('problem', '')}",
        "",
        "## 主要技术栈",
        *_bullet_list(data.get("tech_stack", [])),
        "",
        "## 安装/运行方式",
        *_bullet_list(data.get("install_run", [])),
        "",
        "## 核心目录/文件线索",
        *_bullet_list(data.get("core_files", [])),
        "",
        "## 适合学生学习的点",
        *_bullet_list(data.get("learning_points", [])),
        "",
        "## 适合新手贡献的方向",
        *_bullet_list(data.get("beginner_contributions", [])),
        "",
        "## 风险提示",
        *_bullet_list(data.get("risks", [])),
        "",
    ]
    return "\n".join(lines)


def code_report(result: dict[str, Any]) -> str:
    lines = [
        "# Java/C 实验代码检查报告",
        "",
        f"- 文件名：{result.get('filename')}",
        f"- 识别语言：{result.get('language')}",
        "",
        "## 检查结果",
    ]

    issues = result.get("issues", [])
    if not issues:
        lines.append("- 未发现明显问题")
    for issue in issues:
        line = issue.get("line")
        line_text = f"第 {line} 行" if line else "无法定位行号"
        lines.extend(
            [
                f"### [{issue.get('severity')}] {issue.get('message')}",
                "",
                f"- 位置：{line_text}",
                f"- 最小修改建议：{issue.get('suggestion')}",
                f"- 为什么错：{issue.get('explanation')}",
                "",
            ]
        )
    return "\n".join(lines)


def exam_report(plan: dict[str, Any]) -> str:
    lines = [
        "# 期末资料整理报告",
        "",
        f"- 课程名称猜测：{plan.get('course')}",
        "",
        "## 章节/主题列表",
        *_bullet_list(plan.get("topics", [])),
        "",
        "## 高频关键词",
        *_bullet_list(plan.get("keywords", [])),
        "",
        "## 可能的考试重点",
        *_bullet_list(plan.get("exam_focus", [])),
        "",
        "## 复习任务",
    ]
    tasks = plan.get("tasks", {})
    for title, items in tasks.items():
        lines.extend([f"### {title}", "", *_bullet_list(items), ""])

    lines.extend(["## 3 天冲刺复习计划", ""])
    for item in plan.get("three_day_plan", []):
        lines.extend(
            [
                f"### {item.get('day')}：{item.get('goal')}",
                "",
                str(item.get("tasks", "")),
                "",
            ]
        )
    return "\n".join(lines)


def _bullet_list(items: list[Any]) -> list[str]:
    return [f"- {item}" for item in items] if items else ["- 暂无"]

