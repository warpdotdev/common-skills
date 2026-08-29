#!/usr/bin/env python3
"""Tests for skill-doctor session collection."""

import io
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from collect_sessions import (
    detect_skills_from_entries,
    discover_opencode_databases,
    discover_skills,
    find_claude_session_files,
    find_opencode_sessions,
    opencode_data_root,
    open_opencode_database,
    parse_claude_session,
    session_matches_repos,
)


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n")


def create_opencode_schema(connection):
    connection.executescript(
        """
        CREATE TABLE session (
            id TEXT PRIMARY KEY,
            parent_id TEXT,
            directory TEXT,
            summary_additions INTEGER,
            summary_deletions INTEGER,
            summary_files INTEGER,
            summary_diffs TEXT,
            time_created INTEGER,
            time_updated INTEGER
        );
        CREATE TABLE session_message (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            type TEXT NOT NULL,
            seq INTEGER NOT NULL,
            time_created INTEGER,
            time_updated INTEGER,
            data TEXT NOT NULL
        );
        CREATE TABLE message (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            time_created INTEGER,
            time_updated INTEGER,
            data TEXT NOT NULL
        );
        CREATE TABLE part (
            id TEXT PRIMARY KEY,
            message_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            time_created INTEGER,
            time_updated INTEGER,
            data TEXT NOT NULL
        );
        """
    )


def insert_opencode_session(connection, session_id, directory, now_ms, parent_id=None):
    connection.execute(
        "INSERT INTO session VALUES (?, ?, ?, 0, 0, 0, NULL, ?, ?)",
        (session_id, parent_id, str(directory), now_ms - 1000, now_ms),
    )


def insert_opencode_message(
    connection, message_id, session_id, message_type, seq, data, now_ms
):
    connection.execute(
        "INSERT INTO session_message VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            message_id,
            session_id,
            message_type,
            seq,
            now_ms,
            now_ms,
            data if isinstance(data, str) else json.dumps(data),
        ),
    )


def insert_opencode_v1_message(connection, message_id, session_id, role, now_ms):
    connection.execute(
        "INSERT INTO message VALUES (?, ?, ?, ?, ?)",
        (
            message_id,
            session_id,
            now_ms,
            now_ms,
            json.dumps({"role": role, "time": {"created": now_ms}}),
        ),
    )


