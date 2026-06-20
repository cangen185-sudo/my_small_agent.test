from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.code_checker import check_code
from src.exam_agent import build_review_plan
from src.github_reader import analyze_readme, fetch_readme, parse_github_url
from src.report_writer import code_report, exam_report, readme_report, save_report


SAMPLES_DIR = Path("samples")


st.set_page_config(page_title="Campus Agent Lab", layout="wide")


def main() -> None:
    _ensure_defaults()
    st.title("Campus Agent Lab")
    st.caption("面向软件工程学生的校园学习 Agent 小实验室：能跑、能看、能截图、能写进简历。")

    st.sidebar.markdown("### 工具入口")
    tool = st.sidebar.radio(
        "选择工具",
        ["GitHub README 速读器", "Java/C 实验代码检查器", "期末资料整理 Agent"],
    )
    st.sidebar.markdown("---")
    st.sidebar.info("当前 MVP 不需要 API Key。后续可以接入 OPENAI_API_KEY 提升总结质量。")

    if tool == "GitHub README 速读器":
        render_github_reader()
    elif tool == "Java/C 实验代码检查器":
        render_code_checker()
    else:
        render_exam_agent()


def render_github_reader() -> None:
    st.header("GitHub README 速读器")
    st.write("输入 GitHub 仓库链接自动读取 README；如果联网失败，可以粘贴文本或加载示例。")

    st.text_input("GitHub 仓库链接", placeholder="https://github.com/owner/repo", key="readme_repo_url")
    st.text_area(
        "README 文本（可选）",
        height=260,
        placeholder="联网失败时，把 README 内容粘贴到这里。",
        key="readme_text",
    )

    col1, col2 = st.columns([1, 1])
    col1.button("加载示例 README", on_click=_load_readme_sample)
    run = col2.button("生成速读报告", type="primary")

    if run:
        text = st.session_state.get("readme_text", "").strip()
        source = st.session_state.get("readme_repo_url", "").strip()
        if source:
            try:
                owner, repo = parse_github_url(source)
                text = fetch_readme(owner, repo)
                st.session_state["readme_text"] = text
                st.success("已从 GitHub 获取 README。")
            except Exception as exc:
                st.warning(f"联网读取失败，改用粘贴/示例文本：{exc}")

        if not text:
            st.error("请先输入仓库链接，或粘贴/加载 README 文本。")
            return

        result = analyze_readme(text)
        st.session_state["readme_result"] = result
        st.session_state["readme_report_md"] = readme_report(result, source)

    if "readme_result" in st.session_state:
        _show_readme_result(st.session_state["readme_result"])
        _report_actions("readme_report", st.session_state["readme_report_md"], "save_readme_report")


def render_code_checker() -> None:
    st.header("Java/C 实验代码检查器")
    st.write("只做静态检查和编译检查，不运行用户提交的 C/Java 程序。")

    uploaded = st.file_uploader("上传 .c 或 .java 文件", type=["c", "java", "txt"], key="code_upload")
    if uploaded:
        st.session_state["code_filename"] = uploaded.name
        st.session_state["code_text"] = uploaded.getvalue().decode("utf-8", errors="replace")

    st.text_input("文件名", key="code_filename")
    st.text_area("代码内容", height=340, key="code_text")

    col1, col2, col3 = st.columns([1, 1, 1])
    col1.button("加载 C 示例", on_click=_load_code_sample, args=("buggy_hello.c",))
    col2.button("加载 Java 示例", on_click=_load_code_sample, args=("buggy_list.java",))
    run = col3.button("检查代码", type="primary")

    if run:
        filename = st.session_state.get("code_filename", "Main.java")
        code = st.session_state.get("code_text", "")
        if not code.strip():
            st.error("请上传、粘贴或加载一段 C/Java 代码。")
            return
        result = check_code(filename, code)
        st.session_state["code_result"] = result
        st.session_state["code_report_md"] = code_report(result)

    if "code_result" in st.session_state:
        _show_code_result(st.session_state["code_result"])
        _report_actions("code_check_report", st.session_state["code_report_md"], "save_code_report")


