Patch preview: `proposed_settings_auto_approve.json`

How to apply (manual, no commit):

1. Open your VS Code user or workspace `settings.json`.
2. Decide which settings key to use for auto-approval — many extensions expect a namespaced key (example: `"yourExtension.autoApprove"`). If you're adding to a custom extension, paste the inner object under that key.

Example — top-level insert (replace or merge):

Paste the contents of `proposed_settings_auto_approve.json` at top-level in `settings.json` or merge under the extension-specific key like:

"yourExtension.autoApprove": { <contents of the file's `autoApprove` object> }

Notes and safety checks:
- The file uses plain ASCII spaces — do not paste from a rich editor that may insert NBSPs.
- The deny rules are intentionally placed before scoped allows to avoid engines that apply first-match semantics.
- Do NOT add a blanket `"/\\.ps1$/": { "approve": true }` rule; use explicit, known script paths if needed.

If you'd like, I can now produce a unified-diff preview that shows an insertion into your actual `settings.json` file (no commit) — say "diff preview" and I'll generate it.