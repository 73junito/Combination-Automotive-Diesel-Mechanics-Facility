$bodyFile = "$env:TEMP\pr13_body.md"

gh pr view 13 --json body --jq .body | Out-File -FilePath $bodyFile -Encoding utf8

$note = '**Note:** This PR introduces a scoped, three-tier `autoApprove` safety model for workspace automation. See the pinned PR comment below for rationale, guardrails, and reviewer notes.'

if (-not (Select-String -Path $bodyFile -Pattern 'autoApprove' -Quiet)) {
    Add-Content -Path $bodyFile -Value "`n`n$note"
    gh pr edit 13 --body-file $bodyFile
    Write-Output 'UPDATED'
} else {
    Write-Output 'ALREADY_PRESENT'
}
