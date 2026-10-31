"""Gemini client for the federated Streamable HTTP MCP gateway."""

from __future__ import annotations

import asyncio
import os
import sys
from typing import Any

import httpx
from google import genai
from google.genai import types
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

DEFAULT_MODEL = "gemini-2.5-flash"


def _tool_result_payload(result: Any) -> dict[str, Any]:
    return {
        "is_error": bool(result.isError),
        "content": [
            item.model_dump(mode="json", exclude_none=True)
            if hasattr(item, "model_dump")
            else str(item)
            for item in result.content
        ],
    }


async def _run(prompt: str) -> None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Set GEMINI_API_KEY before starting the Gemini client.")

    gateway_key = os.getenv("OMNIMCP_API_KEY")
    if not gateway_key:
        raise RuntimeError("Set OMNIMCP_API_KEY before connecting to the MCP gateway.")

    client = genai.Client(api_key=api_key)
    model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)

    gateway_url = os.getenv(
        "OMNIMCP_GATEWAY_URL",
        "http://127.0.0.1:8000/mcp",
    )
    async with httpx.AsyncClient(
        headers={"X-API-Key": gateway_key},
        timeout=httpx.Timeout(300.0, connect=10.0),
    ) as http_client:
        async with streamable_http_client(
            gateway_url,
            http_client=http_client,
        ) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                server_tools = await session.list_tools()
                routing = {tool.name for tool in server_tools.tools}
                declarations = [
                    types.FunctionDeclaration(
                        name=tool.name,
                        description=tool.description or tool.name,
                        parameters_json_schema=tool.inputSchema
                        or {"type": "object", "properties": {}},
                    )
                    for tool in server_tools.tools
                ]

                history: list[types.Content | str] = [prompt]
                config = types.GenerateContentConfig(
                    tools=[types.Tool(function_declarations=declarations)]
                )

                for _ in range(8):
                    response = client.models.generate_content(
                        model=model,
                        contents=history,
                        config=config,
                    )
                    function_calls = response.function_calls or []
                    if not function_calls:
                        print(response.text or "")
                        return

                    if not response.candidates:
                        raise RuntimeError(
                            "Gemini requested tools without returning a candidate."
                        )
                    history.append(response.candidates[0].content)
                    response_parts = []
                    for function_call in function_calls:
                        if function_call.name not in routing:
                            raise RuntimeError(
                                f"Gemini requested an unknown tool: {function_call.name}"
                            )
                        result = await session.call_tool(
                            function_call.name,
                            arguments=dict(function_call.args or {}),
                        )
                        response_parts.append(
                            types.Part.from_function_response(
                                name=function_call.name,
                                response=_tool_result_payload(result),
                            )
                        )
                    history.append(types.Content(role="user", parts=response_parts))

                raise RuntimeError(
                    "Gemini exceeded the maximum number of tool-call rounds."
                )


def main() -> None:
    """Prompt for a request and run the federated Gemini/MCP tool loop."""
    prompt = " ".join(sys.argv[1:]).strip()
    if not prompt:
        prompt = input("What would you like to ask the MCP servers? ").strip()
    if not prompt:
        raise SystemExit("A non-empty prompt is required.")
    asyncio.run(_run(prompt))


if __name__ == "__main__":
    main()
