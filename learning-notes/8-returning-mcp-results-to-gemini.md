# 8. Returning MCP results to Gemini

## What this note covers

After an MCP server runs a tool, the client must give the result back to
Gemini. This lets Gemini interpret the result and answer the user's original
prompt.

## Convert the MCP result

In `src/omnimcp_analytics/client.py`, `_tool_result_payload()` at line 80
extracts two things from the MCP result:

- `is_error`: whether MCP marked the tool result as an error.
- `content`: the returned content blocks, converted to JSON-compatible data
  when possible.

The client uses this payload to build a Gemini function-response part. At
lines 153–156, it preserves the function's exposed Gemini name and attaches
the MCP result payload.

## Add the result to the conversation and continue

At line 158, the client appends the function responses to the conversation
history as a user-role content turn. The loop then calls Gemini again at line
128, now with both the original prompt and the tool result in the history.

Gemini can use the result to produce a final answer. It can also request
another tool; the loop handles that and allows up to eight rounds. If it
returns no more function calls, the client prints the final text and returns.

The flow is:

```text
Gemini function call
    -> MCP session.call_tool(...)
    -> MCP CallToolResult
    -> Gemini function-response part
    -> next Gemini response
```

The Gemini function name is used in the response part so it matches the
function request Gemini made, even though the MCP session received the
original, unprefixed tool name.

## Cross-check questions

1. What information does `_tool_result_payload()` preserve from an MCP result?
2. Why does the client call Gemini again after receiving an MCP result?
3. What is the maximum number of tool-call rounds in this client?

## Checkpoint complete

This completes the basic single-client tool loop: discover MCP tools, declare
them to Gemini, route a requested call to MCP, and return the result to Gemini.

The project client is already configured for three MCP servers. Continue with
[note 9](9-federating-three-mcp-servers.md) to understand how those independent
sessions are managed before trying an end-to-end run.
