#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""vibegit test suite — synthetic git repositories, deterministic expectations."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "vibegit.py"

BASE_ENV = dict(
    os.environ,
    GIT_AUTHOR_NAME="Alice Dev",
    GIT_AUTHOR_EMAIL="alice@example.com",
    GIT_COMMITTER_NAME="Alice Dev",
    GIT_COMMITTER_EMAIL="alice@example.com",
    GIT_CONFIG_NOSYSTEM="1",
    GIT_TERMINAL_PROMPT="0",
)


def run_tool(*args, cwd=None):
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    return subprocess.run(
        [sys.executable, str(TOOL), *[str(a) for a in args]],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=120, cwd=cwd, env=env,
    )


class RepoCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="vibegit_test_"))
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        self._day = 1
        self._git("init", "-q")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _env(self, date=None):
        day = date or "2026-01-%02dT12:00:00" % self._day
        self._day += 1
        return dict(BASE_ENV, GIT_AUTHOR_DATE=day, GIT_COMMITTER_DATE=day)

    def _git(self, *args, env=None):
        return subprocess.run(
            ["git", "-C", str(self.repo), "-c", "commit.gpgsign=false", *args],
            check=True, capture_output=True, text=True, env=env or self._env(),
        )

    def commit(self, message, files=None, author=None):
        for rel, content in (files or {"src/app.py": "# code\n"}).items():
            p = self.repo / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
        env = self._env()
        if author:
            env.update(GIT_AUTHOR_NAME=author, GIT_COMMITTER_NAME=author)
        self._git("add", "-A", env=env)
        self._git("commit", "-q", "-m", message, env=env)

    def json_report(self, *args):
        p = run_tool(str(self.repo), "--format", "json", *args)
        self.assertEqual(p.returncode, 0, p.stderr)
        return json.loads(p.stdout)


class TestVibegit(RepoCase):
    def test_clean_repo_scores_low(self):
        self.commit("Add parser for CLI input", {"src/parser.py": "def parse(x):\n    return x\n"})
        self.commit("Refactor config loader", {"src/config.py": "DEFAULTS = {}\n"})
        self.commit("Improve error messages", {"src/errors.py": "class AppError(Exception):\n    pass\n"})
        report = self.json_report()
        self.assertEqual(report["ai"]["confirmed"], 0)
        self.assertEqual(report["ai"]["likely"], 0)
        self.assertLessEqual(report["score"], 14)
        self.assertEqual(report["verdict"], "Clean")

    def test_detects_ai_coauthor_trailer(self):
        self.commit("Add feature flag support",
                    {"src/flags.py": "FLAGS = {}\n"},
                    author="Alice Dev")
        # amend-style: second commit carries the trailer
        self.commit("Wire feature flag into startup\n\nCo-Authored-By: Claude <noreply@anthropic.com>",
                    {"src/startup.py": "FLAGS = {}\n"})
        report = self.json_report()
        self.assertGreaterEqual(report["ai"]["confirmed"], 1)
        self.assertGreater(report["ai"]["estimate_pct"], 0)
        self.assertIn("claude", report["ai"]["tools"])

    def test_detects_generated_with_message(self):
        self.commit("Bootstrap data models\n\nGenerated with [Cursor]",
                    {"src/models.py": "class User:\n    pass\n"})
        report = self.json_report()
        self.assertGreaterEqual(report["ai"]["confirmed"], 1)
        self.assertIn("cursor", report["ai"]["tools"])

    def test_detects_ai_author(self):
        self.commit("Add API client", {"src/client.py": "def get():\n    return 1\n"}, author="GitHub Copilot")
        report = self.json_report()
        self.assertGreaterEqual(report["ai"]["confirmed"], 1)

    def test_giant_commit_signal(self):
        big = "\n".join("line_%d = %d" % (i, i) for i in range(600))
        self.commit("Add generated scaffolding", {"src/big.py": big})
        report = self.json_report()
        self.assertEqual(report["signals"]["giant_commits"]["count"], 1)
        self.assertGreater(report["score_parts"]["giant_commits"], 0)

    def test_test_deletion_signal(self):
        self.commit("Add tests for parser", {"tests/test_parser.py": "def test_ok():\n    assert True\n"})
        self.commit("Remove stale tests", {"src/parser.py": "def parse(x):\n    return x\n"}, )
        # delete the test file in its own commit
        env = self._env()
        (self.repo / "tests" / "test_parser.py").unlink()
        self._git("add", "-A", env=env)
        self._git("commit", "-q", "-m", "Drop outdated parser tests", env=env)
        report = self.json_report()
        self.assertGreaterEqual(report["signals"]["test_deletions"], 1)
        self.assertGreater(report["score_parts"]["test_deletions"], 0)

    def test_short_message_signal(self):
        self.commit("Add billing module", {"src/billing.py": "TOTAL = 0\n"})
        self.commit("wip", {"src/billing.py": "TOTAL = 1\n"})
        report = self.json_report()
        self.assertGreaterEqual(report["signals"]["short_messages"]["count"], 1)

    def test_badge_and_gate(self):
        self.commit("Add oversized dump\n\nGenerated with [Aider]",
                    {"src/dump.py": "\n".join("x%d = %d" % (i, i) for i in range(700))})
        badge = self.tmp / "badge.svg"
        p = run_tool(str(self.repo), "--badge", str(badge), "--format", "json")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue(badge.exists())
        text = badge.read_text(encoding="utf-8")
        self.assertIn("vibegit", text)
        self.assertIn("svg", text)
        # gate: score is high, so a max-score of 0 must fail
        p = run_tool(str(self.repo), "--max-score", "0", "--format", "json")
        self.assertEqual(p.returncode, 1)

    def test_share_line_and_card(self):
        self.commit("Add parser for CLI input", {"src/parser.py": "def parse(x):\n    return x\n"})
        p = run_tool(str(self.repo), "--share")
        self.assertEqual(p.returncode, 0)
        self.assertIn("vibegit", p.stdout)
        self.assertIn("slop", p.stdout)
        p = run_tool(str(self.repo), "--format", "card")
        self.assertEqual(p.returncode, 0)
        self.assertIn("AI-assist", p.stdout)

    def test_markdown_and_json_contract(self):
        self.commit("Add parser for CLI input", {"src/parser.py": "def parse(x):\n    return x\n"})
        p = run_tool(str(self.repo), "--format", "md")
        self.assertEqual(p.returncode, 0)
        self.assertIn("# vibegit report", p.stdout)
        first = self.json_report()
        second = self.json_report()
        self.assertEqual(first, second, "output must be deterministic")
        for key in ("tool", "version", "repo", "branch", "total_commits", "ai",
                    "signals", "score_parts", "score", "verdict"):
            self.assertIn(key, first)

    def test_non_repo_exits_2(self):
        plain = self.tmp / "plain"
        plain.mkdir()
        p = run_tool(str(plain))
        self.assertEqual(p.returncode, 2)
        self.assertIn("not a git repository", p.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
