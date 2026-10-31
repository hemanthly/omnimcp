"""Configuration for the MCP servers owned by the federated gateway."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from mcp import StdioServerParameters


def _environment(*names: str) -> dict[str, str]:
    return {name: os.environ[name] for name in names if name in os.environ}


def _uvx_parameters(
    package: str,
    executable: str,
    args: list[str],
    *,
    with_packages: tuple[str, ...] = (),
) -> StdioServerParameters:
    uvx_args = [argument for requirement in with_packages for argument in ("--with", requirement)]
    return StdioServerParameters(
        command="uvx",
        args=[*uvx_args, "--from", package, executable, *args],
        env={},
    )


def server_parameters() -> list[tuple[str, StdioServerParameters]]:
    db_path = Path(os.getenv("OMNIMCP_SQLITE_DB", "data/omnimcp.db")).expanduser()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return [
        (
            "local",
            StdioServerParameters(
                command=sys.executable,
                args=["-m", "omnimcp_analytics.server"],
                env=_environment("OMNIMCP_LOG_FILE", "LOG_LEVEL"),
            ),
        ),
        (
            "fetch",
            _uvx_parameters("mcp-server-fetch", "mcp-server-fetch", []),
        ),
        (
            "sqlite",
            _uvx_parameters(
                "mcp-server-sqlite",
                "mcp-server-sqlite",
                ["--db-path", str(db_path.resolve())],
                with_packages=("mcp<2",),
            ),
        ),
    ]


def exposed_name(server: str, original: str, used_names: set[str]) -> str:
    base = re.sub(r"[^a-zA-Z0-9_]", "_", f"{server}_{original}")
    if not base or not base[0].isalpha():
        base = f"tool_{base}"
    name = base[:60]
    suffix = 2
    while name in used_names:
        ending = f"_{suffix}"
        name = f"{base[: 60 - len(ending)]}{ending}"
        suffix += 1
    used_names.add(name)
    return name
