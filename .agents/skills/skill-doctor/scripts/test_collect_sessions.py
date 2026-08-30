#!/usr/bin/env python3
"""Tests for skill-doctor session collection."""

import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from collect_sessions import (
    detect_skills_from_entries,
    discover_skills,
    find_claude_session_files,
    find_pi_session_files,
    parse_claude_session,
    parse_pi_session,
    session_matches_repos,
)


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n")


class ClaudeSessionTests(unittest.TestCase):
    def test_discovers_skills_and_matches_sessions_across_projects(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / "first"
            second = root / "second"
            first_skill = first / ".agents" / "skills" / "alpha" / "SKILL.md"
            second_skill = second / ".claude" / "skills" / "beta" / "SKILL.md"
            first_skill.parent.mkdir(parents=True)
            second_skill.parent.mkdir(parents=True)
            first_skill.write_text("---\ndescription: Alpha\n---\n")
            second_skill.write_text("---\ndescription: Beta\n---\n")

            skills = discover_skills(
                [first, second],
                root / "codex-home",
                [],
                False,
            )

            self.assertEqual(set(skills), {"alpha", "beta"})
            self.assertTrue(
                session_matches_repos(second / "src", [first, second])
            )
            self.assertFalse(
                session_matches_repos(root / "elsewhere", [first, second])
            )

    def test_detects_skills_from_deferred_tool_entries(self):
        entries = [
            ("tool:Skill", '{"skill": "alpha"}'),
            ("tool:read", '{"path": "/repo/.agents/skills/beta/SKILL.md"}'),
            ("assistant", "Mentioning gamma here does not count."),
        ]

        self.assertEqual(
            detect_skills_from_entries(entries, {"alpha", "beta", "gamma"}),
            {"alpha", "beta"},
        )

    def test_discovers_parent_sessions_and_optional_subagents(self):
        with tempfile.TemporaryDirectory() as tmp:
            claude_home = Path(tmp)
            parent = claude_home / "projects" / "-repo" / "parent.jsonl"
            subagent = (
                claude_home
                / "projects"
                / "-repo"
                / "parent"
                / "subagents"
                / "agent-child.jsonl"
            )
            old = claude_home / "projects" / "-repo" / "old.jsonl"
            for path in (parent, subagent, old):
                write_jsonl(path, [{"type": "user"}])
            old_time = (datetime.now(timezone.utc) - timedelta(days=10)).timestamp()
            os.utime(old, (old_time, old_time))
            cutoff = datetime.now(timezone.utc) - timedelta(days=1)

            parents = find_claude_session_files(claude_home, cutoff, False)
            with_subagents = find_claude_session_files(claude_home, cutoff, True)

            self.assertEqual([path for _, path in parents], [parent])
            self.assertEqual(
                {path for _, path in with_subagents},
                {parent, subagent},
            )

    def test_parses_messages_tools_skills_and_stats(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.jsonl"
            common = {
                "sessionId": "session-1",
                "cwd": "/tmp/repo",
                "timestamp": "2026-08-20T10:00:00Z",
                "version": "1.0.0",
            }
            write_jsonl(path, [
                {
                    **common,
                    "type": "user",
                    "uuid": "user-1",
                    "message": {"role": "user", "content": "Improve my skill"},
                },
                {
                    **common,
                    "type": "assistant",
                    "uuid": "assistant-1",
                    "message": {
                        "id": "message-1",
                        "role": "assistant",
                        "content": [
                            {"type": "text", "text": "I will inspect it."},
                            {
                                "type": "tool_use",
                                "name": "Skill",
                                "input": {"skill": "update-skill"},
                            },
                        ],
                    },
                },
                {
                    **common,
                    "type": "assistant",
                    "uuid": "assistant-2",
                    "message": {
                        "id": "message-1",
                        "role": "assistant",
                        "content": [
                            {
                                "type": "tool_use",
                                "name": "Edit",
                                "input": {"file_path": "/tmp/repo/SKILL.md"},
                            }
                        ],
                    },
                },
                {
                    **common,
                    "type": "user",
                    "uuid": "result-1",
                    "message": {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "is_error": True,
                                "content": "permission denied",
                            }
                        ],
                    },
                },
            ])

            meta, stats, entries, skills = parse_claude_session(
                path,
                {"update-skill"},
                False,
            )

            self.assertEqual(meta["id"], "session-1")
            self.assertEqual(meta["cwd"], "/tmp/repo")
            self.assertEqual(stats["user_turns"], 1)
            self.assertEqual(stats["assistant_turns"], 1)
            self.assertEqual(stats["tool_calls"], 2)
            self.assertEqual(stats["error_outputs"], 1)
            self.assertTrue(stats["has_code_edits"])
            self.assertEqual(skills, ["update-skill"])
            self.assertIn(("user", "Improve my skill"), entries)
            self.assertIn(("assistant", "I will inspect it."), entries)

    def test_excludes_sidechains_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "agent-child.jsonl"
            write_jsonl(path, [{
                "type": "user",
                "sessionId": "session-1",
                "agentId": "child-1",
                "isSidechain": True,
                "cwd": "/tmp/repo",
                "timestamp": "2026-08-20T10:00:00Z",
                "message": {"role": "user", "content": "Investigate"},
            }])

            self.assertIsNone(parse_claude_session(path, set(), False))
            parsed = parse_claude_session(path, set(), True)
            self.assertEqual(parsed[0]["id"], "session-1-child-1")
            self.assertEqual(parsed[0]["thread_source"], "subagent")


