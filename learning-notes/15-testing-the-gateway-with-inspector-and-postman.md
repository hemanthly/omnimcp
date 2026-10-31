# 15. Testing the federated gateway with Inspector and Postman

## What this note covers

The gateway exposes the analytics, Fetch, and SQLite servers through a single
Streamable HTTP endpoint. MCP Inspector and Postman's MCP request mode can
connect to it, list the combined tools, and call them.

Start the gateway in one terminal:

```powershell
uv run --env-file .env uvicorn omnimcp_analytics.gateway:app --host 127.0.0.1 --port 8000
```

The `.env` file must contain `OMNIMCP_API_KEY=...`. Do not paste the key into
chat, source code, or a shared collection. The key must be supplied in the
`X-API-Key` header for MCP requests.

## MCP Inspector

1. In a separate terminal, launch the Inspector UI:

   ```powershell
   npx -y @modelcontextprotocol/inspector
   ```

2. Select **Streamable HTTP** as the transport and enter:

   ```text
   http://127.0.0.1:8000/mcp
   ```

3. Add the custom request header `X-API-Key` with the local value from `.env`,
   then connect.
4. Open **Tools** and list the available tools. Tool names include their
   upstream prefix, for example `local_get_system_metrics` or
   `sqlite_list_tables`.
5. Call `local_get_system_metrics`. Open **Resources** to inspect
   `logs://latest` if the configured log file exists.

Inspector performs the MCP initialization lifecycle. The URL is the single
Streamable HTTP endpoint `/mcp`, not the old `/mcp/sse` route.

## Postman

In Postman's MCP request mode, select HTTP/Streamable HTTP, enter
`http://127.0.0.1:8000/mcp`, and configure the `X-API-Key` header. Postman
will perform the MCP lifecycle and show the tools and results.

Use the Postman desktop app or Desktop Agent for localhost. A cloud agent runs
remotely and cannot reach the `127.0.0.1` address on your computer.

## What can go wrong

- **503**: the gateway process did not receive `OMNIMCP_API_KEY`.
- **401**: a request omitted or supplied the wrong `X-API-Key`.
- **Startup fails naming an upstream**: check that `uv` is installed and can
  run `uvx`; then inspect the reported server startup error.
- **Connection failure**: check that Uvicorn is running and that the URL is
  `/mcp`.
- **Missing tools**: verify that all upstreams started. The gateway lists
  tools during startup, so a failed upstream prevents successful startup.

Do not share screenshots or exported Postman collections that reveal the API
key.

## Next checkpoint

Continue with [note 16](16-http-sse-and-streamable-http.md) for the transport
concepts, then [note 17](17-federated-streamable-http-gateway.md) for how the
gateway aggregates and routes upstream tools.
