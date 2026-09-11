# v1 -> vNext contract classification

Status: **migration design / qualification input**. This document does not change v1 behavior and does not itself authorize runtime removal.

Authority: issue #11. The target is a small portable core plus capability-qualified extensions. Existing v1 remains reconstructable while consumers migrate.

## Classification rules

- `portable-core`: consumer-visible semantics every conforming embodiment may legitimately rely on.
- `capability-extension`: required only when the embodiment explicitly claims the capability.
- `implementation-specific`: useful runtime behavior/test, but not shared normative conformance.
- `obsolete-contract`: shared v1 assertion/field whose abstraction is no longer authoritative; remove only through explicit versioned migration.
- `unresolved`: insufficient cross-runtime evidence; do not create a shim or new capability vocabulary merely to classify it.

Capability discovery is runtime-owned. This migration must not create a global capability registry.

## Current classification

| Surface | vNext classification | Evidence / migration note |
|---|---|---|
| `GET /health` basic readiness/status | `portable-core` candidate | Both embodiments need a minimal health/readiness semantic. Exact tool/storage payload shape should not silently become portable merely because v1 contains it. |
| `/health` `hostname` | `unresolved` | Useful diagnostic identity, but portability requirement has not yet been justified. |
| `/health` `tools` and `storage` sections | `capability-extension` candidate | Environment/tool/storage introspection is useful but substrate-specific in shape. |
| `GET /health/system` | `capability-extension` candidate | Current tests already tolerate 404. |
| `/health/system.cpu_count` | `capability-extension` candidate | Meaning is portable when system-health capability is claimed. |
| `/health/system.memory` | `unresolved` | Current executable suite incorrectly makes it unconditional whenever `/health/system` exists; known WineBot evidence says memory reporting is substrate-dependent. Do not synthesize it merely for parity. |
| `GET /health/tools` | `capability-extension` candidate | Tool inventory is capability discovery/diagnostics, not a universal business semantic. |
| WinBot Python-tool assertion | `implementation-specific` | Already marked WinBot-specific. |
| `GET /health/presence` | `capability-extension` candidate | Human-presence detection depends on desktop/session semantics. |
| `GET /sessions` | `unresolved` | Session semantics need cross-runtime consumer evidence before entering portable core. |
| `GET /lifecycle/status` | `portable-core` candidate | Useful bounded-operation state semantic where lifecycle operations are present; exact state vocabulary remains subject to migration review. |
| `POST /lifecycle/shutdown` | `capability-extension` candidate | Destructive lifecycle control is not required for every replaceable embodiment. Preserve semantic contract if capability is claimed. |
| `POST /lifecycle/cancel` | `capability-extension` candidate | Coupled to claimed pending lifecycle-operation support. |
| `POST /lifecycle/restart` | `implementation-specific` / remove from portable vNext | Executable suite now classifies hot restart as WinBot-specific. v1 OpenAPI still presents it as shared; migrate explicitly rather than forcing WineBot parity. |
| `POST /input/mouse/click` | `capability-extension` candidate | Raw coordinate input is a fallback capability, not portable required core. Semantic control should remain preferred upstream. |
| `POST /input/key` | `capability-extension` candidate | Shared consumer path may remain useful, but raw keyboard injection should be capability-qualified rather than universal. |
| `POST /input/mouse/move` | `implementation-specific` / remove from portable vNext | Test and docs identify it as WinBot-specific. |
| WinBot `/input/keyboard/type` / `/input/keyboard/press` aliases | `implementation-specific` | Runtime aliases, not portable contract authority. |
| `POST /apps/run` | `capability-extension` candidate | Command/application launch is broadly useful but depends on execution capability and authority. |
| `GET /screenshot` | `capability-extension` candidate | Presentation/compatibility sensor; success can legitimately be unavailable in some session topologies. Do not make screenshot serialization the universal sensor architecture. |
| `GET /windows` | `capability-extension` candidate | Window enumeration requires a desktop/windowing capability. |
| `POST /windows/focus` | `capability-extension` candidate | Window focus/control requires a desktop control capability. |
| `POST /inspect/window` | `capability-extension` candidate | Present in executable tests but absent from current v1 OpenAPI; this is a normative/executable drift that must be reconciled before vNext promotion. |
| `POST /recording/start`, `POST /recording/stop`, `GET /recording/health` | `capability-extension` candidate | Recording is optional embodiment functionality; current tests already tolerate absence for health. |
| WinBot `/recording/status` alias | `implementation-specific` | Already marked WinBot-specific. |
| input tracing surfaces (`/input/trace/*`, `/input/events`) | `capability-extension` candidate | Diagnostics/trace capability, not universal required core. |
| WinBot `/input/trace/events` alias | `implementation-specific` | Already marked WinBot-specific. |
| operation/idempotency surfaces | `portable-core` candidate for semantics; exact endpoints `unresolved` | Stable operation identity/idempotency is cross-runtime value, but exact current API shape needs consumer/evidence review before freezing vNext. |
| `GET /version.api_version` | `portable-core` candidate | Needed to bind consumer behavior and qualification to an exact API contract. |
| `GET /version.os` | `capability-extension`/diagnostic candidate | Useful target identity, but do not use it as the capability model. |
| `GET /version.hostname` | `unresolved` | Diagnostic only unless a consumer requirement earns it. |
| `GET /version.winbot_version` | `obsolete-contract` in shared schema | Implementation-named field encodes WinBot ontology in the shared contract. Replace in vNext with implementation-neutral runtime identity/version semantics while preserving v1 compatibility during migration. |

## Immediate normative drifts to resolve

1. v1 prose says both implementations **MUST** implement canonical paths even though the accepted architecture is capability-qualified.
2. `/lifecycle/restart` remains in shared OpenAPI while the executable suite marks it WinBot-specific.
3. `/input/mouse/move` remains in shared OpenAPI while the executable suite marks it WinBot-specific.
4. `/inspect/window` is exercised by the shared suite but is missing from current v1 OpenAPI.
5. `/health/system.memory` is mandatory in the executable assertion whenever the endpoint exists despite known substrate variance.
6. `winbot_version` remains an implementation-specific field in the shared `/version` schema.

These are contract-migration defects, not instructions to add WineBot compatibility shims.

## vNext minimum candidate

Do not freeze this list until both current embodiments are exercised against the classified suite, but the smallest likely portable spine is:

- contract/runtime version identity sufficient for reconstruction;
- minimal readiness/health result;
- stable request/operation identity and idempotent-result semantics where an operation is accepted;
- explicit capability discovery / unsupported-or-unclaimed representation without requiring identical substrate mechanics;
- common error semantics for malformed, unauthorized, unsupported, and failed operations.

Everything else should begin as a capability-qualified extension unless repeated cross-runtime consumer evidence earns promotion into the portable core.

## Migration sequence

1. complete test-by-test classification and resolve the six known normative drifts above;
2. define implementation-neutral runtime identity/version fields for vNext;
3. define the smallest capability-extension vocabulary using existing runtime discovery surfaces rather than another registry;
4. make conformance output report portable-core and claimed-extension results separately;
5. bind results to exact contract revision, runtime, executor/venue, and evidence class (compatible with the execution-qualification receipt work under `windows-utilities#26`);
6. run WineBot/cloud qualification first where possible;
7. run WinBot/native qualification only on a suitable native Windows executor;
8. retire v1 compatibility assertions only after consumers migrate.

No native-Windows acceptance is implied by this classification.