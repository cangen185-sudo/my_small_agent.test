from src.code_checker import check_code, detect_language, static_check_c, static_check_java


def test_detect_language_by_filename() -> None:
    assert detect_language("hello.c", "int main() {}") == "c"
    assert detect_language("Main.java", "public class Main {}") == "java"


def test_static_check_c_finds_gets_and_malloc_warning() -> None:
    code = """
    #include <stdlib.h>
    int main() {
        char name[8];
        int *p = malloc(sizeof(int));
        gets(name);
    }
    """
    messages = [issue["message"] for issue in static_check_c(code)]
    assert "使用了危险函数 gets" in messages
    assert "malloc 后可能没有判断是否分配成功" in messages


def test_static_check_java_finds_printlin_and_chinese_punctuation() -> None:
    code = """
    public class Demo {
        public static void main(String[] args) {
            System.out.printlin("hi")；
        }
    }
    """
    messages = [issue["message"] for issue in static_check_java("Demo.java", code)]
    assert "System.out.println 拼写错误" in messages
    assert "代码中出现中文标点" in messages


def test_check_code_returns_language_and_issues() -> None:
    result = check_code("Demo.java", "public class Demo {}")
    assert result["language"] == "java"
    assert result["issues"]

