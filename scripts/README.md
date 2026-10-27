# Common skills scripts
These scripts help consuming repositories install, remove, and verify shared agent skills from `warpdotdev/common-skills`.
## Files
- `resolve_common_skills`: resolves and executes scripts from this directory, a local override directory, or raw GitHub.
- `install_common_skills`: installs or updates skills from a lockfile, then verifies the installed contents. Parametrized by `--source`/`--lock-file`/`--label` so it can drive any skill set.
- `install_warp_skills`: thin best-effort wrapper over `install_common_skills` for the internal `warpdotdev/warp-skills` set (`warp-skills-lock.json`).
- `update_common_skills_lock`: regenerates an existing skills lockfile without installing skills; accepts `--source`/`--lock-file` to target any skills source (e.g. `warp-skills-lock.json` from `warpdotdev/warp-skills`).
- `remove_common_skills`: removes installed skills listed in a lockfile from a selected target (`--lock-file`/`--label`).
- `remove_warp_skills`: thin wrapper over `remove_common_skills` for the warp-skills set.
## Quick start
Install common skills into the current checkout:
```sh
scripts/install_common_skills --project
```
Install common skills globally:
```sh
scripts/install_common_skills --global
```
Install only when the lock hash has changed or a locked skill is missing:
```sh
scripts/install_common_skills --project --if-needed --non-interactive
```
Verify the installed skills without installing:
```sh
scripts/install_common_skills --verify-only
```
Remove installed common skills:
```sh
scripts/remove_common_skills --project
```
## Invoking from client repositories
Client repositories do not need to vendor these scripts. They should keep a small `script/resolve_common_skills` shim that loads this repository's `scripts/resolve_common_skills` and forwards arguments to it.
For example, a client repo's `script/resolve_common_skills` shim can look like this:
```sh
#!/usr/bin/env bash

set -eo pipefail

COMMON_SKILLS_REPO="warpdotdev/common-skills"
COMMON_SKILLS_REF="${WARP_COMMON_SKILLS_REF:-main}"
RAW_BASE_URL="${WARP_COMMON_SKILLS_RAW_BASE_URL:-https://raw.githubusercontent.com/${COMMON_SKILLS_REPO}/${COMMON_SKILLS_REF}/scripts}"

if [[ -n "${WARP_COMMON_SKILLS_SCRIPTS_DIR:-}" ]]; then
  exec "${WARP_COMMON_SKILLS_SCRIPTS_DIR%/}/resolve_common_skills" "$@"
fi

curl -fsSL "${RAW_BASE_URL%/}/resolve_common_skills" | bash -s -- "$@"
```
The shim's default path executes this repository's shared resolver through `curl`:
```sh
curl -fsSL "https://raw.githubusercontent.com/warpdotdev/common-skills/${WARP_COMMON_SKILLS_REF:-main}/scripts/resolve_common_skills" | bash -s -- install_common_skills -- --repo-root "${REPO_ROOT}" --if-needed --prompt-for-target
```
Consumer bootstrap and run scripts call the shim instead of calling `curl` directly:
```sh
./script/resolve_common_skills install_common_skills -- --repo-root "${REPO_ROOT}" --if-needed --prompt-for-target
```
With an explicit target, client repos pass the same installer flags they would pass locally:
```sh
./script/resolve_common_skills install_common_skills -- --repo-root "${REPO_ROOT}" --global --if-needed
./script/resolve_common_skills install_common_skills -- --repo-root "${REPO_ROOT}" --project --force
```
The resolver supports these development overrides:
- `WARP_COMMON_SKILLS_REF=<git-ref>`: fetch scripts from a branch, tag, or commit in `warpdotdev/common-skills`; also forwarded to the installer so missing-lock creation and interactive lock update checks use the same ref.
- `WARP_COMMON_SKILLS_SCRIPTS_DIR=/path/to/common-skills/scripts`: execute scripts from a local checkout or worktree instead of fetching from GitHub.
- `WARP_COMMON_SKILLS_RAW_BASE_URL=https://...`: override the raw URL base used by the resolver.
## Developing against these scripts from a client repo
For normal client-repo development, test the remote path first:
```sh
WARP_COMMON_SKILLS_REF=<your-common-skills-branch> ./script/bootstrap --install-common-skills-globally
WARP_COMMON_SKILLS_REF=<your-common-skills-branch> ./script/run --install-common-skills
```
Use `WARP_COMMON_SKILLS_SCRIPTS_DIR` when iterating on unpushed local script changes:
```sh
WARP_COMMON_SKILLS_SCRIPTS_DIR=/path/to/common-skills/scripts ./script/run --install-common-skills
```
Client repos should keep their own `skills-lock.json` checked in. Normal install flows use that lock as the source of truth; interactive flows may ask to update it when this repo would produce a different lock. Review and commit lock changes in the client repo separately from changes to this repo.
## Install script
`install_common_skills` installs common agent skills from `warpdotdev/common-skills`.
When `skills-lock.json` is missing, the script creates it by running the `skills` CLI against the source repo and selecting all valid skills. This is intentionally dynamic: the script should not hardcode a fixed list of common skill names. Set `WARP_COMMON_SKILLS_REF=<git-ref>` to create the lock from a branch, tag, or commit such as `warpdotdev/common-skills#my-branch`.
When `skills-lock.json` already exists and the script is running interactively, it checks whether `warpdotdev/common-skills` would produce an updated lock before prompting for a project/global install target. If `WARP_COMMON_SKILLS_REF` is set, the check uses that branch, tag, or commit as the candidate source. If a different lock is available, it asks before updating `skills-lock.json` and reinstalling from the updated lock. Non-interactive and verify-only runs skip this upstream update prompt and use the existing lock.
When `skills-lock.json` already exists, the script installs from the lock file:
- Project target: `npx --yes skills@1.5.6 experimental_install`
- Global target: `npx --yes skills@1.5.6 add warpdotdev/common-skills --global --agent warp --skill <locked skills> --yes --copy`
The script supports:
- `--repo-root <path>`: repository containing `skills-lock.json`.
- `--project`: install into `.agents/skills`.
- `--global`: install into `~/.agents/skills`.
- `--if-needed`: skip when the stamp matches the lock and locked skills are present.
- `--prompt-for-target`: prompt for project/global when no explicit target is set.
- `--non-interactive`: do not prompt; fail when no target is explicit.
- `--force`: install even if already up to date.
- `--quiet`: suppress no-op output.
- `--verify-only`: verify installed skills match `skills-lock.json` without installing.
- `--source <owner/repo>`: skills source repository (default: `warpdotdev/common-skills`).
- `--lock-file <name>`: lockfile name within the repo (default: `skills-lock.json`).
- `--label <name>`: label used for the stamp file and messages (default: `common`).
- `--best-effort`: on any failure or a missing lockfile, print a short notice and exit 0 (used for the optional internal warp-skills set).
Successful install and skip paths verify that exactly one install target contains the locked common skills and that each installed skill matches `skills-lock.json`.
Project installs add local Git exclude entries for only the locked common-skill directories so unrelated project skills in `.agents/skills` remain visible to Git.
Global installs are shared across client repositories. A second repo pinned to the same lock verifies and succeeds without unnecessarily reinstalling; a repo pinned to a different lock fails with a version-mismatch error instead of overwriting the shared global install.
## Internal warp-skills
`install_warp_skills` and `remove_warp_skills` are thin wrappers that run `install_common_skills`/`remove_common_skills` against the internal `warpdotdev/warp-skills` set pinned in the consumer's `warp-skills-lock.json`. The install wrapper passes `--source warpdotdev/warp-skills --lock-file warp-skills-lock.json --label warp --best-effort` and installs into the same target as common skills (project unless `WARP_COMMON_SKILLS_INSTALL_TARGET=global`).
This step is optional and never required for external contributors: it is best-effort, so a missing `warp-skills-lock.json` or no access to `warpdotdev/warp-skills` results in a short notice and exit 0 without failing the caller. Skip it with `--skip-warp-skills` or `WARP_SKIP_WARP_SKILLS_INSTALL=1`.
Consumers invoke it through the same resolver as common skills:
```sh
./script/resolve_common_skills install_warp_skills -- --repo-root "${REPO_ROOT}" --if-needed
```
warp-skills must not reuse common-skill names. The project-vs-global exclusivity check applies to every set: if a locked skill is found in both `.agents/skills` and `~/.agents/skills`, the install fails instead of silently placing the same name in two locations. Since warp-skills and common skills use distinct names, this check also surfaces any accidental naming collision between the two sets.
## Update lock script
`update_common_skills_lock` non-interactively regenerates an existing skills lockfile from the default branch of a skills source repo without installing skills into the target repository. By default it regenerates `skills-lock.json` from `warpdotdev/common-skills`; pass `--source <owner/repo>` and `--lock-file <name>` to regenerate another lock (e.g. `--source warpdotdev/warp-skills --lock-file warp-skills-lock.json`).
It generates a candidate in a temporary Git repository, then copies back only a changed `skills-lock.json`. Generator failures and missing candidate output fail the command instead of retaining the existing lock.
Run it from a consuming repository:
```sh
/path/to/common-skills/scripts/update_common_skills_lock --repo-root /path/to/consumer
# or, for the warp-skills lock:
/path/to/common-skills/scripts/update_common_skills_lock --repo-root /path/to/consumer --source warpdotdev/warp-skills --lock-file warp-skills-lock.json
```
The downstream lockfile update workflow uses this command before opening lockfile-only pull requests.
## Downstream lockfile workflow
`.github/workflows/update-downstream-skill-locks.yml` runs after every push to `main`. A single parametrized matrixed job refreshes both `skills-lock.json` (from `warpdotdev/common-skills`) and `warp-skills-lock.json` (from `warpdotdev/warp-skills`) in `warpdotdev/warp` and `warpdotdev/warp-server`, opening a lockfile-only pull request for each lock that changes.
Each pull request requests the author of the originating common-skills pull request when possible and enables squash auto-merge. Direct pushes and authors who cannot review a target repository do not prevent pull request creation.
The workflow requires a dedicated GitHub App installed on both downstream repositories with contents and pull-request write access. Configure its App ID as the `COMMON_SKILLS_SYNC_APP_ID` Actions variable and its private key as the `COMMON_SKILLS_SYNC_APP_PRIVATE_KEY` Actions secret in `common-skills`.
## Remove script
`remove_common_skills` removes common agent skills listed in `skills-lock.json`.
The script supports:
- `--repo-root <path>`: repository containing `skills-lock.json`.
- `--project`: remove from `.agents/skills`.
- `--global`: remove from `~/.agents/skills`.
- `--clear-lock`: remove `skills-lock.json` after removing locked skills.
The remove script only deletes paths derived from the lock file and includes path checks before removing project skill directories.
## Verification
`install_common_skills --verify-only` checks that exactly one install target contains the locked common skills and that each installed skill matches `skills-lock.json`.
Verification also runs after successful install and skip paths.
Verification fails if:
- `skills-lock.json` is missing.
- Locked skills are installed in both project and global targets.
- Locked skills are missing from both targets.
- Any installed skill directory hash differs from the lock file.
## Environment variables
- `WARP_SKIP_COMMON_SKILLS_INSTALL=1`: skip installation.
- `WARP_COMMON_SKILLS_INSTALL_TARGET=project|global`: explicit install or removal target.
- `WARP_COMMON_SKILLS_TARGET_REPO_ROOT=/path/to/repo`: repository containing `skills-lock.json` and project-local `.agents/skills`.
- `WARP_COMMON_SKILLS_REF=<git-ref>`: use a specific `warpdotdev/common-skills` branch, tag, or commit when creating a missing lock or checking interactively for lock updates.
## Lock hash stamps
After a successful install, `install_common_skills` writes a stamp with the current lockfile hash. The stamp filename is derived from `--label` (default `common`) so different skill sets do not collide (for example, `warp` uses `warp-skills-lock.hash`).
- Project installs use git path `warp/<label>-skills-lock.hash`, or `.agents/skills/.<label>-skills-lock.hash` when git metadata is unavailable.
- Global installs use `~/.agents/warp/<label>-skills-lock.hash`.
The stamp lets `--if-needed` avoid reinstalling when the lock file and installed skills are already current.
