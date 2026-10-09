#!/usr/bin/env python3
"""List the authenticated Vercel user and deployable account/team scopes as JSON."""

import json
import shutil
import subprocess
import sys


def run(args: list[str]) -> str:
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit code {result.returncode}"
        raise RuntimeError(f"{' '.join(args)} failed: {detail}")
    return result.stdout


def main() -> int:
    if shutil.which("vercel") is None:
        raise RuntimeError("required executable not found: vercel")
    user = run(["vercel", "whoami", "--no-color"]).strip()
    if not user:
        raise RuntimeError("Vercel CLI returned an empty username; run `vercel login`")
    teams_by_slug = {}
    cursor = None
    while True:
        command = ["vercel", "teams", "ls", "--format=json", "--no-color"]
        if cursor is not None:
            command.extend(["--next", str(cursor)])
        try:
            team_data = json.loads(run(command))
        except json.JSONDecodeError as exc:
            raise RuntimeError("Vercel returned invalid JSON while listing scopes") from exc
        for team in team_data.get("teams", []):
            if team.get("slug"):
                teams_by_slug[team["slug"]] = {
                    "slug": team["slug"],
                    "name": team.get("name") or team["slug"],
                    "current": bool(team.get("current")),
                }
        cursor = (team_data.get("pagination") or {}).get("next")
        if cursor is None:
            break
    teams = list(teams_by_slug.values())
    if not teams:
        raise RuntimeError("Vercel returned no deployable account/team scopes")
    print(json.dumps({"authenticated_user": user, "scopes": teams}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
