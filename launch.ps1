# Starts the Streamlit server hidden in the background, opens the app in its
# own dedicated browser window, and shuts the server down automatically once
# that window is closed.

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir
$logFile = Join-Path $scriptDir "launch.log"

function Write-Log($text) {
    "$(Get-Date -Format o)  $text" | Out-File -FilePath $logFile -Append -Encoding utf8
}

function Show-Message($text) {
    Write-Log "MESSAGE: $text"
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.MessageBox]::Show($text, "Analytics UI") | Out-Null
}

try {
    Write-Log "Launcher started. scriptDir=$scriptDir"

    $streamlitExe = Join-Path $scriptDir ".venv\Scripts\streamlit.exe"
    if (-not (Test-Path $streamlitExe)) {
        Show-Message "Could not find .venv\Scripts\streamlit.exe.`n`nLooked in:`n$streamlitExe`n`nSet up the virtual environment first (see README.md):`n  python -m venv .venv`n  .venv\Scripts\activate`n  pip install -r requirements.txt"
        exit 1
    }
    Write-Log "Found streamlit.exe at $streamlitExe"

    # Start Streamlit in the background: headless suppresses its own
    # auto-browser-open and console UI, since we drive both ourselves.
    $streamlit = Start-Process -FilePath $streamlitExe `
        -ArgumentList "run", "app.py", "--server.headless", "true" `
        -WindowStyle Hidden -PassThru
    Write-Log "Started streamlit.exe, PID=$($streamlit.Id)"

    # Wait for the server to come up before opening a browser at it.
    $ready = $false
    for ($i = 0; $i -lt 30; $i++) {
        try {
            Invoke-WebRequest -Uri "http://localhost:8501" -UseBasicParsing -TimeoutSec 2 | Out-Null
            $ready = $true
            break
        } catch {
            Start-Sleep -Seconds 1
        }
    }
    Write-Log "Server ready: $ready"
    if (-not $ready) {
        Stop-Process -Id $streamlit.Id -Force -ErrorAction SilentlyContinue
        Show-Message "Streamlit didn't start in time. Try running 'streamlit run app.py' from a terminal to see the error."
        exit 1
    }

    # Open the app in its own dedicated window (no tabs, no address bar) so we
    # can tell when the user is done with it, rather than just closing one tab
    # among many in a shared browser process.
    $edgeCandidates = @(
        "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
        "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe"
    )
    $edge = $edgeCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $edge) { $edge = "msedge.exe" }
    Write-Log "Using browser: $edge"
    Start-Process -FilePath $edge -ArgumentList "--app=http://localhost:8501"

    # Poll for that window (matched by the page title set in app.py) until it
    # has appeared at least once and then disappeared, i.e. the user closed it.
    $windowTitle = "Analytics UI"
    $seenOpen = $false
    $pollCount = 0
    while ($true) {
        Start-Sleep -Seconds 2
        $pollCount++
        $open = Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -eq $windowTitle }
        if ($open) { $seenOpen = $true }
        if ($pollCount % 15 -eq 0) { Write-Log "Still polling for window '$windowTitle'. seenOpen=$seenOpen currentlyOpen=$([bool]$open)" }
        if ($seenOpen -and -not $open) { break }
    }
    Write-Log "Window closed, shutting down streamlit PID=$($streamlit.Id)"

    # Window closed — shut down the Streamlit server and any child processes it
    # spawned, so nothing is left running in the background.
    taskkill /PID $streamlit.Id /T /F | Out-Null
    Write-Log "Shutdown complete"
} catch {
    Show-Message "Launcher failed:`n`n$($_.Exception.Message)`n`nDetails were written to launch.log next to this script."
    Write-Log "ERROR: $($_ | Out-String)"
    exit 1
}
