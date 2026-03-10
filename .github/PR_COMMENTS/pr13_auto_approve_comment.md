Title: Add scoped workspace `autoApprove` settings — three‑tier safety model

This change adds a scoped `autoApprove` block in `.vscode/settings.json` to implement a three‑tier automation model:

- What: Introduces a three‑tier auto‑approve policy:
  - Tier 1 (low risk): keep common read/list/build commands auto‑approved (e.g. `git status`, `kubectl get`, `python`, build tooling).
  - Tier 2 (scoped auto‑approve): allow destructive or push commands only when safely scoped (e.g. `git push origin (feature|fix|chore|ci|k8s)/*`, `kubectl delete ... -n (dev|staging)`).
  - Tier 3 (guardrails): explicit denies for high‑risk actions (e.g. `git push origin main`, any unscoped `kubectl delete`) so they always require confirmation.

- Why: Preserve developer velocity for common tasks while preventing accidental prod‑level changes (wrong branch or wrong k8s namespace). This balances safety and speed and avoids wildcard execution helpers that would widen blast radius.

- Safety notes:
  - Deny rules are placed before scoped allows to be robust across matcher implementations.
  - No blanket execution helpers (e.g. `"&": true` or `"." : true`) were added.
  - The config intentionally avoids a blanket `/\.ps1$/` auto‑approve rule — prefer explicit script paths.
  - I recommend adding the following script guard to any destructive `.ps1` as a second line of defense (not applied here):

    ```powershell
    if ($env:KUBE_CONTEXT -match 'prod') { throw 'Refusing to run in prod context' }
    ```

- Files changed / commit:
  - `.vscode/settings.json` — commit: "chore: add scoped autoApprove settings (deny prod, scoped allows)" on branch `chore/types-mypy-py311`. This update is intentionally minimal and documented so reviewers can audit the exact rules.

- Request for reviewers:
  - Please confirm there are no workflows/CI hooks that require additional scoped exceptions (e.g. `release/*` branch pushes or `-n=dev` namespace syntaxes). If so, I can add narrow, explicit rules.
  - If you prefer, I can post a follow‑up to add the optional `-n=dev` or `release/*` rules after we observe actual friction.

Would you like me to post this comment to PR #13 now?