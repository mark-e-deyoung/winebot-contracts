# Shared Architecture

## Core Principles

1. **Idempotent Core** — Every mutating operation is idempotent via operation_id
2. **REST API First** — CLI, GUI, WebUI, MCP are all API clients
3. **Session Isolation** — Each session has unique ID and isolated directory
4. **Input Pipeline** — API → backend (AHK/Win32) → runtime → application
5. **CV/OCR Sidecar** — Separate process, optional, graceful degradation
6. **OS Credential Manager** — No plaintext tokens on disk
7. **Graceful Degradation** — No sidecar? No problem. No VNC? Works headlessly.

## Diagram

```
winebotctl CLI / MCP Server / WebUI
              ↓
       REST API (:8000)
              ↓
   ┌─────────┼─────────┐
   │ Recorder │ Input   │
   │ Sessions │ Tracer  │
   └─────────┼─────────┘
             ↓
    Runtime Engine
    WineBot: Wine+Xvfb
    WinBot:  Windows VM
             ↓
    CV/OCR Sidecar (:8001)
    (optional — OpenCV+Tesseract+YOLO)
```

## Platform Differences

| Feature | WineBot | WinBot |
|:---|:---|:---|
| Display | Xvfb `:99` | Native Windows display |
| Input backend | AHK + xdotool | Win32 + AHK |
| Process management | `wineserver -k` | `taskkill` |
| Recording | ffmpeg x11grab | ffmpeg gdigrab |
| Font rendering | Wine (lower contrast) | Native ClearType |
