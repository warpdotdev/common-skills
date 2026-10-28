"""Antigravity collector regression tests using synthetic local exports."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from collect_sessions import (
    TRANSCRIPT_HEAD, TRANSCRIPT_TAIL, decode_antigravity_args, discover_skills,
    find_antigravity_session_files, parse_antigravity_session,
)

SCRIPT = Path(__file__).with_name("collect_sessions.py")


def write_export(home, channel, sid, records):
    path = home / channel / "brain" / sid / ".system_generated/logs/transcript.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n")
    return path


def call(name, **args):
    return {"type": "PLANNER_RESPONSE", "created_at": "2026-10-27T12:00:01Z",
            "tool_calls": [{"name": name, "args": {k: json.dumps(v) for k, v in args.items()}}]}


def smoke_records(project):
    return [
        {"type": "USER_INPUT", "created_at": "2026-10-27T12:00:00Z",
         "content": "<USER_REQUEST>Read the fixture.</USER_REQUEST><ADDITIONAL_METADATA>ignore</ADDITIONAL_METADATA>"},
        call("read_file", Path=str(project / ".agents/skills/probe/SKILL.md")),
        call("write_file", Path=str(project / "result.txt"), Content="42"),
        {"type": "GENERIC", "status": "DONE", "content": "Created file."},
        {"type": "PLANNER_RESPONSE", "content": "Verified 42."},
    ]


class AntigravitySessionTests(unittest.TestCase):
    def test_decodes_json_arguments_without_losing_plain_values(self):
        self.assertEqual(decode_antigravity_args({"Path": '"/work/a b.py"', "Overwrite": "true",
                                                "Line": "3", "Text": "not json"}),
                         {"Path": "/work/a b.py", "Overwrite": True, "Line": 3, "Text": "not json"})
        self.assertEqual(decode_antigravity_args('{"Cwd": "\\\"/work\\\""}'), {"Cwd": "/work"})
        self.assertEqual(decode_antigravity_args("unstructured"), "unstructured")

    def test_current_file_tools_and_user_envelope(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            project = home / "project-with spaces"
            path = write_export(home, "antigravity-cli", "cli", smoke_records(project))
            meta, stats, entries, skills = parse_antigravity_session(path, ["probe"])
            self.assertEqual(meta["cwd"], str(project))
            self.assertEqual(meta["channel"], "antigravity-cli")
            self.assertEqual(stats["user_turns"], 1)
            self.assertTrue(stats["has_code_edits"])
            self.assertEqual(stats["tool_calls"], 2)
            self.assertEqual(skills, ["probe"])
            self.assertIn(("user", "Read the fixture."), entries)
            self.assertNotIn("ADDITIONAL_METADATA", str(entries))

    def test_legacy_paths_results_and_nonzero_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            records = [call("view_file", AbsolutePath=str(project / "src/file.py")),
                       call("run_command", Cwd=str(project), CommandLine="false"),
                       call("replace_file_content", TargetFile=str(project / "src/file.py")),
                       {"type": "RUN_COMMAND", "status": "DONE", "content": "Command exited with code 128."},
                       {"type": "VIEW_FILE", "content": "legacy result"},
                       {"type": "GENERIC", "content": "Command exited with code 0."}]
            path = write_export(Path(tmp), "antigravity", "old", records)
            meta, stats, entries, _ = parse_antigravity_session(path, [])
            self.assertEqual(meta["cwd"], str(project))
            self.assertTrue(stats["has_code_edits"])
            self.assertEqual(stats["error_outputs"], 1)
            self.assertIn(("output", "legacy result"), entries)

    def test_skill_mentions_are_not_usage_and_exact_calls_are_repeated(self):
        with tempfile.TemporaryDirectory() as tmp:
            records = [{"type": "USER_INPUT", "content": "Please use /probe and @probe."},
                       {"type": "SYSTEM_MESSAGE", "content": "<skills>probe</skills>"},
                       {"type": "USER_INPUT", "content": "<skills>probe</skills>"},
                       call("run_command", CommandLine="echo one"),
                       call("run_command", CommandLine="echo two"),
                       call("run_command", CommandLine="echo one")]
            path = write_export(Path(tmp), "antigravity", "repeat", records)
            _, stats, _, skills = parse_antigravity_session(path, ["probe"])
            self.assertEqual(stats["user_turns"], 1)
            self.assertEqual(stats["repeated_tool_calls"], 1)
            self.assertEqual(skills, [])
            self.assertFalse(stats["has_code_edits"])

    def test_global_skill_read_does_not_change_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            records = [call("read_file", Path="/global/.agents/skills/probe/SKILL.md"),
                       call("read_file", Path="/work/project/fixture.txt")]
            path = write_export(Path(tmp), "antigravity-cli", "global-first", records)
            meta, _, _, skills = parse_antigravity_session(path, ["probe"])
            self.assertEqual(meta["cwd"], "/work/project")
            self.assertEqual(skills, ["probe"])

    def test_ordinary_project_named_skills_keeps_its_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_export(Path(tmp), "antigravity-cli", "skills-project", [
                call("read_file", Path="/work/skills/result.txt")])
            self.assertEqual(parse_antigravity_session(path, [])[0]["cwd"], "/work/skills")

    def test_workspace_context_decodes_file_uri_and_preserves_spaces(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_export(Path(tmp), "antigravity", "context", [
                {"type": "USER_INPUT", "content": "<user_information>\n[URI] -> [CorpusName]:\nfile:///work/my%20project\n</user_information>"},
                call("read_file", Path="/elsewhere/file.txt")])
            meta, stats, entries, _ = parse_antigravity_session(path, [])
            self.assertEqual(meta["cwd"], "/work/my project")
            self.assertEqual(stats["user_turns"], 0)
            self.assertNotIn("user_information", str(entries))

    def test_metadata_and_subagent_references(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            parent = write_export(home, "antigravity-insiders", "parent", smoke_records(home / "project"))
            child = write_export(home, "antigravity-insiders", "child", [call("read_file", Path="/other/file")])
            reference = parent.parents[1] / "subagents/child.json"
            reference.parent.mkdir()
            reference.write_text(json.dumps({"conversationId": "child", "workspaceUris": ["file:///work/parent%20project"]}))
            cutoff = datetime.now(timezone.utc) - timedelta(days=1)
            self.assertEqual([p for _, p in find_antigravity_session_files(home, cutoff)], [parent])
            self.assertEqual(len(find_antigravity_session_files(home, cutoff, True)), 2)
            self.assertIsNone(parse_antigravity_session(child, []))
            meta, _, _, _ = parse_antigravity_session(child, [], True)
            self.assertEqual(meta["thread_source"], "subagent")
            self.assertEqual(meta["cwd"], "/work/parent project")

    def test_malformed_workspace_uri_does_not_abort_collection(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            records = [{"type": "USER_INPUT", "content": "<user_information>\n[URI] -> [CorpusName]:\nfile://[malformed\n</user_information>"},
                       call("read_file", Path="/work/fallback/file.txt")]
            parent = write_export(home, "antigravity", "parent", records)
            child = write_export(home, "antigravity", "child", records)
            reference = parent.parents[1] / "subagents/child.json"
            reference.parent.mkdir()
            reference.write_text(json.dumps({"workspaceUris": ["file://[malformed"]}))
            self.assertEqual(parse_antigravity_session(parent, [])[0]["cwd"], "/work/fallback")
            self.assertEqual(parse_antigravity_session(child, [], True)[0]["cwd"], "/work/fallback")

    def test_nul_workspace_paths_are_ignored_before_project_matching(self):
        with tempfile.TemporaryDirectory() as tmp:
            records = [{"type": "USER_INPUT", "content": "<user_information>\n[URI] -> [CorpusName]:\nfile:///work/%00/project\n</user_information>"},
                       call("run_command", Cwd="/work/\0/project"),
                       call("read_file", Path="/work/\0/file"),
                       call("read_file", Path="/work/valid/file")]
            path = write_export(Path(tmp), "antigravity", "nul", records)
            meta, _, _, _ = parse_antigravity_session(path, [])
            self.assertEqual(meta["cwd"], "/work/valid")

    def test_cache_workspace_is_authoritative_and_malformed_cache_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            path = write_export(home, "antigravity-cli", "cached", [call("read_file", Path="/other/file")])
            cache = home / "antigravity-cli/cache/conversation_metadata.json"
            cache.parent.mkdir()
            cache.write_text(json.dumps({"conversations": {"cached": {"summary": {"WorkspaceURIs": ["file:///work/root"]}}}}))
            self.assertEqual(parse_antigravity_session(path, [])[0]["cwd"], "/work/root")
            cache.write_text("not json")
            self.assertEqual(parse_antigravity_session(path, [])[0]["cwd"], "/other")

    def test_discovery_channels_cutoff_and_channel_home_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            paths = [write_export(home, channel, channel, []) for channel in
                     ("antigravity", "antigravity-cli", "antigravity-ide", "antigravity-insiders")]
            old = paths.pop()
            os.utime(old, (1, 1))
            cutoff = datetime.now(timezone.utc) - timedelta(days=1)
            self.assertEqual({p for _, p in find_antigravity_session_files(home, cutoff)}, set(paths))
            self.assertEqual(len(find_antigravity_session_files(home / "antigravity-cli", cutoff)), 1)
            self.assertEqual(find_antigravity_session_files(home / "missing", cutoff), [])

    def test_streams_records_after_eight_mib_and_bounds_transcript(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_export(Path(tmp), "antigravity", "large", [])
            with path.open("w") as stream:
                filler = json.dumps({"type": "SYSTEM_MESSAGE", "content": "x" * 1024}) + "\n"
                while stream.tell() <= 8 * 1024 * 1024:
                    stream.write(filler)
                for i in range(200):
                    stream.write(json.dumps({"type": "PLANNER_RESPONSE", "content": str(i)}) + "\n")
                stream.write(json.dumps(call("read_file", Path="/work/.agents/skills/probe/SKILL.md")) + "\n")
                stream.write("invalid json\nnull\n[]\n")
            _, stats, entries, skills = parse_antigravity_session(path, ["probe"])
            self.assertEqual(stats["tool_calls"], 1)
            self.assertEqual(stats["assistant_turns"], 201)
            self.assertEqual(skills, ["probe"])
            self.assertEqual(len(entries), TRANSCRIPT_HEAD + TRANSCRIPT_TAIL + 1)

    def test_global_and_project_gemini_skills(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project, home = root / "project", root / "home"
            for base, name in [(project, "local"), (home, "global")]:
                p = base / ".gemini/config/skills" / name / "SKILL.md" if base == project else base / "config/skills" / name / "SKILL.md"
                p.parent.mkdir(parents=True)
                p.write_text("---\ndescription: fixture\n---\n")
            with patch("collect_sessions.Path.home", return_value=root / "unused"):
                local = discover_skills([project], root / "codex", [], False, antigravity_home=home)
                global_skills = discover_skills([], root / "codex", [], True, antigravity_home=home)
            self.assertEqual(set(local), {"local"})
            self.assertEqual(set(global_skills), {"global"})

    def test_cli_alias_project_filter_and_auto_all_discovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home, project = root / "gemini", root / "project"
            skill = project / ".agents/skills/probe/SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("---\ndescription: test\n---\n")
            write_export(home, "antigravity-cli", "cli", smoke_records(project))
            write_export(home, "antigravity", "app", smoke_records(root / "other"))
            env = dict(os.environ, HOME=str(root / "empty"), CODEX_HOME=str(root / "empty-codex"),
                       CLAUDE_CONFIG_DIR=str(root / "empty-claude"))
            for harness in ("antigravity", "agy", "auto", "all"):
                out = root / harness
                result = subprocess.run([sys.executable, str(SCRIPT), "--harness", harness,
                                         "--antigravity-home", str(home), "--repo", str(project),
                                         "--out", str(out)], env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                inventory = json.loads((out / "inventory.json").read_text())
                self.assertEqual(inventory["harness"], "antigravity")
                self.assertEqual(inventory["stats"]["sessions_in_scope"], 1)
                self.assertEqual(inventory["sessions"][0]["meta"]["id"], "cli")
                self.assertEqual(inventory["sessions"][0]["skills_used"], ["probe"])
                self.assertTrue(Path(inventory["sessions"][0]["transcript_path"]).exists())


if __name__ == "__main__":
    unittest.main()
