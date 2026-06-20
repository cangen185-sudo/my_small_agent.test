from __future__ import annotations

import subprocess
import time
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
SCREENSHOT_DIR = ROOT / "docs" / "screenshots"
PORT = 8501
BASE_URL = f"http://localhost:{PORT}"


def wait_for_app() -> subprocess.Popen[str]:
    process = subprocess.Popen(
        [
            "python",
            "-m",
            "streamlit",
            "run",
            "app.py",
            "--server.headless=true",
            f"--server.port={PORT}",
        ],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    time.sleep(4)
    return process


def click_button(page: Page, name: str) -> None:
    page.get_by_role("button", name=name).click()
    page.wait_for_timeout(800)


def select_tool(page: Page, name: str) -> None:
    page.get_by_text(name, exact=True).click()
    page.wait_for_timeout(1000)


def capture() -> None:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    process = wait_for_app()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1365, "height": 900})
            page.goto(BASE_URL)
            page.wait_for_selector("text=Campus Agent Lab", timeout=20000)

            click_button(page, "加载示例 README")
            click_button(page, "生成速读报告")
            readme_result = page.get_by_text("速读结果", exact=True)
            readme_result.wait_for(timeout=10000)
            readme_result.scroll_into_view_if_needed()
            page.screenshot(path=SCREENSHOT_DIR / "01-readme-reader.png", full_page=False)

            select_tool(page, "Java/C 实验代码检查器")
            click_button(page, "加载 Java 示例")
            click_button(page, "检查代码")
            code_result = page.get_by_text("检查结果", exact=True)
            code_result.wait_for(timeout=10000)
            code_result.scroll_into_view_if_needed()
            page.screenshot(path=SCREENSHOT_DIR / "02-code-checker.png", full_page=False)

            select_tool(page, "期末资料整理 Agent")
            click_button(page, "加载期末资料示例")
            click_button(page, "生成复习计划")
            exam_result = page.get_by_text("复习计划", exact=True)
            exam_result.wait_for(timeout=10000)
            exam_result.scroll_into_view_if_needed()
            page.screenshot(path=SCREENSHOT_DIR / "03-exam-agent.png", full_page=False)

            browser.close()
    finally:
        process.terminate()
        process.wait(timeout=10)


if __name__ == "__main__":
    capture()
