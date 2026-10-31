# 14. Docker and Render deployment

## What this note covers

The project has a Docker image definition and a Render service configuration.
This checkpoint explains their roles; it does not deploy or publish anything
until you explicitly choose to do that.

## Dockerfile

The `Dockerfile` is the build recipe for a container image. The image is the
packaged artifact; a container is a running instance created from that image.
The `Dockerfile` describes how to build the image:

1. Select a Python base image.
2. Copy the package metadata and source into `/app`.
3. Install the project, its Python dependencies, and `uv` for the upstream
   `uvx` server launchers.
4. Declare the application's port.
5. Start Uvicorn with the FastAPI gateway application.

The container command binds Uvicorn to `0.0.0.0` *inside the container* so
Docker's port mapping and the hosting platform can reach it. This differs from
the local learning command, which binds to `127.0.0.1` on the host machine.

## Render configuration

`render.yaml` describes a Render web service using the Dockerfile. It sets
`/health` as the health-check path and declares `OMNIMCP_API_KEY` as a
non-synchronized environment variable. The actual secret must be set in
Render's dashboard; it is not stored in this file.

In short: `Dockerfile` says how to build and start the application image;
`render.yaml` tells Render what kind of service to create and how to configure
it. Render can build the image from the repository and then run a container
from it.

The gateway starts Fetch and SQLite with `uvx` when it starts, so those
packages must be downloadable and the container must have enough memory and
filesystem capacity. The SQLite database and package caches live inside the
container unless persistent storage is configured.

## Before a real deployment

- Keep the API key in the host's secret settings, never in the Dockerfile,
  source code, or committed YAML.
- Use HTTPS for public access.
- Confirm that the host supports the requirements of Streamable HTTP.
- Remember that this gateway exposes federated MCP tools; it does not run the
  Gemini-powered client.

## Cross-check questions

1. What does the Dockerfile define?
2. Why does the container listen on `0.0.0.0`?
3. Where should the real `OMNIMCP_API_KEY` be configured for Render?
4. Does deploying the gateway also deploy or run the Gemini client?

## Checkpoint complete

The Dockerfile packages and starts the gateway, while Render configuration
describes the hosted web service and its health check. Neither publishes the
Python package to PyPI.

Before studying distribution, continue with
[note 15](15-testing-the-gateway-with-inspector-and-postman.md) to interact
with the running gateway over Streamable HTTP.
