"""Rule-based GitHub README reader and analyzer."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

import requests


README_CANDIDATES = ("README.md", "readme.md", "README.MD", "README.txt")


def parse_github_url(url: str) -> tuple[str, str]:
    """Parse a GitHub repository URL into owner and repo."""
    cleaned = url.strip()
    parsed = urlparse(cleaned)

    if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
        raise ValueError("请输入标准 GitHub 仓库链接，例如 https://github.com/owner/repo")

    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 2:
        raise ValueError("GitHub 链接中没有识别到 owner/repo")

    owner, repo = parts[0], parts[1]
    if repo.endswith(".git"):
        repo = repo[:-4]
    return owner, repo


def fetch_readme(owner: str, repo: str) -> str:
    """Fetch README content from common default branches."""
    branches = ("main", "master")
    errors: list[str] = []

    for branch in branches:
        for filename in README_CANDIDATES:
            url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{filename}"
            try:
                response = requests.get(url, timeout=8)
            except requests.RequestException as exc:
                errors.append(str(exc))
                continue

            if response.status_code == 200 and response.text.strip():
                return response.text

    detail = errors[-1] if errors else "未在 main/master 分支找到 README"
    raise RuntimeError(f"README 获取失败：{detail}")


def analyze_readme(text: str) -> dict[str, Any]:
    """Analyze README text with lightweight keyword and section rules."""
    normalized = text.strip()
    lines = [line.rstrip() for line in normalized.splitlines()]
    headings = _extract_headings(lines)
    tech_stack = _detect_tech_stack(normalized)
    install_steps = _extract_install_steps(lines)
    directories = _extract_directory_clues(lines)
    risks = _detect_risks(normalized, install_steps, tech_stack)

    return {
        "one_sentence": _build_one_sentence(lines, tech_stack),
        "problem": _infer_problem(normalized),
        "tech_stack": tech_stack or ["未明显识别，需要人工补充"],
        "install_run": install_steps or ["README 中没有明显安装/运行命令"],
        "core_files": directories or headings[:8] or ["未识别到目录或标题线索"],
        "learning_points": _student_learning_points(tech_stack, headings, normalized),
        "beginner_contributions": _beginner_contributions(normalized),
        "risks": risks,
    }


def _extract_headings(lines: list[str]) -> list[str]:
    headings: list[str] = []
    for line in lines:
        match = re.match(r"^\s{0,3}#{1,6}\s+(.+)", line)
        if match:
            headings.append(match.group(1).strip())
    return headings


def _detect_tech_stack(text: str) -> list[str]:
    patterns = {
        "Python": r"\bpython\b|pip install|requirements\.txt|pytest|streamlit|fastapi|django|flask",
        "JavaScript/TypeScript": r"\bjavascript\b|\btypescript\b|npm install|yarn|pnpm|react|vue|node\.js|next\.js",
        "Java": r"\bjava\b|maven|gradle|spring boot",
        "C/C++": r"\bc\+\+\b|\bcmake\b|\bgcc\b|\bg\+\+\b|#include\s*<",
        "Docker": r"\bdocker\b|docker-compose|Dockerfile",
        "Database": r"\bpostgres\b|\bmysql\b|\bsqlite\b|\bmongodb\b|\bredis\b",
        "AI/LLM": r"\bopenai\b|\bllm\b|\bgpt\b|langchain|embedding|rag",
    }
    found = [name for name, pattern in patterns.items() if re.search(pattern, text, re.I)]
    return found


def _extract_install_steps(lines: list[str]) -> list[str]:
    commands: list[str] = []
    command_patterns = (
        r"\bpip install\b",
        r"\bpython\b .*\.py",
        r"\bstreamlit run\b",
        r"\bnpm install\b",
        r"\bnpm run\b",
        r"\byarn\b",
        r"\bpnpm\b",
        r"\bdocker\b",
        r"\bmake\b",
        r"\bjava\b",
        r"\bmvn\b",
        r"\bgradle\b",
    )

    for line in lines:
        stripped = line.strip().strip("`")
        if any(re.search(pattern, stripped, re.I) for pattern in command_patterns):
            commands.append(stripped.lstrip("$ ").strip())

    return _dedupe(commands)[:10]


def _extract_directory_clues(lines: list[str]) -> list[str]:
    clues: list[str] = []
    for line in lines:
        stripped = line.strip()
        if re.search(r"(^|[\s`])([A-Za-z0-9_\-./]+/|[A-Za-z0-9_\-]+\.(py|js|ts|java|c|cpp|md|yml|yaml|json))", stripped):
            if len(stripped) <= 120:
                clues.append(stripped.strip("-*` "))
    return _dedupe(clues)[:12]


def _build_one_sentence(lines: list[str], tech_stack: list[str]) -> str:
    for line in lines:
        stripped = line.strip("# >*- `")
        if 20 <= len(stripped) <= 160 and not stripped.lower().startswith(("install", "usage", "example")):
            stack = f"（可能使用 {', '.join(tech_stack[:3])}）" if tech_stack else ""
            return f"{stripped}{stack}"
    return "这是一个需要结合 README 进一步人工确认定位的项目。"


def _infer_problem(text: str) -> str:
    lower = text.lower()
    if any(word in lower for word in ("manage", "dashboard", "admin", "monitor")):
        return "可能在解决管理、监控或可视化类问题。"
    if any(word in lower for word in ("chat", "agent", "llm", "assistant", "rag")):
        return "可能在解决智能问答、自动化助手或知识检索问题。"
    if any(word in lower for word in ("api", "server", "backend", "service")):
        return "可能在提供后端服务、接口封装或业务系统能力。"
    if any(word in lower for word in ("learn", "tutorial", "course", "example")):
        return "可能是教学、示例或学习型项目。"
    return "README 没有直接说明问题背景，建议补充项目目标和使用场景。"


def _student_learning_points(tech_stack: list[str], headings: list[str], text: str) -> list[str]:
    points = ["阅读 README 结构，学习如何描述项目目标、安装方式和使用示例"]
    if tech_stack:
        points.append(f"结合项目学习技术栈：{', '.join(tech_stack)}")
    if any(re.search(r"test|pytest|jest|unit", item, re.I) for item in headings) or re.search(r"\btest\b|pytest|jest", text, re.I):
        points.append("学习测试目录和最小测试用例的组织方式")
    if re.search(r"docker|deploy|ci|github actions", text, re.I):
        points.append("学习部署、容器化或 CI 自动化配置")
    return points


def _beginner_contributions(text: str) -> list[str]:
    ideas = [
        "补充更清晰的安装步骤和常见错误说明",
        "增加最小可运行示例和截图",
        "为核心函数补充单元测试",
    ]
    if "todo" in text.lower():
        ideas.insert(0, "从 README 中的 TODO 项挑选一个小功能完成")
    if not re.search(r"license", text, re.I):
        ideas.append("补充 License 或开源使用说明")
    return ideas


def _detect_risks(text: str, install_steps: list[str], tech_stack: list[str]) -> list[str]:
    risks: list[str] = []
    if len(text) < 500:
        risks.append("README 内容偏短，项目目标和使用方式可能不完整")
    if not install_steps:
        risks.append("未识别到安装/运行命令，新手复现成本可能较高")
    if not tech_stack:
        risks.append("未明显识别技术栈，依赖关系可能需要查看源码确认")
    if not re.search(r"test|pytest|jest|unittest", text, re.I):
        risks.append("未发现测试说明，代码质量保障情况未知")
    risks.append("最近维护情况需要打开 GitHub commits/issues 页面进一步确认")
    return risks


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        key = item.lower()
        if item and key not in seen:
            seen.add(key)
            result.append(item)
    return result

