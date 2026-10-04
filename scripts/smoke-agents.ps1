param(
    [Parameter(Mandatory=$true)][string]$Project,
    [ValidateSet('claude','codex')][string[]]$Agents = @('claude','codex')
)
$ErrorActionPreference = 'Stop'
foreach ($agent in $Agents) {
    # The public CLI enforces readiness, clean baseline, policy and budget.
    # A failed readiness gate stops this script before trying another agent.
    uv run qualia improve --project $Project --agent $agent --budget 1
    if ($LASTEXITCODE -ne 0) { throw "$agent parity check failed or remains unavailable; inspect the public CLI reason." }
}
