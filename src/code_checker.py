"""Static and compile-only checks for C and Java lab code."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Literal


Issue = dict[str, object]
Language = Literal["c", "java", "unknown"]


def detect_language(filename: str, code: str) -> Language:
    """Detect source language from filename first, then code features."""
    suffix = Path(filename).suffix.lower()
    if suffix in {".c", ".h"}:
        return "c"
    if suffix == ".java":
        return "java"
    if "#include" in code or re.search(r"\bint\s+main\s*\(", code):
        return "c"
    if "public class" in code or "System.out" in code:
        return "java"
    return "unknown"


def static_check_c(code: str) -> list[Issue]:
    """Run simple static checks for C code without executing it."""
    issues: list[Issue] = []
    lines = code.splitlines()

    if not re.search(r"\b(main)\s*\(", code):
        issues.append(_issue("error", None, "没有找到 main 函数", "补充 int main(void) 或 int main(int argc, char **argv)。", "C 程序通常从 main 函数开始执行，实验代码缺少入口会无法链接生成程序。"))

    main_line = _find_line(lines, r"\bint\s+main\s*\(")
    if main_line and not re.search(r"return\s+0\s*;", code):
        issues.append(_issue("warning", main_line, "main 函数可能缺少 return 0", "在 main 结束前添加 return 0;。", "虽然部分编译器会默认处理，但显式返回能表达程序正常结束。"))

    for i, line in enumerate(lines, start=1):
        if re.search(r"\bgets\s*\(", line):
            issues.append(_issue("error", i, "使用了危险函数 gets", "改用 fgets(buffer, size, stdin)。", "gets 不知道缓冲区大小，容易造成缓冲区溢出，现代 C 标准已移除它。"))
        if re.search(r"\bmalloc\s*\(", line) and not _nearby_contains(lines, i, r"if\s*\(.+==\s*NULL|if\s*\(.+!\s*="):
            issues.append(_issue("warning", i, "malloc 后可能没有判断是否分配成功", "保存 malloc 返回值后判断指针是否为 NULL。", "内存分配可能失败，不判断会导致后续解引用空指针。"))
        if re.search(r"\[[A-Za-z_]\w*\s*\+\s*1\]", line) or re.search(r"<=\s*sizeof\s*\(", line):
            issues.append(_issue("warning", i, "存在数组越界风险的简单模式", "检查循环边界，数组下标通常应小于长度而不是小于等于长度。", "C 不会自动检查数组边界，越界会导致未定义行为。"))

    return issues


def static_check_java(filename: str, code: str) -> list[Issue]:
    """Run simple static checks for Java code without executing it."""
    issues: list[Issue] = []
    lines = code.splitlines()
    class_match = re.search(r"public\s+class\s+([A-Za-z_]\w*)", code)

    if not class_match:
        issues.append(_issue("error", None, "没有找到 public class", "补充 public class 类名，并确保文件名与类名一致。", "Java 入门实验通常要求 public class 与文件名一致，否则 javac 会报错。"))
    else:
        class_name = class_match.group(1)
        file_stem = Path(filename).stem
        if file_stem and file_stem != class_name:
            line_no = _find_line(lines, rf"public\s+class\s+{re.escape(class_name)}")
            issues.append(_issue("error", line_no, "public class 名可能和文件名不一致", f"将文件名改为 {class_name}.java，或将类名改为 {file_stem}。", "Java 规定 public 类名必须和源文件名保持一致。"))

    if "public static void main" not in code:
        issues.append(_issue("warning", None, "没有找到标准 main 方法", "补充 public static void main(String[] args)。", "没有 main 方法时，普通 Java 程序不能直接作为入口运行。"))

    for i, line in enumerate(lines, start=1):
        if "System.out.printlin" in line:
            issues.append(_issue("error", i, "System.out.println 拼写错误", "把 printlin 改为 println。", "println 是 Java 标准输出方法，拼错会导致编译失败。"))
        if any(char in line for char in ("；", "（", "）", "｛", "｝")):
            issues.append(_issue("error", i, "代码中出现中文标点", "把中文分号、括号或大括号改成英文半角符号。", "Java 语法只接受英文半角标点，中文标点会造成编译错误。"))

    return issues


def compile_check(filename: str, code: str) -> list[Issue]:
    """Compile C or Java code in a temp directory, never run the output."""
    language = detect_language(filename, code)
    if language == "unknown":
        return [_issue("info", None, "无法判断语言，已跳过编译检查", "请使用 .c 或 .java 文件名。", "编译检查需要先确定调用 gcc 还是 javac。")]

    compiler = "gcc" if language == "c" else "javac"
    if shutil.which(compiler) is None:
        return [_issue("info", None, f"未检测到 {compiler}，已跳过编译检查", f"如需编译检查，请先安装 {compiler} 并加入 PATH。", "静态检查仍然有效；编译检查依赖本机编译器。")]

    suffix = ".c" if language == "c" else ".java"
    safe_name = _safe_filename(filename, suffix)

    with tempfile.TemporaryDirectory(prefix="campus_agent_compile_") as tmp:
        source_path = Path(tmp) / safe_name
        source_path.write_text(code, encoding="utf-8")
        if language == "c":
            command = [compiler, "-fsyntax-only", str(source_path)]
        else:
            command = [compiler, str(source_path)]

        try:
            result = subprocess.run(command, cwd=tmp, capture_output=True, text=True, timeout=10, check=False)
        except subprocess.TimeoutExpired:
            return [_issue("error", None, "编译检查超时", "先检查代码中是否有异常复杂的宏或语法结构。", "为了保证工具响应速度，编译检查设置了时间限制。")]

    if result.returncode == 0:
        return [_issue("info", None, "编译检查通过", "当前没有发现编译错误。", "这里只做编译或语法检查，不会运行你的程序。")]

    output = (result.stderr or result.stdout).strip()
    return [_issue("error", None, "编译失败", _shorten(output), "编译器给出的错误通常比静态规则更准确，请优先根据第一条错误修改。")]


def check_code(filename: str, code: str) -> dict[str, object]:
    """Detect language, run static checks, and run compile-only check."""
    language = detect_language(filename, code)
    if language == "c":
        static_issues = static_check_c(code)
    elif language == "java":
        static_issues = static_check_java(filename, code)
    else:
        static_issues = [_issue("warning", None, "暂不支持该文件类型", "请上传或粘贴 .c / .java 代码。", "当前 MVP 只面向 C 和 Java 实验代码。")]

    compile_issues = compile_check(filename, code) if language in {"c", "java"} else []
    return {
        "filename": filename,
        "language": language,
        "issues": static_issues + compile_issues,
    }


def _issue(severity: str, line: int | None, message: str, suggestion: str, explanation: str) -> Issue:
    return {
        "severity": severity,
        "line": line,
        "message": message,
        "suggestion": suggestion,
        "explanation": explanation,
    }


def _find_line(lines: list[str], pattern: str) -> int | None:
    for i, line in enumerate(lines, start=1):
        if re.search(pattern, line):
            return i
    return None


def _nearby_contains(lines: list[str], line_no: int, pattern: str) -> bool:
    start = max(0, line_no - 1)
    end = min(len(lines), line_no + 3)
    return any(re.search(pattern, line) for line in lines[start:end])


def _safe_filename(filename: str, suffix: str) -> str:
    name = Path(filename).name or f"Main{suffix}"
    if not name.endswith(suffix):
        name = f"{Path(name).stem or 'Main'}{suffix}"
    return name


def _shorten(text: str, limit: int = 1200) -> str:
    cleaned = text.strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[:limit] + "\n...（输出过长，已截断）"

