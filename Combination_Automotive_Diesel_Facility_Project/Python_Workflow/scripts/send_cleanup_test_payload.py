#!/usr/bin/env python3
"""Generate and optionally POST a Slack Blocks payload that mimics
the cleanup workflow notification.

Usage:
  python send_cleanup_test_payload.py            # print payload to stdout and write docs/cleanup_test_payload.json
  python send_cleanup_test_payload.py --webhook <URL>  # POST to webhook URL

Options:
  --threshold N     Notify threshold (default 3)
  --deleted N       Number of deleted releases to synthesize (default 2)
  --max-assets N    Max assets per release (default 3)
  --output PATH     Write payload JSON to PATH (default: docs/cleanup_test_payload.json)

This script does not require extra packages and uses only the stdlib.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path


def make_sample_deleted_releases(n_deleted: int, max_assets: int) -> list[str]:
    items = []
    now = datetime.utcnow().isoformat() + "Z"
    for i in range(1, n_deleted + 1):
        pr = 100 + i
        run = i
        tag = f"mep-loadmap-pr-{pr}-run-{run}"
        html = f"https://github.com/example/repo/releases/tag/{tag}"
        name = f"Draft preview for PR #{pr}"
        assets = [
            f"<{html}/assets/{a}|asset-{a}.png>"
            for a in range(1, min(max_assets, 3) + 1)
        ]
        if max_assets > 3:
            assets.append(f"…and {max_assets - 3} more asset(s)")
        entry = f'<{html}|PR #{pr} – run {run}>{" – " + name if name else ""} (created {now})'
        if assets:
            entry += f"\nAssets: {' · '.join(assets)}"
        items.append(entry)
    return items


def build_payload(
    keep_per_pr: int,
    min_age_days: int,
    deleted_releases: list[str],
    repo: str,
    run_id: str,
) -> dict:
    max_list = 10
    listItems = deleted_releases or []
    payload_blocks = []
    payload_blocks.append(
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "Draft Release Cleanup Summary"},
        }
    )
    payload_blocks.append(
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Retention:* keep {keep_per_pr} per PR · delete drafts older than {min_age_days} days",
            },
        }
    )
    payload_blocks.append(
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "This cleanup keeps the repository tidy and prevents clutter from automated PR runs. See <https://github.com/73junito/Combination-Automotive-Diesel-Mechanics-Facility/blob/chore/types-mypy-py311/Combination_Automotive_Diesel_Facility_Project/Python_Workflow/README.md|Cleanup docs> for details.",
            },
        }
    )

    # Summary
    deleted_count = len(listItems)
    payload_blocks.append(
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Summary:* {deleted_count} draft release{'' if deleted_count==1 else 's'} deleted",
            },
        }
    )

    # Per-release sections with dividers
    for idx, item in enumerate(listItems):
        payload_blocks.append(
            {"type": "section", "text": {"type": "mrkdwn", "text": item}}
        )
        if idx != len(listItems) - 1:
            payload_blocks.append({"type": "divider"})

    payload_blocks.append(
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Repository: {repo} • Workflow: cleanup-draft-releases • Run: {run_id}",
                }
            ],
        }
    )

    return {"blocks": payload_blocks}

    # (new Blocks returned above)


def post_webhook(url: str, payload: dict) -> None:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            print("Webhook responded with:", resp.status)
            body = resp.read().decode("utf-8", errors="replace")
            if body:
                print("Response body:", body)
    except urllib.error.HTTPError as e:
        print("HTTPError:", e.code, e.reason)
    except Exception as e:
        print("Request failed:", str(e))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--webhook", help="Slack webhook URL to POST payload to")
    p.add_argument("--threshold", type=int, default=3, help="Notify threshold")
    p.add_argument(
        "--deleted",
        type=int,
        default=2,
        help="Number of deleted releases to synthesize",
    )
    p.add_argument(
        "--max-assets", type=int, default=3, help="Max assets per release (for sample)"
    )
    p.add_argument(
        "--output",
        default="docs/cleanup_test_payload.json",
        help="Write payload JSON to this path",
    )
    args = p.parse_args(argv)

    repo = "73junito/Combination-Automotive-Diesel-Mechanics-Facility"
    run_id = "TEST-LOCAL"
    deleted_items = make_sample_deleted_releases(args.deleted, args.max_assets)
    payload = build_payload(
        keep_per_pr=3,
        min_age_days=14,
        deleted_releases=deleted_items,
        repo=repo,
        run_id=run_id,
    )

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2))
    print(f"Wrote payload JSON to {out_path}")
    print("\n---- PAYLOAD START ----")
    print(json.dumps(payload, indent=2))
    print("---- PAYLOAD END ----\n")

    if args.webhook:
        print("Posting payload to webhook:", args.webhook)
        post_webhook(args.webhook, payload)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