def insert_opencode_v1_part(connection, part_id, message_id, session_id, data, now_ms):
    connection.execute(
        "INSERT INTO part VALUES (?, ?, ?, ?, ?, ?)",
        (
            part_id,
            message_id,
            session_id,
            now_ms,
            now_ms,
            data if isinstance(data, str) else json.dumps(data),
        ),
    )


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
        self.assertEqual(
            detect_skills_from_entries(
                [("tool:read", '{"name": "gamma"}')], {"gamma"}
            ),
            set(),
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


class OpenCodeSessionTests(unittest.TestCase):
    def test_discovers_default_channels_and_explicit_replacements_by_file_identity(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stable = root / "opencode.db"
            channel = root / "opencode-dev.db"
            replacement = root / "custom.db"
            for path in (stable, channel, replacement):
                path.touch()
            alias = root / "alias.db"
            alias.symlink_to(replacement)

            self.assertEqual(
                discover_opencode_databases(data_dir=root),
                [channel.resolve(), stable.resolve()],
            )
            self.assertEqual(
                discover_opencode_databases(
                    ["custom.db", str(alias), "custom.db"], root
                ),
                [replacement.resolve()],
            )
            rejected = []
            self.assertEqual(
                discover_opencode_databases(
                    [":memory:", "missing.db", str(root)], root, rejected
                ),
                [],
            )
            self.assertEqual(
                [Path(path).name for path, _ in rejected],
                [":memory:", "missing.db", root.name],
            )
            with patch.dict(os.environ, {"XDG_DATA_HOME": str(root)}, clear=False):
                self.assertEqual(opencode_data_root(), root / "opencode")

    def test_normalizes_v1_messages_parts_stats_skills_children_and_cutoff(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            database = root / "opencode.db"
            repo = root / "repo"
            repo.mkdir()
            now = datetime.now(timezone.utc)
            now_ms = int(now.timestamp() * 1000)
            connection = sqlite3.connect(database)
            create_opencode_schema(connection)
            insert_opencode_session(connection, "root", repo, now_ms)
            insert_opencode_session(connection, "child", repo, now_ms, "root")
            connection.execute(
                "UPDATE session SET summary_additions = 1 WHERE id = 'child'"
            )
            insert_opencode_v1_message(
                connection, "m-assistant", "root", "assistant", now_ms + 2000
            )
            insert_opencode_v1_message(
                connection, "m-user", "root", "user", now_ms + 1000
            )
            insert_opencode_v1_part(
                connection,
                "a-text",
                "m-assistant",
                "root",
                {"type": "text", "text": "Inspecting."},
                now_ms + 2000,
            )
            insert_opencode_v1_part(
                connection,
                "b-hidden",
                "m-assistant",
                "root",
                {"type": "text", "text": "ignored", "ignored": True},
                now_ms + 2000,
            )
            insert_opencode_v1_part(
                connection,
                "c-skill",
                "m-assistant",
                "root",
                {
                    "type": "tool",
                    "tool": "skill",
                    "state": {
                        "status": "completed",
                        "input": {"name": "skill-doctor"},
                        "output": "loaded",
                        "metadata": {"name": "skill-doctor"},
                    },
                },
                now_ms + 3000,
            )
            insert_opencode_v1_part(
                connection,
                "d-skill-error",
                "m-assistant",
                "root",
                {
                    "type": "tool",
                    "tool": "skill",
                    "state": {
                        "status": "error",
                        "input": {"name": "skill-doctor"},
                        "error": "failed",
                    },
                },
                now_ms + 3000,
            )
            insert_opencode_v1_part(
                connection,
                "e-edit",
                "m-assistant",
                "root",
                {
                    "type": "tool",
                    "tool": "edit",
                    "state": {
                        "status": "completed",
                        "input": {"filePath": "collector.py"},
                        "output": "updated",
                    },
                },
                now_ms + 4000,
            )
            insert_opencode_v1_part(
                connection,
                "f-pending",
                "m-assistant",
                "root",
                {
                    "type": "tool",
                    "tool": "read",
                    "state": {"status": "pending", "input": {}},
                },
                now_ms + 4000,
            )
            insert_opencode_v1_part(
                connection,
                "g-reasoning",
                "m-assistant",
                "root",
                {"type": "reasoning", "text": "hidden"},
                now_ms + 4000,
            )
            insert_opencode_v1_part(
                connection,
                "u-text",
                "m-user",
                "root",
                {"type": "text", "text": "Fix the collector"},
                now_ms + 1000,
            )
            for index in range(12):
                insert_opencode_v1_part(
                    connection,
                    f"z-unknown-{index:02}",
                    "m-assistant",
                    "root",
                    {"type": "future"},
                    now_ms + 2000,
                )
            insert_opencode_v1_part(
                connection,
                "z-malformed",
                "m-assistant",
                "root",
                "{bad json",
                now_ms + 2000,
            )
            connection.execute(
                "INSERT INTO message VALUES (?, ?, ?, ?, ?)",
                (
                    "m-unknown",
                    "root",
                    now_ms + 2000,
                    now_ms + 2000,
                    json.dumps({"role": "future"}),
                ),
            )
            insert_opencode_v1_message(
                connection, "child-user", "child", "user", now_ms
            )
            insert_opencode_v1_part(
                connection,
                "child-text",
                "child-user",
                "child",
                {"type": "text", "text": "child"},
                now_ms,
            )
            connection.commit()
            connection.close()

            warnings = io.StringIO()
            with redirect_stderr(warnings):
                records, scanned, usable = find_opencode_sessions(
                    [database], now - timedelta(seconds=1), False
                )
            self.assertEqual(len(warnings.getvalue().splitlines()), 11)
            self.assertIn(
                "additional OpenCode warnings suppressed", warnings.getvalue()
            )
            self.assertEqual(scanned, 2)
            self.assertEqual(usable, [database])
            self.assertEqual(len(records), 1)
            record = records[0]
            self.assertEqual(record["meta"]["source_id"], "root")
            self.assertEqual(record["meta"]["cwd"], str(repo))
            self.assertEqual(record["skills_used"], ["skill-doctor"])
            self.assertEqual(record["stats"]["user_turns"], 1)
            self.assertEqual(record["stats"]["assistant_turns"], 1)
            self.assertEqual(record["stats"]["tool_calls"], 3)
            self.assertEqual(record["stats"]["repeated_tool_calls"], 1)
            self.assertEqual(record["stats"]["error_outputs"], 1)
            self.assertTrue(record["stats"]["has_code_edits"])
            self.assertEqual(
                record["modified_at"],
                datetime.fromtimestamp((now_ms + 4000) / 1000, tz=timezone.utc),
            )
            self.assertEqual(
                [
                    entry
                    for entry in record["entries"]
                    if entry[0] in {"user", "assistant"}
                ],
                [("user", "Fix the collector"), ("assistant", "Inspecting.")],
            )

            with redirect_stderr(io.StringIO()):
                with_children, _, _ = find_opencode_sessions(
                    [database], now - timedelta(seconds=1), True
                )
            self.assertEqual(
                {record["meta"]["source_id"] for record in with_children},
                {"root", "child"},
            )
            child = next(
                record
                for record in with_children
                if record["meta"]["source_id"] == "child"
            )
            self.assertEqual(child["meta"]["thread_source"], "subagent")
            self.assertTrue(child["stats"]["has_code_edits"])

            with redirect_stderr(io.StringIO()):
                outside, _, _ = find_opencode_sessions(
                    [database], now + timedelta(seconds=4), True
                )
            self.assertEqual(outside, [])

    def test_prefers_message_parts_and_falls_back_per_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            database = Path(tmp) / "opencode.db"
            now = datetime.now(timezone.utc)
            now_ms = int(now.timestamp() * 1000)
            connection = sqlite3.connect(database)
            create_opencode_schema(connection)
            for session_id in ("preferred", "fallback"):
                insert_opencode_session(connection, session_id, tmp, now_ms)

            insert_opencode_v1_message(
                connection, "preferred-user", "preferred", "user", now_ms
            )
            insert_opencode_v1_part(
                connection,
                "preferred-text",
                "preferred-user",
                "preferred",
                {"type": "text", "text": "message-part"},
                now_ms,
            )
            insert_opencode_message(
                connection,
                "ignored-fallback",
                "preferred",
                "user",
                1,
                {"text": "must-not-merge"},
                now_ms,
            )
            insert_opencode_message(
                connection,
                "fallback-user",
                "fallback",
                "user",
                1,
                {"text": "session-message"},
                now_ms,
            )
            connection.commit()
            connection.close()

            records, _, _ = find_opencode_sessions(
                [database], now - timedelta(seconds=1), False
            )
            by_id = {record["meta"]["source_id"]: record for record in records}
            self.assertEqual(by_id["preferred"]["entries"], [("user", "message-part")])
            self.assertEqual(
                by_id["fallback"]["entries"], [("user", "session-message")]
            )

    def test_accepts_either_current_schema_representation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            now = datetime.now(timezone.utc)
            now_ms = int(now.timestamp() * 1000)
            databases = []
            for name, dropped in (
                ("message-parts.db", ("session_message",)),
                ("session-message.db", ("message", "part")),
            ):
                database = root / name
                connection = sqlite3.connect(database)
                create_opencode_schema(connection)
                for table in dropped:
                    connection.execute(f"DROP TABLE {table}")
                insert_opencode_session(connection, name, root, now_ms)
                if name == "message-parts.db":
                    insert_opencode_v1_message(
                        connection, "message", name, "user", now_ms
                    )
                else:
                    insert_opencode_message(
                        connection,
                        "message",
                        name,
                        "user",
                        1,
                        {"text": "fallback"},
                        now_ms,
                    )
                connection.commit()
                connection.close()
                databases.append(database)

            records, _, usable = find_opencode_sessions(
                databases, now - timedelta(seconds=1), False
            )
            self.assertEqual(usable, databases)
            self.assertEqual(
                {record["meta"]["source_id"] for record in records},
                {"message-parts.db", "session-message.db"},
            )

    def test_reads_committed_uncheckpointed_wal_without_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            database = Path(tmp) / "opencode.db"
            now = datetime.now(timezone.utc)
            now_ms = int(now.timestamp() * 1000)
            writer = sqlite3.connect(database)
            self.assertEqual(
                writer.execute("PRAGMA journal_mode=WAL").fetchone()[0], "wal"
            )
            create_opencode_schema(writer)
            writer.commit()
            writer.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            insert_opencode_session(writer, "wal-session", tmp, now_ms)
            insert_opencode_v1_message(
                writer, "wal-user", "wal-session", "user", now_ms
            )
            insert_opencode_v1_part(
                writer,
                "wal-text",
                "wal-user",
                "wal-session",
                {"type": "text", "text": "from wal"},
                now_ms,
            )
            writer.commit()
            wal = Path(str(database) + "-wal")
            self.assertGreater(wal.stat().st_size, 0)

            reader = open_opencode_database(database)
            try:
                self.assertEqual(reader.execute("PRAGMA query_only").fetchone()[0], 1)
                self.assertEqual(
                    reader.execute("SELECT count(*) FROM session").fetchone()[0], 1
                )
                with self.assertRaises(sqlite3.OperationalError):
                    reader.execute("DELETE FROM session")
            finally:
                reader.close()

            records, _, _ = find_opencode_sessions(
                [database], now - timedelta(seconds=1), False
            )
            self.assertEqual(records[0]["entries"], [("user", "from wal")])
            self.assertEqual(writer.execute("PRAGMA journal_mode").fetchone()[0], "wal")
            self.assertEqual(
                writer.execute("SELECT count(*) FROM session").fetchone()[0], 1
            )
            self.assertGreater(wal.stat().st_size, 0)
            writer.close()

    def test_deduplicates_physical_databases_but_namespaces_distinct_copies(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            now = datetime.now(timezone.utc)
            now_ms = int(now.timestamp() * 1000)
            identities = []
            for name in ("opencode.db", "opencode-dev.db"):
                database = root / name
                connection = sqlite3.connect(database)
                create_opencode_schema(connection)
                insert_opencode_session(connection, "same-id", root, now_ms)
                connection.commit()
                connection.close()
                identities.append(database)
            (root / "alias.db").symlink_to(identities[0])

            discovered = discover_opencode_databases(
                [str(identities[0]), str(root / "alias.db"), str(identities[1])], root
            )
            records, _, _ = find_opencode_sessions(
                discovered, now - timedelta(seconds=1), False
            )
            self.assertEqual(len(discovered), 2)
            self.assertEqual(len({record["meta"]["id"] for record in records}), 2)

    def test_opencode_cli_writes_source_inventory_and_transcript(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            skill = repo / ".agents" / "skills" / "skill-doctor" / "SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("---\ndescription: Grade skills\n---\n")
            data = root / "data"
            data.mkdir()
            database = data / "custom.db"
            now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
            connection = sqlite3.connect(database)
            create_opencode_schema(connection)
            insert_opencode_session(connection, "cli-session", repo, now_ms)
            insert_opencode_v1_message(
                connection, "cli-user", "cli-session", "user", now_ms
            )
            insert_opencode_v1_part(
                connection,
                "cli-user-text",
                "cli-user",
                "cli-session",
                {"type": "text", "text": "grade this"},
                now_ms,
            )
            insert_opencode_v1_message(
                connection, "cli-assistant", "cli-session", "assistant", now_ms
            )
            insert_opencode_v1_part(
                connection,
                "cli-skill",
                "cli-assistant",
                "cli-session",
                {
                    "type": "tool",
                    "tool": "skill",
                    "state": {
                        "status": "completed",
                        "input": {"name": "skill-doctor"},
                        "output": "loaded",
                        "metadata": {"name": "skill-doctor"},
                    },
                },
                now_ms,
            )
            connection.commit()
            connection.close()
            out = root / "report"
            script = Path(__file__).resolve().parent / "collect_sessions.py"

            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--harness",
                    "opencode",
                    "--opencode-data-dir",
                    str(data),
                    "--opencode-db",
                    "custom.db",
                    "--repo",
                    str(repo),
                    "--out",
                    str(out),
                ],
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            inventory = json.loads((out / "inventory.json").read_text())
            self.assertEqual(inventory["harness"], "opencode")
            self.assertEqual(list(inventory["sources"]), ["opencode"])
            self.assertEqual(inventory["opencode_databases"], [str(database.resolve())])
            self.assertEqual(inventory["stats"]["sessions_sampled"], 1)
            self.assertEqual(inventory["stats"]["session_records_in_window"], 1)
            self.assertEqual(inventory["sessions"][0]["skills_used"], ["skill-doctor"])
            transcript = Path(inventory["sessions"][0]["transcript_path"])
            self.assertIn("[user] grade this", transcript.read_text())

            subprocess.run(
                ["git", "init", str(repo)], capture_output=True, check=True, text=True
            )
            all_out = root / "all-report"
            all_result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--harness",
                    "opencode",
                    "--opencode-data-dir",
                    str(data),
                    "--opencode-db",
                    "custom.db",
                    "--all-conversations",
                    "--out",
                    str(all_out),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(all_result.returncode, 0, all_result.stderr)
            all_inventory = json.loads((all_out / "inventory.json").read_text())
            self.assertEqual(
                all_inventory["sessions"][0]["skills_used"], ["skill-doctor"]
            )

            missing = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--harness",
                    "opencode",
                    "--opencode-data-dir",
                    str(data),
                    "--opencode-db",
                    "missing.db",
                    "--all-conversations",
                    "--out",
                    str(root / "missing-report"),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(missing.returncode, 1)
            self.assertIn("no usable OpenCode databases found", missing.stderr)
            self.assertIn(str(data / "missing.db"), missing.stderr)

            claude_projects = root / "claude" / "projects"
            claude_projects.mkdir(parents=True)
            mixed = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--harness",
                    "all",
                    "--claude-home",
                    str(root / "claude"),
                    "--codex-home",
                    str(root / "missing-codex"),
                    "--opencode-data-dir",
                    str(data),
                    "--opencode-db",
                    "missing.db",
                    "--warp-data-dir",
                    str(root / "missing-warp"),
                    "--all-conversations",
                    "--out",
                    str(root / "mixed-report"),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(mixed.returncode, 0, mixed.stderr)
            self.assertIn(
                f"warning: OpenCode database {data / 'missing.db'}", mixed.stderr
            )


if __name__ == "__main__":
    unittest.main()
