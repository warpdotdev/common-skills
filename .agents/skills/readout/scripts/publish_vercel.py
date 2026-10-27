#!/usr/bin/env python3
"""Publish one readout through a dedicated Vercel project.

The script intentionally requires --confirm-public because the HTML and any
embedded source snippets become visible to anyone on the internet.

Usage:
  python3 publish_vercel.py <doc.html> --scope account-or-team \
    --confirm-public --confirm-disable-protection
  python3 publish_vercel.py <doc.html> --scope account-or-team --dry-run
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional
from urllib.parse import quote


NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,99}$")
URL_RE = re.compile(r"https://[^\s]+")
MANAGED_MARKER = ".readout-managed.json"


class PublishError(RuntimeError):
    pass


def run(
    args: list[str],
    *,
    cwd: Optional[Path] = None,
    check: bool = True,
    input_text: Optional[str] = None,
) -> subprocess.CompletedProcess:
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, input=input_text)
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit code {result.returncode}"
        raise PublishError(f"{' '.join(args)} failed: {detail}")
    return result


def vercel_user() -> str:
    result = run(["vercel", "whoami", "--no-color"])
    user = result.stdout.strip()
    if not user:
        raise PublishError("Vercel CLI returned an empty username; run `vercel login`")
    return user


def project_name(user: str) -> str:
    slug = re.sub(r"[^a-z0-9-]+", "-", user.lower()).strip("-")
    if not slug:
        raise PublishError(f"could not derive a Vercel project name from username {user!r}")
    return f"readouts-{slug}"[:100].rstrip("-")


def parse_json(result: subprocess.CompletedProcess, action: str) -> dict:
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise PublishError(f"Vercel returned invalid JSON while {action}") from exc


def is_not_found(result: subprocess.CompletedProcess) -> bool:
    detail = f"{result.stderr}\n{result.stdout}"
    return "HTTP 404" in detail or "not found" in detail.lower()


def inspect_project(scope: str, project: str) -> Optional[dict]:
    result = run(
        ["vercel", "api", f"/v9/projects/{project}", "--scope", scope, "--raw", "--no-color"],
        check=False,
    )
    if result.returncode == 0:
        return parse_json(result, f"inspecting project {scope}/{project}")
    if is_not_found(result):
        return None
    detail = result.stderr.strip() or result.stdout.strip()
    raise PublishError(
        f"could not inspect Vercel project {scope}/{project}: {detail}. "
        "Check `vercel login`, the selected scope, permissions, and network access."
    )


def create_project(scope: str, project: str) -> dict:
    result = run(
        [
            "vercel", "api", "/v11/projects", "--scope", scope,
            "--method", "POST", "--input", "-", "--raw", "--no-color",
        ],
        input_text=json.dumps({"name": project, "ssoProtection": None}),
    )
    return parse_json(result, f"creating project {scope}/{project}")


def marker_matches(site: Path, scope: str, project: str, project_info: dict) -> bool:
    marker = site / MANAGED_MARKER
    if marker.is_file():
        try:
            data = json.loads(marker.read_text())
        except json.JSONDecodeError:
            return False
        return (
            data.get("scope") == scope
            and data.get("project") == project
            and data.get("project_id") == project_info.get("id")
        )

    linked = site / ".vercel" / "project.json"
    if linked.is_file():
        try:
            linked_data = json.loads(linked.read_text())
        except json.JSONDecodeError:
            return False
        return linked_data.get("projectId") == project_info.get("id")
    return False


def write_marker(site: Path, scope: str, project: str, project_info: dict) -> None:
    (site / MANAGED_MARKER).write_text(
        json.dumps(
            {
                "scope": scope,
                "project": project,
                "project_id": project_info.get("id"),
            },
            indent=2,
        )
        + "\n"
    )


def ensure_public_project(scope: str, project: str) -> None:
    run(
        [
            "vercel", "api", f"/v9/projects/{project}", "--scope", scope,
            "--method", "PATCH", "--input", "-", "--silent", "--no-color",
        ],
        input_text=json.dumps({"ssoProtection": None}),
    )


def prepare_site(doc: Path, scope: str, project: str, skill_dir: Path) -> Path:
    site = Path.home() / ".readouts" / ".publish" / "vercel" / scope / project
    site.mkdir(parents=True, exist_ok=True)
    (site / ".vercelignore").write_text(f"{MANAGED_MARKER}\n")
    shutil.copy2(doc, site / doc.name)
    run(["python3", str(skill_dir / "update_index.py"), str(site)])

    link = run([
        "vercel", "link", "--yes", "--team", scope, "--project", project,
        "--cwd", str(site), "--no-color",
    ])
    if not (site / ".vercel" / "project.json").is_file():
        detail = link.stderr.strip() or link.stdout.strip()
        raise PublishError(f"Vercel linked {scope}/{project} but did not create project metadata: {detail}")
    return site


def deploy(site: Path, scope: str) -> str:
    result = run([
        "vercel", "deploy", "--prod", "--yes", "--scope", scope,
        "--cwd", str(site), "--no-color",
    ])
    urls = URL_RE.findall(result.stdout)
    if not urls:
        detail = result.stderr.strip() or result.stdout.strip()
        raise PublishError(f"Vercel deployment succeeded but returned no deployment URL: {detail}")
    return urls[-1].rstrip("/")


def public_alias(deployment_url: str, scope: str, project: str) -> str:
    result = run([
        "vercel", "inspect", deployment_url, "--scope", scope,
        "--format=json", "--no-color",
    ])
    try:
        aliases = json.loads(result.stdout).get("aliases") or []
    except json.JSONDecodeError as exc:
        raise PublishError("Vercel returned invalid JSON while resolving the public alias") from exc
    preferred = f"{project}.vercel.app"
    if preferred in aliases:
        return f"https://{preferred}"
    if aliases:
        return f"https://{min(aliases, key=len)}"
    raise PublishError(f"Vercel deployment {deployment_url} has no production alias")


def verify_public_url(public_url: str, doc: Path, skill_dir: Path) -> dict:
    result = run([
        "python3", str(skill_dir / "verify_public_url.py"), public_url,
        "--expected-file", str(doc), "--json",
    ])
    return parse_json(result, f"verifying public URL {public_url}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("doc", type=Path, help="self-contained readout HTML file")
    parser.add_argument("--scope", required=True, help="Vercel account/team slug from list_vercel_scopes.py")
    parser.add_argument("--project", help="Vercel project (default: readouts-<vercel-user>)")
    parser.add_argument(
        "--confirm-public",
        action="store_true",
        help="confirm that the document and embedded source may be publicly accessible",
    )
    parser.add_argument(
        "--confirm-disable-protection",
        action="store_true",
        help="confirm that Vercel Authentication may be disabled for the dedicated project",
    )
    parser.add_argument(
        "--allow-existing-project",
        action="store_true",
        help="adopt an existing unmarked project after separately confirming it is dedicated to readouts",
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable deployment details")
    parser.add_argument("--dry-run", action="store_true", help="validate inputs and print the intended deployment")
    args = parser.parse_args()

    doc = args.doc.expanduser().resolve()
    if not doc.is_file() or doc.suffix.lower() != ".html":
        raise PublishError(f"expected an existing .html file, got {doc}")
    if not NAME_RE.fullmatch(args.scope):
        raise PublishError(f"invalid Vercel scope slug: {args.scope}")
    if not args.dry_run and not args.confirm_public:
        raise PublishError(
            "refusing public deployment without --confirm-public; "
            "the HTML and any embedded source snippets will be visible to anyone"
        )
    if not args.dry_run and not args.confirm_disable_protection:
        raise PublishError(
            "refusing to change project visibility without --confirm-disable-protection; "
            "all current and future deployments in the dedicated project will be public"
        )
    if not args.dry_run and shutil.which("vercel") is None:
        raise PublishError("required executable not found: vercel")

    project = args.project
    if project is None:
        project = "readouts-<vercel-user>" if args.dry_run else project_name(vercel_user())
    if project != "readouts-<vercel-user>" and not NAME_RE.fullmatch(project):
        raise PublishError(f"invalid Vercel project name: {project}")

    if args.dry_run:
        print(f"Would publicly deploy {doc} to Vercel scope {args.scope}, project {project}.")
        print(f"The returned URL will use the public production alias and end with /{quote(doc.name)}.")
        return 0


    skill_dir = Path(__file__).resolve().parent
    site = Path.home() / ".readouts" / ".publish" / "vercel" / args.scope / project
    site.mkdir(parents=True, exist_ok=True)
    project_info = inspect_project(args.scope, project)
    created = project_info is None
    if created:
        project_info = create_project(args.scope, project)
        write_marker(site, args.scope, project, project_info)
    elif marker_matches(site, args.scope, project, project_info):
        write_marker(site, args.scope, project, project_info)
    elif args.allow_existing_project:
        write_marker(site, args.scope, project, project_info)
    else:
        raise PublishError(
            f"refusing to modify existing unmarked project {args.scope}/{project}; "
            "use the default dedicated project, or pass --allow-existing-project only "
            "after confirming the project contains no unrelated deployments"
        )

    ensure_public_project(args.scope, project)
    site = prepare_site(doc, args.scope, project, skill_dir)
    deployment_url = deploy(site, args.scope)
    alias_url = public_alias(deployment_url, args.scope, project)
    public_url = f"{alias_url}/{quote(doc.name)}"
    verification = verify_public_url(public_url, doc, skill_dir)
    output = {
        "document": str(doc),
        "scope": args.scope,
        "project": project,
        "project_created": created,
        "public_url": public_url,
        "public_index": f"{alias_url}/",
        "verification": verification,
    }
    if args.json:
        print(json.dumps(output, indent=2))
    else:
        print(f"Published {doc}")
        print(f"Public URL: {public_url}")
        print(f"Public index: {alias_url}/")
        print(f"Anonymous verification: HTTP {verification['status']}, title matched")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except PublishError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
