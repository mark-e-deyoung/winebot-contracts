# Idempotency Contract

Both implementations must provide idempotent operations via `X-Operation-Id` header.

## Header
```
X-Operation-Id: op-<12-char-hex>
```

## Behavior

**First call** with operation_id=X: Execute, store result, return `cache-control: miss`

**Subsequent calls** with operation_id=X: Return cached result, `cache-control: hit`

## Operations API
```
GET  /operations                 List recent (limit 200)
GET  /operations/{operation_id}  Get cached result
```

## Lifecycle
```
pending → running → complete | failed | timeout
```

Same operation_id always returns original result (no re-execution of failed ops).
Failed operations can retry with a new operation_id.
