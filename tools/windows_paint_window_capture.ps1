# Window-only screenshot of a blank disposable Paint process on a public Windows runner.
# No WinBot source, desktop/taskbar capture, secrets, or raw window titles.
$ErrorActionPreference = 'Stop'
if ($env:GITHUB_ACTIONS -ne 'true') { throw 'Public hosted runner only' }
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class WinBotReferenceWin32 {
  [StructLayout(LayoutKind.Sequential)]
  public struct Rect { public int Left, Top, Right, Bottom; }
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out Rect r);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int mode);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr hdc, uint flags);
}
'@
$PIDSession = [System.Diagnostics.Process]::GetCurrentProcess().SessionId
$p = $null
try {
    $p = Start-Process -FilePath 'mspaint.exe' -PassThru -ErrorAction Stop
    $w = $null
    for ($i=0; $i -lt 20; $i++) {
        Start-Sleep -Milliseconds 500
        $candidates = @(Get-Process -Name 'mspaint' -ErrorAction SilentlyContinue |
            Where-Object { $_.SessionId -eq $PIDSession -and $_.MainWindowHandle -ne 0 })
        if ($candidates.Count -gt 0) { $w = $candidates[0]; break }
    }
    if ($null -eq $w) {
        Write-Output 'REFERENCE_PAINT_VISUAL=NO_WINDOW'
        return
    }
    $hwnd = $w.MainWindowHandle
    $element = [System.Windows.Automation.AutomationElement]::FromHandle($hwnd)
    if ($null -eq $element -or $element.Current.ProcessId -ne $w.Id) {
        Write-Output 'REFERENCE_PAINT_VISUAL=UIA_PROCESS_UNVERIFIED'
        return
    }
    # Fresh Notepad is required; an existing/saved document is never captured.
    if ($w.MainWindowTitle -notmatch 'Untitled|Unbenannt') {
        Write-Output 'REFERENCE_PAINT_VISUAL=NONEMPTY_DOCUMENT'
        return
    }
    [void][WinBotReferenceWin32]::ShowWindow($hwnd, 9)
    [void][WinBotReferenceWin32]::SetForegroundWindow($hwnd)
    Start-Sleep -Milliseconds 500
    if ([WinBotReferenceWin32]::GetForegroundWindow() -ne $hwnd) {
        Write-Output 'REFERENCE_PAINT_VISUAL=FOCUS_UNVERIFIED'
        return
    }
    # A new blank Paint document is the only admissible public visual fixture.
    Start-Sleep -Milliseconds 400
    if ([WinBotReferenceWin32]::GetForegroundWindow() -ne $hwnd) {
        Write-Output 'REFERENCE_PAINT_VISUAL=FOCUS_LOST'
        return
    }
    $rect = New-Object WinBotReferenceWin32+Rect
    if (-not [WinBotReferenceWin32]::GetWindowRect($hwnd, [ref]$rect)) { throw 'window rectangle unavailable' }
    $bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
    $left = [Math]::Max($rect.Left, $bounds.Left)
    $top = [Math]::Max($rect.Top, $bounds.Top)
    $right = [Math]::Min($rect.Right, $bounds.Right)
    $bottom = [Math]::Min($rect.Bottom, $bounds.Bottom)
    $width = $right - $left
    $height = $bottom - $top
    if ($width -lt 400 -or $height -lt 250 -or $width -gt 2200 -or $height -gt 1600) {
        Write-Output 'REFERENCE_PAINT_VISUAL=RECT_INVALID'
        return
    }
    $bitmap = New-Object System.Drawing.Bitmap($width, $height)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    try {
        # PrintWindow renders only the verified HWND, never the background desktop.
        # CopyFromScreen of a decorated window rectangle leaked runner-console edge pixels.
        $hdc = $graphics.GetHdc()
        try {
            $printed = [WinBotReferenceWin32]::PrintWindow($hwnd, $hdc, 2)
            if (-not $printed) { $printed = [WinBotReferenceWin32]::PrintWindow($hwnd, $hdc, 0) }
        } finally {
            $graphics.ReleaseHdc($hdc)
        }
        if (-not $printed) {
            Write-Output 'REFERENCE_PAINT_VISUAL=PRINTWINDOW_UNAVAILABLE'
            return
        }
        $colors = New-Object 'System.Collections.Generic.HashSet[int]'
        for($x=0; $x -lt $width; $x += [Math]::Max([int]($width/20),1)) {
            for($y=0; $y -lt $height; $y += [Math]::Max([int]($height/20),1)) {
                [void]$colors.Add($bitmap.GetPixel($x,$y).ToArgb())
            }
        }
        if ($colors.Count -lt 6) {
            Write-Output 'REFERENCE_PAINT_VISUAL=SCREEN_UNRENDERED'
            return
        }
        New-Item -ItemType Directory -Path 'safe-native-reference' -Force | Out-Null
        $bitmap.Save((Join-Path (Resolve-Path 'safe-native-reference') 'paint-window.png'), [System.Drawing.Imaging.ImageFormat]::Png)
        Write-Output 'REFERENCE_PAINT_VISUAL=WINDOW_ONLY_CAPTURED'
        Write-Output 'REFERENCE_PAINT_SYNTHETIC_BLANK_CANVAS=true'
        Write-Output ('REFERENCE_WINDOW_SIZE_CLASS=' + $(if($width -gt 800){'large'}else{'compact'}))
        Write-Output 'PRINTWINDOW_HWND_ONLY=true'
    } finally {
        $graphics.Dispose()
        $bitmap.Dispose()
    }
} catch {
    Write-Output 'REFERENCE_PAINT_VISUAL=ERROR'
    # Do not dump exception stacks, process names or source paths into public logs.
    exit 1
} finally {
    if ($null -ne $p) {
        try { if (-not $p.HasExited) { $p.Kill() } } catch {}
        try { $p.Dispose() } catch {}
    }
}
