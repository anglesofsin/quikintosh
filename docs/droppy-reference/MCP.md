# Local MCP bridge

`quickintosh-mcp` implements JSON-RPC MCP over stdio, protocol 2025-03-26.
It does not listen on a network port, discover credentials, read file contents,
execute commands, or modify an existing AI client's configuration.

Default: only `quickintosh_status` is exposed. Explicit startup flags add:

- `--allow-ui`: open shelf pages 0–14.
- `--allow-files`: add existing, absolute local paths to the tray, preserving originals.
- `--allow-activities`: publish bounded agent/build progress in Live Activities.

Example client configuration:

```json
{
  "mcpServers": {
    "quickintosh": {
      "command": "/home/pg/.local/bin/quickintosh-mcp",
      "args": ["--allow-activities"]
    }
  }
}
```

Only add flags for actions you want that client to perform. Calls are limited to
60 per minute, IPC calls to 10 seconds, requests to 64 KiB. Tool input validation
is enforced independently of the advertised JSON Schema. A stdio smoke test is
not a claim that a particular third-party client has been configured or tested.

Reference: https://modelcontextprotocol.io/specification/2025-03-26/server/tools
