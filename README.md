# interactive-agent-blender

A live, no-screenshot connection between an LLM agent and Blender: the agent reads and mutates
actual scene state over a local socket instead of interpreting rendered images.

## Current state

- `addon.py` — the [blender-mcp](https://github.com/ahujasid/blender-mcp) Blender addon (installed
  and enabled in the local Blender 5.2 user preferences, auto-starts its TCP server on
  `localhost:9876` whenever Blender opens).
- `.mcp.json` — registers the `blender` MCP server (`uvx blender-mcp`) so an MCP-aware agent can
  connect to that running Blender session directly (`get_scene_info`, `execute_blender_code`,
  `get_object_info`, asset-generation tools, etc).

## Target benchmark

Seven proofs the agent needs to demonstrate against a live Blender session:

1. One Blender process survives 100 verified interactive actions
2. Agent creates a simple mesh interactively
3. Agent models against a reference
4. Agent detects and repairs its own mistake
5. Agent retrieves a previously learned topology skill
6. Agent completes an unseen hard-surface prop
7. Independent verification says the result is clean
