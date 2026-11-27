param(
    [int]$WindowDays = 28,
    [string]$OutputPath = "docs/devops/evidence/dora-source-2026-11-27.json"
)

$ErrorActionPreference = "Stop"

function Invoke-GhJson {
    param([string]$Endpoint, [switch]$Paginate)
    if ($Paginate) {
        $raw = gh api --paginate --slurp $Endpoint
    } else {
        $raw = gh api $Endpoint
    }
    if ($LASTEXITCODE -ne 0) { throw "GitHub metadata query failed: $Endpoint" }
    return ConvertFrom-Json -InputObject ($raw -join "`n") -NoEnumerate
}

function ConvertTo-UtcString {
    param([datetimeoffset]$Value)
    return $Value.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.ffffffZ")
}

function Normalize-ApiTimestamp {
    param([object]$Value)
    if ($null -eq $Value) { return "" }
    if ($Value -is [datetime]) { return ConvertTo-UtcString ([datetimeoffset]$Value) }
    if ($Value -is [datetimeoffset]) { return ConvertTo-UtcString $Value }
    return ConvertTo-UtcString ([datetimeoffset]::Parse([string]$Value))
}

function In-Window {
    param([string]$Value, [datetimeoffset]$Start, [datetimeoffset]$End)
    if (-not $Value) { return $false }
    $time = [datetimeoffset]::Parse($Value).ToUniversalTime()
    return $time -ge $Start -and $time -le $End
}

if ($WindowDays -lt 1 -or $WindowDays -gt 90) { throw "WindowDays must be between 1 and 90." }
$end = [datetimeoffset]::UtcNow
$start = $end.AddDays(-$WindowDays)
$repo = "kendshhh/PhishLens"
$productionServiceId = "srv-db7eap25b2lc73fkelpg"
$historyPath = "docs/devops/evidence/production-deploys-2026-11-14.csv"
if (-not (Test-Path -LiteralPath $historyPath)) { throw "Required historical Render evidence is missing: $historyPath" }

$main = Invoke-GhJson "repos/$repo/commits/main"
$ciPages = Invoke-GhJson "repos/$repo/actions/workflows/ci.yml/runs?branch=main&per_page=100" -Paginate
$prPages = Invoke-GhJson "repos/$repo/pulls?state=closed&sort=updated&direction=desc&per_page=100" -Paginate
$recentDeploys = render deploys list $productionServiceId --output json | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw "Render production deploy metadata query failed." }

$ciRuns = [System.Collections.Generic.List[object]]::new()
foreach ($page in $ciPages) {
    foreach ($run in $page.workflow_runs) {
        if ($run.status -ne "completed" -or $run.event -ne "push" -or $run.head_branch -ne "main" -or
            -not (In-Window $run.created_at $start $end)) { continue }
        $ciRuns.Add([pscustomobject]@{
            run_id = [long]$run.id
            sha = [string]$run.head_sha
            event = [string]$run.event
            branch = [string]$run.head_branch
            created_at_utc = Normalize-ApiTimestamp $run.created_at
            started_at_utc = Normalize-ApiTimestamp $run.run_started_at
            finished_at_utc = Normalize-ApiTimestamp $run.updated_at
            conclusion = [string]$run.conclusion
            url = [string]$run.html_url
        })
    }
}

$mergedPullRequests = [System.Collections.Generic.List[object]]::new()
foreach ($page in $prPages) {
    foreach ($pr in $page) {
        if (-not (In-Window $pr.merged_at $start $end)) { continue }
        $mergedPullRequests.Add([pscustomobject]@{
            number = [int]$pr.number
            merge_sha = [string]$pr.merge_commit_sha
            head_sha = [string]$pr.head.sha
            base_branch = [string]$pr.base.ref
            merged_at_utc = Normalize-ApiTimestamp $pr.merged_at
        })
    }
}

# The Render CLI returns the most recent 20 deploys. Combine those live records
# with the retained, immutable 69-row inventory ending Nov 14, then deduplicate.
$deployById = @{}
foreach ($row in (Import-Csv -LiteralPath $historyPath)) {
    if (-not (In-Window $row.created_at_utc $start $end)) { continue }
    $deployById[$row.deploy_id] = [pscustomobject]@{
        deploy_id = [string]$row.deploy_id
        sha = [string]$row.commit_sha
        created_at_utc = [string]$row.created_at_utc
        started_at_utc = [string]$row.started_at_utc
        finished_at_utc = [string]$row.finished_at_utc
        status = [string]$row.status
        trigger = [string]$row.trigger
        source = "retained-render-inventory-2026-11-14"
    }
}
foreach ($row in $recentDeploys) {
    if (-not (In-Window $row.createdAt $start $end)) { continue }
    $deployById[$row.id] = [pscustomobject]@{
        deploy_id = [string]$row.id
        sha = [string]$row.commit.id
        created_at_utc = Normalize-ApiTimestamp $row.createdAt
        started_at_utc = Normalize-ApiTimestamp $row.startedAt
        finished_at_utc = Normalize-ApiTimestamp $row.finishedAt
        status = [string]$row.status
        trigger = [string]$row.trigger
        source = "render-cli-live-inventory"
    }
}
$deployments = @($deployById.Values | Sort-Object created_at_utc)
$liveDeploy = $recentDeploys | Where-Object { $_.status -eq "live" } | Select-Object -First 1

$snapshot = [ordered]@{
    schema_version = 1
    repository = $repo
    collected_at_utc = ConvertTo-UtcString $end
    window_utc = [ordered]@{
        start = ConvertTo-UtcString $start
        end = ConvertTo-UtcString $end
        duration_days = $WindowDays
    }
    current_main_sha = [string]$main.sha
    production_sha = if ($liveDeploy) { [string]$liveDeploy.commit.id } else { $null }
    source_urls = [ordered]@{
        ci_runs = "https://api.github.com/repos/$repo/actions/workflows/ci.yml/runs?branch=main&per_page=100"
        merged_pull_requests = "https://api.github.com/repos/$repo/pulls?state=closed&per_page=100"
        production_deploys = "https://dashboard.render.com/web/$productionServiceId/deploys"
        historical_render_inventory = "docs/devops/evidence/production-deploys-2026-11-14.csv"
    }
    collection_limits = [ordered]@{
        ci_run_events = "Paginated GitHub Actions CI workflow metadata; push events on main only."
        pull_requests = "Paginated GitHub closed-PR metadata; merged PRs in the UTC window only."
        render_deployments = "Latest Render CLI inventory plus retained Nov 14 inventory; IDs deduplicated."
        recovery_and_rework = "No authoritative incident or planned/unplanned deployment ledger is available to this collector."
    }
    ci_runs = @($ciRuns | Sort-Object started_at_utc)
    merged_pull_requests = @($mergedPullRequests | Sort-Object merged_at_utc)
    production_deployments = $deployments
    recovery_events = $null
    deployment_classifications = $null
}

$parent = Split-Path -Parent $OutputPath
if ($parent -and -not (Test-Path -LiteralPath $parent)) {
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
}
$json = $snapshot | ConvertTo-Json -Depth 10
Set-Content -LiteralPath $OutputPath -Value $json -Encoding utf8
Write-Output "Wrote current, redacted DORA source metadata to $OutputPath"
Write-Output "CI runs: $($ciRuns.Count); merged PRs: $($mergedPullRequests.Count); production deploy records: $($deployments.Count); main: $($main.sha)"
