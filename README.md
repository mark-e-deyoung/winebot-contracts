# WineBot Contracts

Portable behavioral contracts and conformance tests shared where WinBot and WineBot expose genuinely equivalent consumer semantics.

| Project | Runtime Engine | Repository |
|:---|:---|:---|
| **WineBot** | Containerized Wine (Linux/Docker) | [SemperSupra/WineBot](https://github.com/SemperSupra/WineBot) |
| **WinBot** | Cloned Windows VM (Hyper-V) | [mark-e-deyoung/WinBot](https://github.com/mark-e-deyoung/WinBot) |

This repository is a **thin cross-runtime conformance authority**, not a shared runtime/control plane and not a requirement for universal feature parity. Stable portable behavior belongs in the required core. Substrate-specific behavior should be capability-qualified and tested only when an implementation claims that capability.

Do not add fleet orchestration, package/distribution ownership, shared session arbitration, generalized runtime lifecycle management, or implementation-specific compatibility shims here merely to make WinBot and WineBot look identical. Runtime-local mechanics remain with the runtime that owns them unless repeated cross-runtime evidence earns a smaller shared contract.

Legacy shared control-plane implementations currently present under `src/winebot_contracts/` are migration/retirement candidates tracked in issue #11. They should not gain new consumers while that cleanup is qualified.

## Structure

```
api/openapi.yaml              REST API specification
cli/winebotctl.md             CLI command contract
cli/idempotency.md            Idempotency contract
mcp/tools.json                MCP tool definitions for AI agents
tests/conformance/            pytest-based cross-project conformance tests
schemas/session.json          Session manifest schema
docs/architecture.md          Shared architecture principles
docs/compatibility.md         Backward compatibility rules
```

## Conformance model

Classify shared behavior as one of:

- **portable required core** — semantics every conforming embodiment can legitimately expose;
- **capability-qualified extension** — semantics required only when the implementation advertises the capability;
- **implementation-specific** — behavior owned by one runtime and not part of the portable contract.

A missing substrate capability should be explicit and machine-readable rather than synthesized solely for parity. Backward-compatible migration should precede retirement of existing consumer-visible behavior.

## Using This Repo

### Run conformance tests against an implementation

```bash
# Install test dependencies
pip install -r tests/conformance/requirements.txt

# Run against WineBot or WinBot
pytest tests/conformance/ -v \
  --api-url http://localhost:8000 \
  --api-token your-token-here
```

### Validate the OpenAPI spec independently

```bash
pip install openapi-spec-validator pyyaml
python -c "
import yaml
from openapi_spec_validator import validate
with open('api/openapi.yaml') as f:
    spec = yaml.safe_load(f)
validate(spec)
print('OpenAPI spec is valid')
"
```

CI consumers may check out this repository at an immutable revision and run the shared suite directly. A git submodule is optional; WineBot currently uses direct checkout rather than requiring a submodule topology.

## Current migration authority

Issue #11 is the durable authority for narrowing the historical broad-parity model. Preserve portable schemas, consumer-visible semantics, idempotency, errors/results, capability discovery, and conformance evidence. Freeze new consumers of the generalized `InputBroker` and `RuntimePlugin` implementations while retirement/migration is completed.

## License

PolyForm Noncommercial 1.0.0
