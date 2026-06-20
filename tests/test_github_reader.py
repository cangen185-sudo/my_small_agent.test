import pytest

from src.github_reader import analyze_readme, parse_github_url


def test_parse_github_url_normal_repo() -> None:
    assert parse_github_url("https://github.com/openai/openai-python") == ("openai", "openai-python")


def test_parse_github_url_rejects_non_github() -> None:
    with pytest.raises(ValueError):
        parse_github_url("https://example.com/owner/repo")


def test_analyze_readme_detects_python_streamlit() -> None:
    text = """
    # Demo App
    A small Python Streamlit demo.

    ## Install
    pip install -r requirements.txt
    streamlit run app.py
    """
    result = analyze_readme(text)
    assert "Python" in result["tech_stack"]
    assert any("streamlit run app.py" in item for item in result["install_run"])

