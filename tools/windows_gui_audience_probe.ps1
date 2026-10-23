# Public, disposable Windows runner CAPABILITY PROBE; not a WinBot guest.
# Never capture screenshots or publish raw window names/user/runner identity.
$ErrorActionPreference = 'Stop'
if ($env:GITHUB_ACTIONS -ne 'true') { throw 'This probe is limited to disposable GitHub Actions' }

$process = [System.Diagnostics.Process]::GetCurrentProcess()
$zero = $process.SessionId -eq 0
$interactive = [Environment]::UserInteractive
$uiaReady = $false
try {
    Add-Type -AssemblyName UIAutomationClient -ErrorAction Stop
    Add-Type -AssemblyName UIAutomationTypes -ErrorAction Stop
    $uiaReady = $true
} catch {
    # UI Automation may be unavailable in the hosted service/session.
}

Write-Output ('VENUE=GITHUB_HOSTED_WINDOWS_REFERENCE_NOT_WINBOT')
Write-Output ('SESSION_ZERO=' + $zero.ToString().ToLowerInvariant())
Write-Output ('USER_INTERACTIVE=' + $interactive.ToString().ToLowerInvariant())
Write-Output ('UIA_ASSEMBLY_AVAILABLE=' + $uiaReady.ToString().ToLowerInvariant())

$programs = @(
    @{ Name = 'Notepad'; Exe = 'notepad.exe'; Proc = 'notepad' },
    @{ Name = 'Paint'; Exe = 'mspaint.exe'; Proc = 'mspaint' },
    @{ Name = 'Calculator'; Exe = 'calc.exe'; Proc = 'CalculatorApp' }
)
$started = New-Object 'System.Collections.Generic.List[System.Diagnostics.Process]'
try {
    foreach ($spec in $programs) {
        $launched = $false
        $visible = $false
        $uiaMatched = $false
        try {
            $p = Start-Process -FilePath $spec.Exe -PassThru -ErrorAction Stop
            if ($null -ne $p) { $started.Add($p) }
            $launched = $true
            Start-Sleep -Seconds 2
            $procs = @(Get-Process -Name $spec.Proc -ErrorAction SilentlyContinue |
                Where-Object { $_.SessionId -eq $process.SessionId })
            $visible = @($procs | Where-Object { $_.MainWindowHandle -ne 0 }).Count -gt 0
            if ($uiaReady -and $visible) {
                try {
                    $root = [System.Windows.Automation.AutomationElement]::RootElement
                    $collection = $root.FindAll(
                        [System.Windows.Automation.TreeScope]::Children,
                        [System.Windows.Automation.Condition]::TrueCondition
                    )
                    foreach ($window in $collection) {
                        $windowPid = $window.Current.ProcessId
                        if (@($procs | Where-Object { $_.Id -eq $windowPid }).Count -gt 0) {
                            $uiaMatched = $true
                            break
                        }
                    }
                } catch {
                    $uiaMatched = $false
                }
            }
        } catch {
            # Only report safe classifications. Do not echo exception text/paths.
        }
        Write-Output ($spec.Name.ToUpperInvariant() +
            '_PROCESS_LAUNCH=' + $launched.ToString().ToLowerInvariant())
        Write-Output ($spec.Name.ToUpperInvariant() +
            '_WINDOW_VISIBLE=' + $visible.ToString().ToLowerInvariant())
        Write-Output ($spec.Name.ToUpperInvariant() +
            '_UIA_TOPLEVEL=' + $uiaMatched.ToString().ToLowerInvariant())
    }
} finally {
    foreach ($p in $started) {
        try {
            if (-not $p.HasExited) { $p.CloseMainWindow() | Out-Null; Start-Sleep -Milliseconds 250 }
            if (-not $p.HasExited) { $p.Kill() }
        } catch {
            # Stop only processes launched by this probe.
        }
        try { $p.Dispose() } catch {}
    }
}
Write-Output 'NO_SCREENSHOTS_OR_RAW_WINDOW_NAMES_PUBLISHED=true'
