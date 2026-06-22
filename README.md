# WineBot Contracts

Shared API specification, CLI contract, and conformance tests ensuring feature parity between:

| Project | Runtime Engine | Repository |
|:---|:---|:---|
| **WineBot** | Containerized Wine (Linux/Docker) | [SemperSupra/WineBot](https://github.com/SemperSupra/WineBot) |
| **WinBot** | Cloned Windows VM | [SemperSupra/WinBot](https://github.com/SemperSupra/WinBot) |

Both projects must implement the contracts defined here. The contracts cover API endpoints, CLI commands, idempotency, MCP tools, CV/OCR sidecar, and credential management.

## Structure

```
api/openapi.yaml         REST API specification
cli/winebotctl.md        CLI command contract
cli/idempotency.md       Idempotency contract
mcp/tools.json           MCP tool definitions for AI agents
tests/conformance/       Cross-project conformance tests
schemas/session.json     Session manifest schema
docs/architecture.md     Shared architecture principles
docs/compatibility.md    Backward compatibility rules
```

## Using This Repo

```bash
# Run conformance tests against your implementation
API_URL=http://localhost:8000 API_TOKEN=xxx python3 tests/conformance/run_conformance.py
```

## License

MIT
