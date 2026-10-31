import sys

from fastapi.testclient import TestClient
from mcp import StdioServerParameters

from omnimcp_analytics.gateway import app, create_app


def test_gateway_health_is_public():
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_streamable_http_endpoint_fails_closed_without_configured_key(monkeypatch):
    monkeypatch.delenv("OMNIMCP_API_KEY", raising=False)
    client = TestClient(app)

    assert client.get("/mcp").status_code == 503
    assert client.post("/mcp").status_code == 503


def test_streamable_http_endpoint_rejects_invalid_key(monkeypatch):
    monkeypatch.setenv("OMNIMCP_API_KEY", "expected-secret")
    client = TestClient(app)
    headers = {"X-API-Key": "wrong-secret"}

    assert client.get("/mcp", headers=headers).status_code == 401
    assert client.post("/mcp", headers=headers).status_code == 401


def test_gateway_lists_and_routes_upstream_tools(monkeypatch, tmp_path):
    monkeypatch.setenv("OMNIMCP_API_KEY", "expected-secret")
    log_path = tmp_path / "gateway.log"
    log_path.write_text("test log content", encoding="utf-8")
    gateway = create_app(
        [
            (
                "local",
                StdioServerParameters(
                    command=sys.executable,
                    args=["-m", "omnimcp_analytics.server"],
                    env={"OMNIMCP_LOG_FILE": str(log_path)},
                ),
            )
        ]
    )
    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
        "X-API-Key": "expected-secret",
    }

    with TestClient(gateway) as client:
        initialized = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {},
                    "clientInfo": {"name": "gateway-test", "version": "1.0"},
                },
            },
        )
        assert initialized.status_code == 200
        protocol_version = initialized.json()["result"]["protocolVersion"]
        session_id = initialized.headers["mcp-session-id"]
        session_headers = {
            **headers,
            "MCP-Protocol-Version": protocol_version,
            "Mcp-Session-Id": session_id,
        }

        assert client.post(
            "/mcp",
            headers=session_headers,
            json={"jsonrpc": "2.0", "method": "notifications/initialized"},
        ).status_code == 202

        tools_response = client.post(
            "/mcp",
            headers=session_headers,
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {},
            },
        )
        assert tools_response.status_code == 200
        tools = tools_response.json()["result"]["tools"]
        assert "local_get_system_metrics" in {tool["name"] for tool in tools}

        resources_response = client.post(
            "/mcp",
            headers=session_headers,
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "resources/list",
                "params": {},
            },
        )
        assert resources_response.status_code == 200
        resources = resources_response.json()["result"]["resources"]
        log_resource = next(
            resource for resource in resources if resource["uri"] == "logs://latest"
        )
        resource_response = client.post(
            "/mcp",
            headers=session_headers,
            json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "resources/read",
                "params": {"uri": log_resource["uri"]},
            },
        )
        assert resource_response.status_code == 200
        assert (
            resource_response.json()["result"]["contents"][0]["text"]
            == "test log content"
        )

        call_response = client.post(
            "/mcp",
            headers=session_headers,
            json={
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {"name": "local_get_system_metrics", "arguments": {}},
            },
        )
        assert call_response.status_code == 200
        result = call_response.json()["result"]
        assert result["isError"] is not True
        assert result["content"]
