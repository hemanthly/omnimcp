# 6. Sending the prompt to Gemini

## What this note covers

After the MCP client has discovered tools and prepared Gemini function
declarations, it sends the user's prompt and those declarations to Gemini.
This checkpoint is about the request and response shape; it does not yet
follow the returned tool call back to the MCP server.

## Constructing the Gemini request

In `src/omnimcp_analytics/client.py`, the client puts the function declarations
inside a Gemini request configuration:

```python
config = types.GenerateContentConfig(
    tools=[types.Tool(function_declarations=declarations)]
)
```

The conversation history begins with the user's prompt. The client then sends
the current history and configuration to Gemini:

```python
response = client.models.generate_content(
    model=model,
    contents=history,
    config=config,
)
```

This is a request to the Gemini API. It is not an MCP request and does not by
itself call one of the local MCP tools.

## Two possible response paths

The client checks `response.function_calls`:

- If Gemini returns no function calls, the client prints its text answer and
  finishes this run.
- If Gemini returns a function call, the client must handle that request.
  Gemini's response is a request from the model, not proof that the MCP tool
  has run. The client still needs to route it to an MCP session and call the
  MCP tool.

The tool declarations are therefore like a menu: they tell Gemini which tools
are available and what arguments they accept. Gemini can choose to ask for a
tool, but the client code is responsible for carrying out that request.

The client repeats this process in a loop so it can send tool results back to
Gemini and receive a final answer. The current implementation limits the loop
to eight rounds.

## Cross-check questions

1. What information does `generate_content(...)` send to Gemini?
2. Is `generate_content(...)` an MCP `tools/call` request?
3. If `response.function_calls` is empty, what does the client do?
4. If Gemini returns a function call, has the MCP tool run already?
5. Why does the client loop and call Gemini again after tool execution?

## Next checkpoint

Continue with [note 7](7-how-the-client-routes-a-tool-call.md) to follow a
Gemini function call through the client's routing table to the appropriate MCP
session.
