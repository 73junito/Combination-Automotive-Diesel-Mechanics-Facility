$tag = 'v1.1.0'
$zip = 'Combination_Automotive_Diesel_Facility_Project\Python_Workflow\outputs\portfolio_submission.zip'
$notesPath = 'RELEASE_NOTES_v1.1.0_draft.md'

# Check if tag exists
& git rev-parse -q --verify refs/tags/$tag > $null 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Output 'TAG_EXISTS'
} else {
    & git tag -a $tag -m "v1.1.0 - portfolio submission (verified outputs)"
    if ($LASTEXITCODE -ne 0) { Write-Output 'TAG_CREATE_FAILED'; exit 0 }
    & git push origin $tag
    if ($LASTEXITCODE -eq 0) { Write-Output 'TAG_PUSHED' } else { Write-Output 'TAG_PUSH_FAILED' }
}

# Create GitHub release if gh is available
if (Get-Command gh -ErrorAction SilentlyContinue) {
    if (Test-Path $notesPath) { $notes = Get-Content -Raw $notesPath } else { $notes = 'Verified portfolio submission release.' }
    gh release create $tag -t $tag -n "$notes" $zip
    if ($LASTEXITCODE -eq 0) { Write-Output 'GH_RELEASE_CREATED' } else { Write-Output 'GH_RELEASE_FAILED' }
} else {
    Write-Output 'GH_NOT_FOUND'
}
