<#
zip_outputs.ps1
Create a ZIP bundle of SVG and PNG visuals in an outputs folder.

Usage:
  .\zip_outputs.ps1 -OutputDir ".\Python_Workflow\scripts\outputs"
  .\zip_outputs.ps1 -OutputDir ".\Python_Workflow\scripts\outputs" -ZipName visuals_bundle.zip -Force

Parameters:
  -OutputDir   Folder to search for .svg/.png files (default: ./outputs)
  -ZipName     Name of the zip file to create inside OutputDir (default: visuals_bundle.zip)
  -Extensions  Array of extensions to include (default: svg,png)
  -Force       Overwrite existing zip
#>

param(
    [string]$OutputDir = "./outputs",
    [string]$ZipName = "visuals_bundle.zip",
    [string[]]$Extensions = @("svg","png"),
    [switch]$Force
)

$OutFull = Resolve-Path -LiteralPath $OutputDir -ErrorAction SilentlyContinue
if (-not $OutFull) {
    Write-Error "Output directory not found: $OutputDir"
    exit 2
}
$OutFull = $OutFull.Path
$zipPath = Join-Path $OutFull $ZipName

# Collect files with matching extensions (non-recursive)
$files = Get-ChildItem -Path $OutFull -File | Where-Object { $Extensions -contains ($_.Extension.TrimStart('.').ToLower()) }
if (-not $files -or $files.Count -eq 0) {
    Write-Warning "No files with extensions $($Extensions -join ',') found in $OutFull. Nothing to zip."
    exit 0
}

# Remove existing zip if requested
if (Test-Path $zipPath) {
    if ($Force) { Remove-Item $zipPath -Force; Write-Host "Existing zip removed: $zipPath" }
    else { Write-Error "Zip already exists: $zipPath. Use -Force to overwrite."; exit 3 }
}

# Create temporary list file for compress-archive support of many files
$paths = $files | ForEach-Object { $_.FullName }

try {
    Compress-Archive -Path $paths -DestinationPath $zipPath -Force
    Write-Host "Created zip: $zipPath"
} catch {
    Write-Error "Failed to create zip: $_"
    exit 4
}

exit 0