class PiSessionTests(unittest.TestCase):
    def test_finds_session_files_within_window(self):
        with tempfile.TemporaryDirectory() as tmp:
            pi_home = Path(tmp)
            recent = pi_home / "agent" / "sessions" / "--repo--" / "20260820_new.jsonl"
            old = pi_home / "agent" / "sessions" / "--repo--" / "20260101_old.jsonl"
            for path in (recent, old):
                write_jsonl(path, [{"type": "session", "id": "s", "cwd": "/tmp/repo"}])
            old_time = (datetime.now(timezone.utc) - timedelta(days=10)).timestamp()
            os.utime(old, (old_time, old_time))
            cutoff = datetime.now(timezone.utc) - timedelta(days=1)

            found = find_pi_session_files(pi_home, cutoff)

            self.assertEqual([path for _, path in found], [recent])

    def test_missing_sessions_directory_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            found = find_pi_session_files(Path(tmp), datetime.now(timezone.utc))
            self.assertEqual(found, [])

    def test_parses_messages_tool_calls_skills_and_stats(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.jsonl"
            write_jsonl(path, [
                {
                    "type": "session",
                    "version": 3,
                    "id": "session-1",
                    "timestamp": "2026-08-20T10:00:00.000Z",
                    "cwd": "/tmp/repo",
                },
                {
                    "type": "message",
                    "id": "a1",
                    "parentId": None,
                    "timestamp": "2026-08-20T10:00:01.000Z",
                    "message": {"role": "user", "content": "Improve my skill"},
                },
                {
                    "type": "message",
                    "id": "a2",
                    "parentId": "a1",
                    "timestamp": "2026-08-20T10:00:02.000Z",
                    "message": {
                        "role": "assistant",
                        "content": [
                            {"type": "text", "text": "I will inspect it."},
                            {
                                "type": "toolCall",
                                "id": "call_1",
                                "name": "edit",
                                "arguments": {"path": "/tmp/repo/.agents/skills/update-skill/SKILL.md"},
                            },
                        ],
                        "provider": "anthropic",
                        "model": "claude-sonnet-4-5",
                        "usage": {},
                        "stopReason": "toolUse",
                    },
                },
                {
                    "type": "message",
                    "id": "a3",
                    "parentId": "a2",
                    "timestamp": "2026-08-20T10:00:03.000Z",
                    "message": {
                        "role": "toolResult",
                        "toolCallId": "call_1",
                        "toolName": "edit",
                        "content": [{"type": "text", "text": "permission denied"}],
                        "isError": True,
                    },
                },
            ])

            meta, stats, entries, skills = parse_pi_session(path, {"update-skill"}, False)

            self.assertEqual(meta["id"], "session-1")
            self.assertEqual(meta["cwd"], "/tmp/repo")
            self.assertEqual(stats["user_turns"], 1)
            self.assertEqual(stats["assistant_turns"], 1)
            self.assertEqual(stats["tool_calls"], 1)
            self.assertEqual(stats["error_outputs"], 1)
            self.assertTrue(stats["has_code_edits"])
            self.assertEqual(skills, ["update-skill"])
            self.assertIn(("user", "Improve my skill"), entries)
            self.assertIn(("assistant", "I will inspect it."), entries)

    def test_bash_execution_counts_as_tool_call_and_detects_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.jsonl"
            write_jsonl(path, [
                {
                    "type": "session",
                    "id": "session-2",
                    "timestamp": "2026-08-20T10:00:00.000Z",
                    "cwd": "/tmp/repo",
                },
                {
                    "type": "message",
                    "id": "b1",
                    "parentId": None,
                    "timestamp": "2026-08-20T10:00:01.000Z",
                    "message": {"role": "user", "content": "Run the tests"},
                },
                {
                    "type": "message",
                    "id": "b2",
                    "parentId": "b1",
                    "timestamp": "2026-08-20T10:00:02.000Z",
                    "message": {
                        "role": "bashExecution",
                        "command": "pytest",
                        "output": "FAILED test_x",
                        "exitCode": 1,
                        "cancelled": False,
                        "truncated": False,
                    },
                },
                {
                    "type": "message",
                    "id": "b3",
                    "parentId": "b2",
                    "timestamp": "2026-08-20T10:00:03.000Z",
                    "message": {
                        "role": "assistant",
                        "content": [{"type": "text", "text": "Let me fix that."}],
                        "provider": "anthropic",
                        "model": "claude-sonnet-4-5",
                        "usage": {},
                        "stopReason": "stop",
                    },
                },
            ])

            meta, stats, entries, skills = parse_pi_session(path, set(), False)

            self.assertEqual(stats["tool_calls"], 1)
            self.assertEqual(stats["assistant_turns"], 1)
            self.assertEqual(stats["error_outputs"], 1)
            self.assertIn(("tool:bash", "pytest"), entries)


if __name__ == "__main__":
    unittest.main()
