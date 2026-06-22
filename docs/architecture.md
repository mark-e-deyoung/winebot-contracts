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
| Display | Xvfb `:99` (software framebuffer) | Native Windows display |
| GPU / 3D | **None** — no OpenGL, no D3D, no Vulkan | Native GPU with full DirectX/Vulkan |
| GLX support | ❌ Not available | N/A (native WGL) |
| Software rendering | GDI only (no LLVMpipe by default) | Native GDI + WARP software rasterizer |
| Input backend | AHK + xdotool | Win32 + AHK |
| Process management | `wineserver -k` | `taskkill` |
| Recording | ffmpeg x11grab | ffmpeg gdigrab |
| Font rendering | Wine libfonts (Liberation fonts) | Native ClearType |
| 2D apps (Notepad, cmd) | ✅ Full compatibility | ✅ Full compatibility |
| 2D DirectDraw games | ✅ with `DirectDraw=0` | ✅ Native DirectDraw |
| OpenGL 3D games | ❌ No GL context available | ✅ Native OpenGL |
| Direct3D apps | ❌ Requires `renderer=gdi` | ✅ Native Direct3D |
| CAD / 3D tools | ❌ No GPU | ✅ Native GPU |
| mDNS discovery | ✅ Avahi on port 5353 | ⚠️ Windows mDNS stack |
| Session dirs | `/artifacts/sessions/` (Linux path) | `C:\artifacts\sessions\` (Windows path) |

### Rendering Divergence

This is the **most significant difference** between WineBot and WinBot. WineBot
uses Xvfb — a pure software framebuffer with no GPU acceleration whatsoever.
WinBot runs on a Windows VM with full GPU passthrough and native DirectX/Vulkan
drivers.

**Impact:** Any application requiring OpenGL 2.1+, Direct3D 9+, or Vulkan will
fail in WineBot but work correctly in WinBot. This includes:
- All 3D games (SuperTux, 0 A.D., any Unity/Unreal title)
- CAD and 3D modeling tools
- GPU-accelerated ML inference (use the CV sidecar instead)
- Video encoding with hardware acceleration (CPU encoding still works)

**Contract:** Both implementations MUST report their rendering capabilities via
`GET /health/system`. The response includes a `gpu_available` boolean field.
Conformance tests verify this field is present but do not require GPU support.
Agents and CLI users should check this field before running 3D workloads.

