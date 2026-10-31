"""API-key-protected Streamable HTTP gateway federating three MCP servers."""

from __future__ import annotations

import base64
import hmac
import logging
import os
import time
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import quote

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from mcp.server.lowlevel.helper_types import ReadResourceContents
from mcp.server.lowlevel.server import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from pydantic import AnyUrl

from omnimcp_analytics.upstreams import exposed_name, server_parameters

logger = logging.getLogger("omnimcp_analytics.gateway")


@dataclass(frozen=True)
class UpstreamRoute:
    session: ClientSession
    name: str
    server: str


@dataclass
class Federation:
    tools: list[types.Tool] = field(default_factory=list)
    tool_routes: dict[str, UpstreamRoute] = field(default_factory=dict)
    resources: list[types.Resource] = field(default_factory=list)
    resource_routes: dict[str, UpstreamRoute] = field(default_factory=dict)
    prompts: list[types.Prompt] = field(default_factory=list)
    prompt_routes: dict[str, UpstreamRoute] = field(default_factory=dict)


def _require_federation(state: dict[str, Federation | None]) -> Federation:
    federation = state["federation"]
    if federation is None:
        raise RuntimeError("The MCP gateway has not completed startup.")
    return federation


async def _discover_upstreams(
    sessions: list[tuple[str, ClientSession]],
) -> Federation:
    federation = Federation()
    tool_names: set[str] = set()
    prompt_names: set[str] = set()
    discovered_resources: list[tuple[str, types.Resource, ClientSession]] = []

    for server_name, session in sessions:
        tools_result = await session.list_tools()
        for tool in tools_result.tools:
            name = exposed_name(server_name, tool.name, tool_names)
            federation.tools.append(
                tool.model_copy(
                    update={
                        "name": name,
                        "description": f"[{server_name}] {tool.description or tool.name}",
                    }
                )
            )
            federation.tool_routes[name] = UpstreamRoute(
                session=session,
                name=tool.name,
                server=server_name,
            )

        resources_result = await session.list_resources()
        discovered_resources.extend(
            (server_name, resource, session) for resource in resources_result.resources
        )

        prompts_result = await session.list_prompts()
        for prompt in prompts_result.prompts:
            name = exposed_name(server_name, prompt.name, prompt_names)
            federation.prompts.append(
                prompt.model_copy(
                    update={
                        "name": name,
                        "description": f"[{server_name}] {prompt.description or prompt.name}",
                    }
                )
            )
            federation.prompt_routes[name] = UpstreamRoute(
                session=session,
                name=prompt.name,
                server=server_name,
            )

    uri_counts: dict[str, int] = {}
    for _, resource, _ in discovered_resources:
        key = str(resource.uri)
        uri_counts[key] = uri_counts.get(key, 0) + 1

    for server_name, resource, session in discovered_resources:
        original_uri = str(resource.uri)
        exposed_uri = original_uri
        if uri_counts[original_uri] > 1:
            exposed_uri = f"omnimcp://{server_name}/{quote(original_uri, safe='')}"
        federation.resources.append(
            resource.model_copy(
                update={
                    "uri": AnyUrl(exposed_uri),
                    "name": f"{server_name}_{resource.name}",
                    "description": f"[{server_name}] {resource.description or resource.name}",
                }
            )
        )
        federation.resource_routes[exposed_uri] = UpstreamRoute(
            session=session,
            name=original_uri,
            server=server_name,
        )

    return federation


