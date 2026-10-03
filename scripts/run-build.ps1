# Qualia autonomous build runner (Windows PowerShell 5.1).
# Relaunches a fresh Codex session until docs/BUILD-STATE.md starts with "BUILD COMPLETE"
# or OWNER-NEEDED.md exists. First session gets the kickoff prompt, later ones the recovery prompt.
# Owner alerts go to the ntfy topic in scripts/ntfy-topic.local (gitignored). See docs/03 §2.
param([int]$MaxRuns = 60, [int]$WaitMinutes = 30, [string]$Model = "")

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$state = Join-Path $root "docs\BUILD-STATE.md"
$owner = Join-Path $root "OWNER-NEEDED.md"
$topicFile = Join-Path $PSScriptRoot "ntfy-topic.local"
$logs = Join-Path $root "logs"
New-Item -ItemType Directory -Force $logs | Out-Null
$OutputEncoding = [System.Text.Encoding]::UTF8   # prompts contain non-ASCII; PS 5.1 defaults to ASCII for native stdin

# Keep the PC awake while this window runs (process-level request; no system setting changes).
Add-Type -Namespace Qualia -Name Power -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint f);'
[Qualia.Power]::SetThreadExecutionState([uint32]"0x80000001") | Out-Null

function Notify([string]$title, [string]$body) {
  if (-not (Test-Path $topicFile)) { return }
  $topic = (Get-Content $topicFile -Raw).Trim()
  try { Invoke-RestMethod -Method Post -Uri "https://ntfy.sh/$topic" -Headers @{ Title = $title; Priority = "4" } -Body $body | Out-Null } catch {}
}
function StateHash { if (Test-Path $state) { (Get-FileHash $state).Hash } else { "" } }

$stalls = 0
for ($run = 1; $run -le $MaxRuns; $run++) {
  if (Test-Path $owner) {
    Notify "Qualia: owner needed" ((Get-Content $owner -Raw) + "`nAnswer per docs/03 section 7, then relaunch.")
    Write-Host "OWNER-NEEDED.md exists - stopping. See docs/03 section 7."; exit 2
  }
  if ((Test-Path $state) -and ((Get-Content $state -TotalCount 1) -match '^BUILD COMPLETE')) {
    Notify "Qualia: build complete" "Open WELCOME-BACK.md. Next: docs/03 section 8."
    Write-Host "Build complete."; exit 0
  }
  $promptFile = if (Test-Path $state) { "recovery.md" } else { "kickoff.md" }
  $prompt = Get-Content (Join-Path $PSScriptRoot "prompts\$promptFile") -Raw -Encoding UTF8
  $before = StateHash
  $log = Join-Path $logs ("run-{0:D3}.log" -f $run)
  $cx = @("exec", "-s", "workspace-write", "-c", 'approval_policy="never"', "-c", "sandbox_workspace_write.network_access=true")
  if ($Model) { $cx += @("-m", $Model) }
  Write-Host ("[{0}] run {1}: {2}" -f (Get-Date -Format "HH:mm"), $run, $promptFile)
  $prompt | & codex @cx - *> $log
  # Only the tail: the session's own text may mention rate limits (e.g. Jev 429 handling).
  if (Get-Content $log -Tail 15 | Select-String -Pattern 'usage limit|rate limit|too many requests' -Quiet) {
    Write-Host "Usage limit hit - waiting $WaitMinutes min (expected, not an emergency)."
    Start-Sleep -Seconds ($WaitMinutes * 60); continue
  }
  if ((StateHash) -eq $before) { $stalls++ } else { $stalls = 0 }
  if ($stalls -ge 3) {
    "# Owner needed`nThe runner saw three sessions in a row with no BUILD-STATE progress.`nLast log: $log`n" | Set-Content $owner -Encoding UTF8
  }
}
Notify "Qualia: runner stopped" "Reached $MaxRuns runs without finishing. Relaunch per docs/03 section 2."
exit 1
