"""Contrôle du format Agent Skills / plugin Claude Code."""

import json
import os
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "SKILL.md"
PLUGIN = ROOT / ".claude-plugin" / "plugin.json"
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RESERVED = ("anthropic", "claude")


def parse_frontmatter(text: str) -> dict:
    if not text.startswith("---\n"):
        raise AssertionError("SKILL.md doit commencer par un frontmatter YAML")
    rest = text[4:]
    end = rest.find("\n---")
    if end < 0:
        raise AssertionError("frontmatter YAML non refermé")
    block = rest[:end]
    data = {}
    current = None
    indent = None
    for line in block.splitlines():
        if current and (line.startswith("  ") or line.startswith("\t")):
            key, _, value = line.strip().partition(":")
            data[current][key.strip()] = value.strip().strip('"')
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value == "":
            current = key
            data[current] = {}
        else:
            current = None
            data[key] = value.strip('"')
    return data


class SkillFormatTest(unittest.TestCase):
    def test_skill_md_respecte_agentskills(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertLessEqual(text.count("\n") + 1, 500)
        meta = parse_frontmatter(text)
        name = meta["name"]
        description = meta["description"]
        self.assertTrue(NAME_RE.fullmatch(name), name)
        self.assertLessEqual(len(name), 64)
        self.assertFalse(name.startswith("-") or name.endswith("-"))
        self.assertNotIn("--", name)
        for reserved in RESERVED:
            self.assertNotIn(reserved, name)
        self.assertTrue(description)
        self.assertLessEqual(len(description), 1024)
        self.assertNotIn("<", description)
        self.assertNotIn(">", description)
        self.assertIn("Légifrance", description)
        self.assertIn("/legifrance", description)
        if "compatibility" in meta:
            self.assertLessEqual(len(meta["compatibility"]), 500)
        allowed = {
            "name", "description", "license", "compatibility",
            "metadata", "allowed-tools",
        }
        self.assertTrue(set(meta) <= allowed, set(meta) - allowed)
        self.assertIn("${CLAUDE_SKILL_DIR}", text)

    def test_plugin_et_marketplace_claude_code(self):
        plugin = json.loads(PLUGIN.read_text(encoding="utf-8"))
        marketplace = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
        self.assertEqual(plugin["name"], "legifrance")
        self.assertEqual(plugin["displayName"], "Skill Legifrance")
        self.assertIn("homepage", plugin)
        self.assertEqual(marketplace["name"], "skill-legifrance")
        self.assertEqual(marketplace["owner"]["name"], "PieceMaker Legal")
        plugins = marketplace["plugins"]
        self.assertEqual(len(plugins), 1)
        entry = plugins[0]
        self.assertEqual(entry["name"], "legifrance")
        self.assertEqual(entry["source"], "./")
        self.assertIs(entry["strict"], False)


if __name__ == "__main__":
    unittest.main()