def create_app(
    upstreams: list[tuple[str, StdioServerParameters]] | None = None,
) -> FastAPI:
    """Create an independently-lifecycled federated MCP gateway application."""
    state: dict[str, Federation | None] = {"federation": None}
    mcp_server = Server("omnimcp-federated-gateway")
    session_manager = StreamableHTTPSessionManager(
        app=mcp_server,
        json_response=True,
    )

    @mcp_server.list_tools()
    async def list_tools(_: types.ListToolsRequest) -> types.ListToolsResult:
        return types.ListToolsResult(tools=_require_federation(state).tools)

    @mcp_server.call_tool()
    async def call_tool(
        name: str, arguments: dict[str, Any] | None
    ) -> types.CallToolResult:
        route = _require_federation(state).tool_routes.get(name)
        if route is None:
            raise ValueError(f"Unknown federated tool: {name}")
        started = time.perf_counter()
        try:
            return await route.session.call_tool(
                route.name,
                arguments=arguments or {},
            )
        finally:
            elapsed_ms = (time.perf_counter() - started) * 1000
            logger.info(
                "server=%s tool=%s duration_ms=%.3f",
                route.server,
                route.name,
                elapsed_ms,
            )

    @mcp_server.list_resources()
    async def list_resources(_: types.ListResourcesRequest) -> types.ListResourcesResult:
        return types.ListResourcesResult(resources=_require_federation(state).resources)

    @mcp_server.read_resource()
    async def read_resource(uri: AnyUrl) -> list[ReadResourceContents]:
        route = _require_federation(state).resource_routes.get(str(uri))
        if route is None:
            raise ValueError(f"Unknown federated resource: {uri}")
        result = await route.session.read_resource(AnyUrl(route.name))
        contents: list[ReadResourceContents] = []
        for content in result.contents:
            if isinstance(content, types.TextResourceContents):
                value: str | bytes = content.text
            elif isinstance(content, types.BlobResourceContents):
                value = base64.b64decode(content.blob)
            else:
                raise TypeError(
                    f"Unsupported resource content type: {type(content).__name__}"
                )
            contents.append(
                ReadResourceContents(
                    content=value,
                    mime_type=content.mimeType,
                    meta=content.meta,
                )
            )
        return contents

    @mcp_server.list_prompts()
    async def list_prompts(_: types.ListPromptsRequest) -> types.ListPromptsResult:
        return types.ListPromptsResult(prompts=_require_federation(state).prompts)

    @mcp_server.get_prompt()
    async def get_prompt(
        name: str, arguments: dict[str, str] | None
    ) -> types.GetPromptResult:
        route = _require_federation(state).prompt_routes.get(name)
        if route is None:
            raise ValueError(f"Unknown federated prompt: {name}")
        return await route.session.get_prompt(route.name, arguments=arguments)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        async with AsyncExitStack() as stack:
            sessions: list[tuple[str, ClientSession]] = []
            configured_upstreams = (
                server_parameters() if upstreams is None else upstreams
            )
            for server_name, parameters in configured_upstreams:
                try:
                    streams = await stack.enter_async_context(stdio_client(parameters))
                    session = await stack.enter_async_context(ClientSession(*streams))
                    await session.initialize()
                except Exception as exc:
                    raise RuntimeError(
                        f"Unable to initialize upstream MCP server '{server_name}'."
                    ) from exc
                sessions.append((server_name, session))

            try:
                state["federation"] = await _discover_upstreams(sessions)
            except Exception as exc:
                raise RuntimeError("Unable to discover upstream MCP capabilities.") from exc

            try:
                async with session_manager.run():
                    yield
            finally:
                state["federation"] = None

    app = FastAPI(title="OmniMCP Gateway", version="0.1.0", lifespan=lifespan)

    @app.middleware("http")
    async def require_api_key(request: Request, call_next):
        path = request.url.path
        if path == "/mcp" or path.startswith("/mcp/"):
            expected_key = os.getenv("OMNIMCP_API_KEY", "")
            supplied_key = request.headers.get("X-API-Key", "")
            if not expected_key:
                return JSONResponse(
                    status_code=503,
                    content={"detail": "Gateway API key is not configured."},
                )
            if not hmac.compare_digest(supplied_key, expected_key):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "A valid X-API-Key header is required."},
                )
        return await call_next(request)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.mount("/mcp", session_manager.asgi_app)
    return app


app = create_app()