def render_exam_agent() -> None:
    st.header("期末资料整理 Agent")
    st.write("粘贴 txt / md 复习资料，自动整理成复习清单和 3 天冲刺计划。")

    uploaded = st.file_uploader("上传 txt / md 文件", type=["txt", "md"], key="exam_upload")
    if uploaded:
        st.session_state["exam_text"] = uploaded.getvalue().decode("utf-8", errors="replace")

    st.text_area("复习资料内容", height=340, key="exam_text")

    col1, col2 = st.columns([1, 1])
    col1.button("加载期末资料示例", on_click=_load_exam_sample)
    run = col2.button("生成复习计划", type="primary")

    if run:
        text = st.session_state.get("exam_text", "")
        if not text.strip():
            st.error("请上传、粘贴或加载一份复习资料。")
            return
        plan = build_review_plan(text)
        st.session_state["exam_result"] = plan
        st.session_state["exam_report_md"] = exam_report(plan)

    if "exam_result" in st.session_state:
        _show_exam_result(st.session_state["exam_result"])
        _report_actions("exam_review_report", st.session_state["exam_report_md"], "save_exam_report")


def _show_readme_result(data: dict[str, object]) -> None:
    st.subheader("速读结果")
    st.info(str(data["one_sentence"]))
    st.write("**项目解决的问题**")
    st.write(data["problem"])
    _list_section("主要技术栈", data["tech_stack"])
    _list_section("安装/运行方式", data["install_run"])
    _list_section("核心目录/文件线索", data["core_files"])
    _list_section("适合学生学习的点", data["learning_points"])
    _list_section("适合新手贡献的方向", data["beginner_contributions"])
    _list_section("风险提示", data["risks"])


def _show_code_result(result: dict[str, object]) -> None:
    st.subheader("检查结果")
    st.write(f"文件：`{result['filename']}`，识别语言：`{result['language']}`")
    for issue in result.get("issues", []):
        severity = issue["severity"]
        line = issue["line"] or "无法定位"
        with st.container(border=True):
            st.write(f"**[{severity}] {issue['message']}**")
            st.write(f"位置：{line}")
            st.write(f"建议：{issue['suggestion']}")
            st.caption(f"为什么错：{issue['explanation']}")


def _show_exam_result(plan: dict[str, object]) -> None:
    st.subheader("复习计划")
    st.info(f"课程名称猜测：{plan['course']}")
    _list_section("章节/主题列表", plan["topics"])
    _list_section("高频关键词", plan["keywords"])
    _list_section("可能的考试重点", plan["exam_focus"])

    st.write("**复习任务**")
    tasks = plan["tasks"]
    for title, items in tasks.items():
        _list_section(title, items)

    st.write("**3 天冲刺复习计划**")
    for day in plan["three_day_plan"]:
        with st.container(border=True):
            st.write(f"**{day['day']}：{day['goal']}**")
            st.write(day["tasks"])


def _list_section(title: str, items: object) -> None:
    st.write(f"**{title}**")
    if isinstance(items, list):
        for item in items:
            st.write(f"- {item}")
    else:
        st.write(items)


def _report_actions(prefix: str, markdown: str, save_key: str) -> None:
    st.subheader("导出报告")
    st.download_button(
        "下载 Markdown 报告",
        data=markdown.encode("utf-8"),
        file_name=f"{prefix}.md",
        mime="text/markdown",
        key=f"download_{prefix}",
    )
    if st.button("保存到 outputs/", key=save_key):
        path = save_report(prefix, markdown)
        st.success(f"已保存：{path}")


def _read_sample(filename: str) -> str:
    return (SAMPLES_DIR / filename).read_text(encoding="utf-8")


def _load_readme_sample() -> None:
    st.session_state["readme_text"] = _read_sample("sample_readme.md")
    st.session_state["readme_repo_url"] = ""
    st.session_state.pop("readme_result", None)
    st.session_state.pop("readme_report_md", None)


def _load_code_sample(filename: str) -> None:
    st.session_state["code_filename"] = filename
    st.session_state["code_text"] = _read_sample(filename)
    st.session_state.pop("code_result", None)
    st.session_state.pop("code_report_md", None)


def _load_exam_sample() -> None:
    st.session_state["exam_text"] = _read_sample("final_exam_notes.md")
    st.session_state.pop("exam_result", None)
    st.session_state.pop("exam_report_md", None)


def _ensure_defaults() -> None:
    defaults = {
        "readme_repo_url": "",
        "readme_text": "",
        "code_filename": "buggy_hello.c",
        "code_text": "",
        "exam_text": "",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


if __name__ == "__main__":
    main()
