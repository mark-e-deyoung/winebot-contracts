# winebotctl — CLI Command Contract

Both WineBot and WinBot MUST provide a `winebotctl` CLI with identical command syntax.

## Token Resolution Order

1. `--token` CLI flag
2. `WINEBOT_API_TOKEN` / `API_TOKEN` env var
3. OS credential store (Windows Credential Manager / macOS Keychain / Linux libsecret)
4. Container/VM token file

## Commands

### Health
```
winebotctl health                GET /health
winebotctl health system         GET /health/system
winebotctl health recording      GET /recording/health
```

### Lifecycle
```
winebotctl lifecycle status      GET /lifecycle/status
winebotctl lifecycle shutdown    POST /lifecycle/shutdown
winebotctl lifecycle reset-workspace  POST /lifecycle/reset_workspace
```

### Recording
```
winebotctl recording start       POST /recording/start
winebotctl recording stop        POST /recording/stop
winebotctl recording pause       POST /recording/pause
winebotctl recording resume      POST /recording/resume
winebotctl recording status      GET /recording/health
winebotctl recording perf        GET /recording/perf/summary
```

### Input
```
winebotctl input click X Y       POST /input/mouse/click
winebotctl input key KEYS        POST /input/key
winebotctl input trace start     POST /input/trace/start
winebotctl input trace stop      POST /input/trace/stop
winebotctl input trace status    GET /input/trace/status
winebotctl input trace events    GET /input/events
```

### Automation
```
winebotctl apps run PATH         POST /apps/run
winebotctl screenshot            GET /screenshot
winebotctl windows list          GET /windows
winebotctl inspect window        POST /inspect/window
```

### Credential
```
winebotctl credential list       List stored credentials
winebotctl credential get NAME   Retrieve credential from OS keychain
winebotctl credential store N V  Store credential
winebotctl credential remove N   Delete credential
winebotctl credential import-token  Import from runtime
```

### Diagnostics
```
winebotctl diag bundle           Generate support bundle
winebotctl tail SOURCE           Tail logs
```

## Exit Codes

- 0 — success
- 1 — API error (4xx/5xx)
- 2 — CLI error (bad arguments)
