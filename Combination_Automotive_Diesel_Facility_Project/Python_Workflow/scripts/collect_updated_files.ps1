if ($env:KUBE_CONTEXT -match 'prod') {
    throw 'Refusing to run in prod context'
}

param(
    [string]$SourceDir = "..\..\Python_Workflow\outputs",
    [string]$TargetDir = ".\outputs",
    [int]$SinceMinutes = 1440,
    [string[]]$IncludeExtensions = @('*.pdf','*.png'),
    [string]$ZipName = '',
    [switch]$Force
)

Set-StrictMode -Version Latest

# Resolve paths relative to script location
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$FullSource = Resolve-Path -Path (Join-Path $ScriptRoot $SourceDir) -ErrorAction SilentlyContinue
if (-not $FullSource) { throw "Source directory not found: $SourceDir (resolved from $ScriptRoot)" }
$FullSource = $FullSource.ProviderPath

$FullTarget = Resolve-Path -Path (Join-Path $ScriptRoot $TargetDir) -ErrorAction SilentlyContinue
if (-not $FullTarget) { New-Item -ItemType Directory -Path (Join-Path $ScriptRoot $TargetDir) | Out-Null }
$FullTarget = (Resolve-Path -Path (Join-Path $ScriptRoot $TargetDir)).ProviderPath

Write-Host "Collecting files modified in the last $SinceMinutes minute(s) from:`n  $FullSource`ninto:`n  $FullTarget" -ForegroundColor Cyan

$sinceTime = (Get-Date).AddMinutes(-$SinceMinutes)

$collected = @()
foreach ($pattern in $IncludeExtensions) {
    $items = Get-ChildItem -Path $FullSource -Filter $pattern -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -gt $sinceTime }
    foreach ($it in $items) {
        $rel = $it.FullName.Substring($FullSource.Length).TrimStart('\','/')
        $dest = Join-Path $FullTarget $rel
        $destDir = Split-Path -Parent $dest
        if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir | Out-Null }
        if ((Test-Path $dest) -and -not $Force) {
            Write-Host "Skipping existing file (use -Force to overwrite): $rel" -ForegroundColor Yellow
            continue
        }
        Copy-Item -Path $it.FullName -Destination $dest -Force
        $collected += $dest
        Write-Host "Copied: $rel" -ForegroundColor Green
    }
}

if ($collected.Count -eq 0) {
    Write-Host "No updated files found within the last $SinceMinutes minutes." -ForegroundColor Yellow
    exit 0
}

if ($ZipName) {
    $zipPath = Join-Path $FullTarget $ZipName
    if ((Test-Path $zipPath) -and -not $Force) {
        Write-Host "Zip already exists: $zipPath (use -Force to overwrite)" -ForegroundColor Yellow
    }
    else {
        if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
        Compress-Archive -Path $collected -DestinationPath $zipPath -Force
        Write-Host "Created zip: $zipPath" -ForegroundColor Cyan
    }
}

Write-Host "Done. Collected $($collected.Count) file(s)." -ForegroundColor Cyan
