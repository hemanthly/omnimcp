from omnimcp_analytics.client import _tool_result_payload
from omnimcp_analytics.upstreams import exposed_name, server_parameters


def test_exposed_name_namespaces_and_sanitizes_tools():
    used = set()

    assert exposed_name("fetch", "get-page", used) == "fetch_get_page"
    assert exposed_name("fetch", "get page", used) == "fetch_get_page_2"


def test_tool_result_payload_preserves_error_and_content():
    class Text:
        text = "sample"

        def model_dump(self, **kwargs):
            return {"type": "text", "text": self.text}

    class Result:
        isError = True
        content = [Text()]

    assert _tool_result_payload(Result()) == {
        "is_error": True,
        "content": [{"type": "text", "text": "sample"}],
    }


def test_mcp_children_do_not_inherit_gemini_credentials(monkeypatch, tmp_path):
    monkeypatch.setenv("GEMINI_API_KEY", "do-not-forward")
    monkeypatch.setenv("OMNIMCP_SQLITE_DB", str(tmp_path / "test.db"))

    parameters = server_parameters()

    assert "GEMINI_API_KEY" not in parameters[0][1].env
    assert "GEMINI_API_KEY" not in parameters[1][1].env
    assert "GEMINI_API_KEY" not in parameters[2][1].env


def test_community_servers_use_available_uv_packages(monkeypatch, tmp_path):
    monkeypatch.setenv("OMNIMCP_SQLITE_DB", str(tmp_path / "test.db"))

    parameters = server_parameters()

    assert parameters[1][1].command == "uvx"
    assert parameters[1][1].args == [
        "--from",
        "mcp-server-fetch",
        "mcp-server-fetch",
    ]
    assert parameters[2][1].command == "uvx"
    assert parameters[2][1].args[:4] == [
        "--with",
        "mcp<2",
        "--from",
        "mcp-server-sqlite",
    ]
    assert parameters[2][1].args[4] == "mcp-server-sqlite"
