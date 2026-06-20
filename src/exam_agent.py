"""Rule-based final exam notes organizer."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any


COURSE_KEYWORDS = {
    "高等数学": ["极限", "导数", "微分", "积分", "级数", "泰勒", "偏导", "重积分"],
    "数据结构": ["链表", "栈", "队列", "树", "二叉树", "图", "排序", "查找", "复杂度"],
    "大学英语": ["grammar", "vocabulary", "reading", "translation", "writing", "听力", "阅读", "作文", "翻译"],
    "计算机组成原理": ["cpu", "cache", "流水线", "指令", "总线", "存储器", "补码", "寻址"],
    "中国近现代史纲要": ["鸦片战争", "辛亥革命", "五四", "抗日", "改革开放", "新民主主义", "近代史"],
}

STOPWORDS = {
    "the", "and", "with", "that", "this", "from", "for", "are", "was", "were",
    "一个", "我们", "需要", "可以", "以及", "进行", "掌握", "理解", "重点",
}


def guess_course(text: str) -> str:
    """Guess course name by keyword hits."""
    lower = text.lower()
    scores: dict[str, int] = {}
    for course, keywords in COURSE_KEYWORDS.items():
        scores[course] = sum(lower.count(keyword.lower()) for keyword in keywords)

    best_course, best_score = max(scores.items(), key=lambda item: item[1])
    return best_course if best_score > 0 else "通用课程复习资料"


def extract_keywords(text: str) -> list[str]:
    """Extract frequent Chinese or English study keywords."""
    chinese_terms = re.findall(r"[\u4e00-\u9fff]{2,8}", text)
    english_terms = re.findall(r"[A-Za-z][A-Za-z0-9_+\-]{2,}", text.lower())
    tokens = [token for token in chinese_terms + english_terms if token not in STOPWORDS]
    counts = Counter(tokens)
    return [word for word, _ in counts.most_common(12)]


def split_topics(text: str) -> list[str]:
    """Split notes into chapter or topic clues."""
    topics: list[str] = []
    for line in text.splitlines():
        stripped = line.strip(" #*-`\t")
        if not stripped:
            continue
        if re.match(r"^(第[一二三四五六七八九十0-9]+[章节]|chapter\s+\d+|\d+[.、])", stripped, re.I):
            topics.append(stripped)
        elif len(stripped) <= 32 and any(word in stripped for word in ("章", "节", "专题", "重点", "复习")):
            topics.append(stripped)
    if not topics:
        keywords = extract_keywords(text)
        topics = [f"专题：{keyword}" for keyword in keywords[:6]]
    return _dedupe(topics)[:10]


def build_review_plan(text: str) -> dict[str, Any]:
    """Build a practical review checklist and 3-day sprint plan."""
    course = guess_course(text)
    keywords = extract_keywords(text)
    topics = split_topics(text)
    exam_focus = _exam_focus(course, keywords, text)

    return {
        "course": course,
        "topics": topics,
        "keywords": keywords,
        "exam_focus": exam_focus,
        "tasks": {
            "待背诵": _memory_tasks(course, keywords),
            "待刷题": _practice_tasks(course, topics),
            "待整理": _organize_tasks(topics),
        },
        "three_day_plan": _three_day_plan(course, topics, exam_focus),
    }


def _exam_focus(course: str, keywords: list[str], text: str) -> list[str]:
    focus: list[str] = []
    if course == "高等数学":
        focus.extend(["公式适用条件", "典型题型解法步骤", "易错计算和定义域"])
    elif course == "数据结构":
        focus.extend(["核心结构的操作过程", "时间复杂度分析", "手写代码与边界条件"])
    elif course == "大学英语":
        focus.extend(["高频词汇和固定搭配", "作文模板", "阅读题定位方法"])
    elif course == "计算机组成原理":
        focus.extend(["概念对比题", "计算题步骤", "指令与存储系统流程"])
    elif course == "中国近现代史纲要":
        focus.extend(["时间线", "重要事件原因和影响", "人物与会议对应关系"])
    else:
        focus.extend(["老师反复强调的概念", "章节标题对应的大题", "错题中重复出现的知识点"])

    if re.search(r"必考|重点|考试|题型|简答|计算|证明", text):
        focus.append("资料中标记为“重点/必考/题型”的内容优先复习")
    focus.extend([f"围绕关键词“{word}”整理定义、例题和易错点" for word in keywords[:3]])
    return _dedupe(focus)[:8]


def _memory_tasks(course: str, keywords: list[str]) -> list[str]:
    base = [f"背诵关键词：{word}" for word in keywords[:5]]
    if course in {"中国近现代史纲要", "大学英语"}:
        base.append("整理一页核心概念/作文模板速记表")
    return base or ["整理需要背诵的定义、公式或模板"]


def _practice_tasks(course: str, topics: list[str]) -> list[str]:
    if course in {"高等数学", "数据结构", "计算机组成原理"}:
        return [f"针对“{topic}”完成 3 道典型题并复盘错误" for topic in topics[:4]]
    return [f"围绕“{topic}”做一组选择/简答/阅读练习" for topic in topics[:4]]


def _organize_tasks(topics: list[str]) -> list[str]:
    return [
        "把资料拆成“会 / 不熟 / 不会”三类",
        "为每个主题补 1 个例题或记忆提示",
        *[f"整理“{topic}”的考点卡片" for topic in topics[:3]],
    ]


def _three_day_plan(course: str, topics: list[str], exam_focus: list[str]) -> list[dict[str, str]]:
    topic_text = "、".join(topics[:4]) if topics else "全部核心主题"
    focus_text = "；".join(exam_focus[:3]) if exam_focus else "基础概念和典型题"
    return [
        {
            "day": "Day 1",
            "goal": "建立复习框架",
            "tasks": f"通读资料，标出不会的内容；整理课程 {course} 的主题列表：{topic_text}。",
        },
        {
            "day": "Day 2",
            "goal": "集中突破高频考点",
            "tasks": f"围绕 {focus_text} 做题或背诵；每个错点写一句原因。",
        },
        {
            "day": "Day 3",
            "goal": "模拟检查和查漏补缺",
            "tasks": "用 60-90 分钟做一套综合练习；最后只看错题、公式、时间线和易混概念。",
        },
    ]


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result

