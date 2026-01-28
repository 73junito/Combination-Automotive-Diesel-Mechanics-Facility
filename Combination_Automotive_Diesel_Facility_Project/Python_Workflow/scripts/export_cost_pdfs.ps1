param(
    [string]$RepoRoot = "..\..\..",
    [string]$SourceDir = ".",
    [string]$TargetDir = ".\outputs",
    [switch]$Force,
    [switch]$UseLibreOffice,
    [string]$LibreOfficePath
)

Set-StrictMode -Version Latest

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$fullSourceDir = Resolve-Path -Path (Join-Path $scriptRoot $SourceDir) -ErrorAction SilentlyContinue
if (-not $fullSourceDir) { $fullSourceDir = Resolve-Path -Path (Join-Path $scriptRoot $RepoRoot) }
$fullSourceDir = $fullSourceDir.ProviderPath

$fullTargetDir = Resolve-Path -Path (Join-Path $scriptRoot $TargetDir) -ErrorAction SilentlyContinue
if (-not $fullTargetDir) { New-Item -ItemType Directory -Path (Join-Path $scriptRoot $TargetDir) | Out-Null }
$fullTargetDir = (Resolve-Path -Path (Join-Path $scriptRoot $TargetDir)).ProviderPath

Write-Host "Exporting cost PDFs from: $fullSourceDir -> $fullTargetDir" -ForegroundColor Cyan

# Mapping: source filename (search) -> output PDF name
$mappings = @(
    @{ search = 'essential_equipment.csv'; alt = 'essential_equipment.xlsx'; out = 'Essential_Equipment_Cost_List.pdf' },
    @{ search = 'nonessential_equipment.csv'; alt = 'nonessential_equipment.xlsx'; out = 'Nonessential_Equipment_Cost_List.pdf' },
    @{ search = 'furniture.csv'; alt = 'equipment_lists.xlsx'; out = 'Furniture_List_with_Cost.pdf' },
    @{ search = 'maintenance.csv'; alt = 'maintenance_and_replacement.csv'; out = 'Maintenance_and_Replacement_Costs.pdf' },
    @{ search = 'totals.csv'; alt = 'total_costs.xlsx'; out = 'Total_Facility_Cost_Estimate.pdf' }
)

function Find-SourceFile($name, $alt) {
    $path = Get-ChildItem -Path $fullSourceDir -Filter $name -Recurse -File -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($path) { return $path.FullName }
    if ($alt) { $path2 = Get-ChildItem -Path $fullSourceDir -Filter $alt -Recurse -File -ErrorAction SilentlyContinue | Select-Object -First 1; if ($path2) { return $path2.FullName } }
    return $null
}

function Export-WithExcel($src, $pdfPath) {
    Write-Host "Attempting Excel export: $src -> $pdfPath" -ForegroundColor Gray
    try {
        $excel = New-Object -ComObject Excel.Application
    } catch {
        Write-Host "Excel COM not available." -ForegroundColor Yellow; return $false
    }
    $excel.Visible = $false
    $wb = $null
    try {
        $ext = [IO.Path]::GetExtension($src).ToLower()
        if ($ext -eq '.csv') {
            # Create a new workbook and import the CSV
            $wb = $excel.Workbooks.Add()
            $ws = $wb.Worksheets.Item(1)
            $importRange = $ws.Range('A1')
            $text = Get-Content -Path $src -Raw
            $rows = $text -split "\r?\n"
            $r = 1
            foreach ($line in $rows) {
                $cols = $line -split ','
                $c = 1
                foreach ($val in $cols) { $ws.Cells.Item($r,$c).Value2 = $val; $c++ }
                $r++
            }
        } else {
            $wb = $excel.Workbooks.Open($src)
        }

        foreach ($ws in $wb.Worksheets) {
            $ws.PageSetup.Orientation = 2 # xlLandscape
            $ws.PageSetup.Zoom = $false
            $ws.PageSetup.FitToPagesWide = 1
            $ws.PageSetup.FitToPagesTall = $false
        }
        $wb.ExportAsFixedFormat(0, $pdfPath)
        $wb.Close($false)
        $excel.Quit()
        [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
        return $true
    } catch {
        Write-Warning "Excel export failed: $_"
        if ($wb) { $wb.Close($false) }
        try { $excel.Quit(); [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null } catch {}
        return $false
    }
}

function Export-WithSOffice($src, $pdfPath) {
    Write-Host "Attempting LibreOffice export via soffice: $src -> $pdfPath" -ForegroundColor Gray
    $sofficePath = $null
    if ($LibreOfficePath) {
        $candidate = $LibreOfficePath
        if ($candidate -notmatch 'soffice(\.exe)?$') { $candidate = Join-Path $candidate 'program\soffice.exe' }
        if (Test-Path $candidate) { $sofficePath = (Resolve-Path $candidate).Path }
        else { Write-Host "LibreOffice not found at provided path: $LibreOfficePath" -ForegroundColor Yellow }
    }
    if (-not $sofficePath) {
        $cmd = Get-Command soffice -ErrorAction SilentlyContinue
        if ($cmd) { $sofficePath = $cmd.Path }
    }
    if (-not $sofficePath) { Write-Host "soffice not found in PATH or at provided path." -ForegroundColor Yellow; return $false }
    $outDir = Split-Path -Parent $pdfPath
    $args = @('--headless','--convert-to','pdf','--outdir',"$outDir","$src")
    $p = Start-Process -FilePath $sofficePath -ArgumentList $args -NoNewWindow -Wait -PassThru
    if ($p.ExitCode -eq 0 -and (Test-Path $pdfPath)) { return $true }
    return $false
}

foreach ($map in $mappings) {
    $src = Find-SourceFile $map.search $map.alt
    if (-not $src) { Write-Warning "Source not found for $($map.out) (searched $($map.search) and $($map.alt)). Skipping."; continue }
    $pdfPath = Join-Path $fullTargetDir $map.out
    if ((Test-Path $pdfPath) -and -not $Force) { Write-Host "PDF already exists: $pdfPath (use -Force to overwrite). Skipping." -ForegroundColor Yellow; continue }

    $ok = $false
    if (-not $UseLibreOffice) { $ok = Export-WithExcel $src $pdfPath }
    if (-not $ok) { $ok = Export-WithSOffice $src $pdfPath }

    if ($ok) { Write-Host "Exported: $pdfPath" -ForegroundColor Green } else { Write-Warning "Failed to export $src -> $pdfPath" }
}

Write-Host "Export script finished." -ForegroundColor Cyan
