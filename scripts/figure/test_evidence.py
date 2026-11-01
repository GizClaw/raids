"""Source integrity tests; native selector execution is validated separately."""

from __future__ import annotations

import tempfile
import unittest
import json
import hashlib
from pathlib import Path

import evidence
import generate


class CardEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.repo = generate.repository_root()
        self.data = generate.load(self.repo, "figure-li-bai")
        self.units = evidence.units(self.repo, self.data)

    def test_every_source_field_is_losslessly_covered(self):
        lines = (self.repo / "cards/figure/李白.txt").read_text().splitlines()
        for line_number, line in enumerate(lines, 1):
            field, _, original = line.partition("：")
            units = [unit for unit in self.units if unit["line"] == line_number]
            self.assertEqual([unit["part"] for unit in units], list(range(1, len(units) + 1)))
            self.assertTrue(all(unit["field"] == field for unit in units))
            self.assertEqual("；".join(unit["text"] for unit in units), original)

    def test_qualifiers_are_not_cut_into_a_different_claim(self):
        birthplace = next(unit for unit in self.units if unit["field"] == "出生地")
        self.assertEqual(birthplace["text"], self.data["card"]["出生地"])
        legends = [unit for unit in self.units if unit["field"] == "后人传说"]
        self.assertEqual([unit["text"] for unit in legends], self.data["card"]["后人传说"].split("；"))
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            card = repo / "cards/figure/李白.txt"
            card.parent.mkdir(parents=True)
            long_qualified = "后人传说：" + "流传的说法，" * 120 + "但未证实，不能称为本人亲历"
            card.write_text(long_qualified)
            units = evidence.units(repo, self.data)
            self.assertEqual(len(units), 1)
            self.assertEqual(units[0]["text"], long_qualified.partition("：")[2])
            self.assertGreater(units[0]["characters"], 467)

    def test_existing_role_aliases_are_lookup_only(self):
        du_fu = next(unit for unit in self.units
                     if unit["field"] == "身边的人" and unit["text"].startswith("杜甫"))
        self.assertIn("du", du_fu["terms"])
        self.assertIn("fu", du_fu["terms"])
        self.assertNotIn("du fu", du_fu["text"].lower())
        self.assertEqual(du_fu["rendered"], "身边的人：" + du_fu["text"])
        self.assertIn("杜子美", du_fu["mentions"])
        self.assertIn("子美", du_fu["mentions"])

    def test_search_is_an_explicit_package_dependency(self):
        manifest = json.loads(generate.raid_manifest("figure-li-bai", self.data))
        tools = manifest["implementations"][generate.IMPLEMENTATION]["parameters"]["tools"]
        self.assertEqual(tools["reference.search"]["resource_id"], "volc-reference-search")
        other = generate.load(self.repo, "figure-confucius")
        other_manifest = json.loads(generate.raid_manifest("figure-confucius", other))
        self.assertNotIn("tools", other_manifest["implementations"][generate.IMPLEMENTATION]["parameters"])

    def test_no_editorial_reference_or_test_answer_enters_source(self):
        edited = {**self.data, "narration": {"mode": "compact", "reference": "杜撰的测试标准答案"}}
        self.assertEqual(evidence.units(self.repo, edited), self.units)

    def test_english_units_are_bound_to_the_entire_source_card(self):
        card = self.repo / "cards/figure/李白.txt"
        mirror = json.loads(card.with_suffix(".en.json").read_text())
        self.assertEqual(mirror["source_sha256"], hashlib.sha256(card.read_bytes()).hexdigest())
        self.assertEqual(set(mirror["units"]), {f"L{unit['line']}.{unit['part']}" for unit in self.units})
        for value in mirror["units"].values():
            self.assertTrue(value.strip())
            self.assertNotIn("【", value)
            self.assertNotIn("】", value)
        for unit in self.units:
            if unit["field"] == "名句":
                self.assertIn("Paraphrase:", mirror["units"][f"L{unit['line']}.{unit['part']}"])

    def test_scene_view_has_the_same_card_and_explicit_existing_sources(self):
        card = self.repo / "cards/figure/李白.txt"
        scene = json.loads(card.with_suffix(".scene.json").read_text())
        self.assertEqual(scene["source_sha256"], hashlib.sha256(card.read_bytes()).hexdigest())
        self.assertEqual(len(scene["source_units"]), len(set(scene["source_units"])))
        self.assertTrue(set(scene["source_units"]) <= {f"L{unit['line']}.{unit['part']}" for unit in self.units})
        self.assertTrue(scene["context"].strip())


if __name__ == "__main__":
    unittest.main()
