# Real stock Windows UI Automation capability census, never reads control values.
# Public hosted runner reference only; not a WinBot guest or permissioned actor.
$ErrorActionPreference = 'Stop'
if ($env:GITHUB_ACTIONS -ne 'true') { throw 'Disposable GitHub Actions only' }
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$ownSession = [System.Diagnostics.Process]::GetCurrentProcess().SessionId
$apps = @(
    @{ Name='Notepad'; Exe='notepad.exe'; Proc='notepad' },
    @{ Name='Paint'; Exe='mspaint.exe'; Proc='mspaint' }
)
foreach($app in $apps) {
    $p = $null
    $observed = $false
    $edit = -1
    $button = -1
    $menu = -1
    $textOrValuePattern = $false
    try {
        $p = Start-Process -FilePath $app.Exe -PassThru -ErrorAction Stop
        $w = $null
        for($n=0; $n -lt 15; $n++) {
            Start-Sleep -Milliseconds 400
            $candidates = @(Get-Process -Name $app.Proc -ErrorAction SilentlyContinue |
                Where-Object { $_.SessionId -eq $ownSession -and $_.MainWindowHandle -ne 0 })
            if($candidates.Count) {$w = $candidates[0];break}
        }
        if($null -ne $w) {
            $root = [System.Windows.Automation.AutomationElement]::FromHandle($w.MainWindowHandle)
            if($null -ne $root -and $root.Current.ProcessId -eq $w.Id) {
                $observed = $true
                foreach($category in @(
                    @{ Key='edit'; C=[System.Windows.Automation.ControlType]::Edit },
                    @{ Key='button'; C=[System.Windows.Automation.ControlType]::Button },
                    @{ Key='menu'; C=[System.Windows.Automation.ControlType]::MenuItem }
                )) {
                    $condition = New-Object System.Windows.Automation.PropertyCondition(
                        [System.Windows.Automation.AutomationElement]::ControlTypeProperty,$category.C)
                    $nodes = $root.FindAll([System.Windows.Automation.TreeScope]::Descendants,$condition)
                    switch($category.Key) {
                        'edit' {$edit = $nodes.Count}
                        'button' {$button = $nodes.Count}
                        'menu' {$menu = $nodes.Count}
                    }
                    if($category.Key -eq 'edit') {
                        foreach($node in $nodes) {
                            $pattern = $null
                            try {
                                if($node.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern,[ref]$pattern)) {
                                    $textOrValuePattern=$true;break
                                }
                                if($node.TryGetCurrentPattern([System.Windows.Automation.TextPattern]::Pattern,[ref]$pattern)) {
                                    $textOrValuePattern=$true;break
                                }
                            } catch {}
                        }
                    }
                }
            }
        }
    } catch {
        # No raw errors, window titles, process properties, or host identity output.
    } finally {
        if($null -ne $p) {
            try {if(-not $p.HasExited){$p.Kill()}}catch{}
            try {$p.Dispose()}catch{}
        }
    }
    $prefix = $app.Name.ToUpperInvariant()
    Write-Output ($prefix + '_UIA_SEMANTIC_WINDOW=' + $observed.ToString().ToLowerInvariant())
    foreach($metric in @(@('EDIT',$edit),@('BUTTON',$button),@('MENUITEM',$menu))) {
        $count=$metric[1]
        $class=if($count -lt 0){'unavailable'}elseif($count -eq 0){'zero'}elseif($count -le 10){'1-10'}else{'11-plus'}
        Write-Output ($prefix + '_UIA_' + $metric[0] + '_COUNT_CLASS=' + $class)
    }
    Write-Output ($prefix + '_UIA_EDITOR_PATTERN=' + $textOrValuePattern.ToString().ToLowerInvariant())
}
Write-Output 'NO_UIA_VALUES_OR_RAW_WINDOW_NAMES_PUBLISHED=true'
