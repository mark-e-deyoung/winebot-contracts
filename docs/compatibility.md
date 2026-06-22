# Backward Compatibility

## Breaking Changes (require version bump)
- Removing an endpoint
- Removing a field from a response
- Changing a field type
- Adding a required request field

## Non-Breaking (same version)
- Adding a new endpoint
- Adding an optional request field
- Adding a response field

## Deprecation
1. Mark deprecated in OpenAPI spec
2. Add `Deprecation: true` response header
3. Add `Sunset: <date>` (90 days)
4. Log deprecation warnings
5. Remove in next major version

## Contract Version Sync

| Contract | WineBot | WinBot |
|:---|:---|:---|
| v1.0 | v0.9.7+ | v0.1.0+ |

## Conformance Test Suite
```
tests/conformance/run_conformance.py
```
Run against either implementation with `API_URL` and `API_TOKEN` env vars.
