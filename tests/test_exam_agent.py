from src.exam_agent import build_review_plan, extract_keywords, guess_course, split_topics


def test_guess_course_data_structure() -> None:
    text = "链表 栈 队列 二叉树 图 排序 查找 复杂度"
    assert guess_course(text) == "数据结构"


def test_extract_keywords_returns_common_terms() -> None:
    text = "复杂度 复杂度 二叉树 二叉树 二叉树 queue stack"
    keywords = extract_keywords(text)
    assert "二叉树" in keywords


def test_build_review_plan_has_three_days() -> None:
    text = """
    # 数据结构
    第一章 绪论
    重点：复杂度、链表、栈、队列、二叉树。
    """
    plan = build_review_plan(text)
    assert plan["course"] == "数据结构"
    assert len(plan["three_day_plan"]) == 3
    assert split_topics(text)

