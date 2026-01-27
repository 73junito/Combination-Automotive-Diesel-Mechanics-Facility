<#
PowerShell helper to convert DXF → SVG using Inkscape CLI (Windows)
Usage examples:
  .\convert_dxf_to_svg.ps1 -InputPath .\Drawings\CAD\layout.dxf -OutputPath .\outputs\layout.svg
  .\convert_dxf_to_svg.ps1 -InputPath layout.dxf -OutputPath layout.svg -InkscapePath "C:\Program Files\Inkscape\bin\inkscape.exe"

Notes:
- Requires Inkscape installed. Script tries PATH then common Program Files path.
- Attempts both modern and legacy CLI flags for compatibility.
#>
param(
    [Parameter(Mandatory=$true)][string]$InputPath,
    [Parameter(Mandatory=$true)][string]$OutputPath,
    [string]$InkscapePath
)

function Find-Inkscape {
    param($hint)
    if ($hint) {
        if (Test-Path $hint) { return (Resolve-Path $hint).Path }
    }
    $cmd = Get-Command inkscape -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Path }
    $candidates = @(
        "C:\Program Files\Inkscape\bin\inkscape.exe",
        "C:\Program Files\Inkscape\inkscape.exe",
        "C:\Program Files (x86)\Inkscape\inkscape.exe"
    )
    foreach ($p in $candidates) { if (Test-Path $p) { return $p }}
    return $null
}

$inkscape = Find-Inkscape -hint $InkscapePath
if (-not $inkscape) {
    Write-Error "Inkscape not found. Please install Inkscape or pass -InkscapePath."
    exit 2
}

$in = (Resolve-Path $InputPath).Path
$out = (Resolve-Path -LiteralPath $(Split-Path -Parent $OutputPath) -ErrorAction SilentlyContinue)
if (-not $out) { New-Item -ItemType Directory -Path (Split-Path -Parent $OutputPath) -Force | Out-Null }
$outFile = (Resolve-Path -LiteralPath (Split-Path -Parent $OutputPath) -ErrorAction SilentlyContinue) | ForEach-Object { Join-Path $_ (Split-Path $OutputPath -Leaf) }
$outFile = $OutputPath

Write-Host "Using Inkscape: $inkscape"
Write-Host "Converting: $in → $outFile"

# Try modern CLI first (Inkscape 1.0+)
$attempt1 = & "$inkscape" --batch-process --export-type=svg --export-filename="$outFile" "$in" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "Converted with modern Inkscape CLI."
    exit 0
}

# Fallback: legacy CLI (older Inkscape)
$attempt2 = & "$inkscape" "$in" --export-plain-svg="$outFile" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "Converted with legacy Inkscape CLI."
    exit 0
}

Write-Error "Conversion failed. Inkscape output:\n$attempt1\n$attempt2"
exit $LASTEXITCODE
