"""Strict structured lean output, rejection evidence, and extraction recovery."""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "arena"))
import bracket as B  # noqa: E402


class LeanResultTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="arena-result-")
        self.addCleanup(self.temp.cleanup)
        self.state = B.new_state(2, 7, B.load_strategies(), self.temp.name)
        self.match = self.state["rounds"][0]["matches"][0]
        a, b = self.match["a"], self.match["b"]
        score = lambda value: dict({key: value for key, _ in B.WEIGHTS}, fatal=False)
        self.good = {"match": self.match["id"], "scores": {a: score(8), b: score(7)},
                     "winner": a, "reason": "Stronger verified coverage.", "survived": ["Edge case checked"],
                     "standing": {a: [], b: []}, "solution": "Complete answer.\nLiteral quotes: \"hello\".\n"}
        self.result = Path(B.result_out(self.temp.name, 1, self.match["id"]))
        self.result.parent.mkdir()
        self.verdict = Path(B.verdict_out(self.temp.name, 1, self.match["id"]))
        self.solution = Path(B.synthesized_out(self.temp.name, 1, self.match["id"]))

    def put(self, result=None):
        self.result.write_text(json.dumps(self.good if result is None else result), encoding="utf-8")

    def test_valid_result_extracts_exact_answer_and_advances(self):
        self.put()
        original = self.result.read_bytes()
        self.assertEqual(B.collect(self.state)[0][1], "recorded")
        self.assertEqual(self.result.read_bytes(), original)
        self.assertEqual(self.solution.read_bytes(), self.good["solution"].encode("utf-8"))
        self.assertEqual(json.loads(self.verdict.read_text()), {k: v for k, v in self.good.items() if k != "solution"})
        B.advance(self.state)
        self.assertEqual(self.state["champion"], self.good["winner"])
        self.assertEqual(self.state["agents"][self.state["champion"]]["solution"], str(self.solution))
        self.assertEqual(B.collect(self.state), [])

    def test_invalid_artifacts_preserve_bytes_and_existing_derived_files(self):
        invalid = ["garbage", "[]", json.dumps(self.good) + " trailing content",
                   "```json\n" + json.dumps(self.good) + "\n```",
                   json.dumps(self.good).replace('"match":', '"match": "duplicate", "match":', 1)]
        mutations = [
            ("match", "r2-m01"), ("winner", "a999"), ("winner", self.match["b"]),
            ("solution", None), ("solution", []), ("solution", "   \n"), ("solution", "bad\x00text"),
            ("solution", "bad\ud800text"), ("reason", ""), ("survived", [2]),
            ("standing", {self.match["a"]: [], self.match["b"]: "wrong"}),
        ]
        for key, value in mutations:
            bad = copy.deepcopy(self.good)
            bad[key] = value
            invalid.append(json.dumps(bad))
        for key in self.good:
            bad = copy.deepcopy(self.good)
            del bad[key]
            invalid.append(json.dumps(bad))
        bad = dict(self.good, extra="no extra fields")
        invalid.append(json.dumps(bad))
        for value in [True, "8", -1, 11, float("nan"), float("inf"), 10 ** 400]:
            bad = copy.deepcopy(self.good)
            bad["scores"][self.match["a"]]["correctness"] = value
            invalid.append(json.dumps(bad))
        for key, value in [("fatal", "false"), ("extra", 1)]:
            bad = copy.deepcopy(self.good)
            bad["scores"][self.match["a"]][key] = value
            invalid.append(json.dumps(bad))
        bad = copy.deepcopy(self.good)
        del bad["scores"][self.match["a"]]["clarity"]
        invalid.append(json.dumps(bad))
        bad = copy.deepcopy(self.good)
        bad["scores"]["a999"] = bad["scores"].pop(self.match["b"])
        invalid.append(json.dumps(bad))
        self.verdict.write_bytes(b"prior verdict evidence")
        self.solution.write_bytes(b"prior answer evidence")
        for index, text in enumerate(invalid):
            with self.subTest(case=index):
                self.result.write_bytes(text.encode("utf-8"))
                before = copy.deepcopy(self.state)
                self.assertEqual(B.collect(self.state)[0][1], "unreadable")
                self.assertEqual(self.state, before)
                rejected = str(self.result) + ".unreadable" + (".%d" % index if index else "")
                self.assertEqual(Path(rejected).read_bytes(), text.encode("utf-8"))
                self.assertEqual(self.verdict.read_bytes(), b"prior verdict evidence")
                self.assertEqual(self.solution.read_bytes(), b"prior answer evidence")
                self.assertFalse(self.result.exists())

    def test_literal_set_content_and_embedded_verdict_corruption_is_not_repaired(self):
        embedded = json.dumps({k: v for k, v in self.good.items() if k != "solution"})
        corrupted = "Plausible answer.\n '@\nSet-Content -LiteralPath '.arena\\run\\r1\\r1-m01.verdict.json' -Value @'\n" + embedded
        for index, answer in enumerate([corrupted, "Plausible answer.\n" + embedded]):
            with self.subTest(case=index):
                self.put(dict(self.good, solution=answer))
                original = self.result.read_bytes()
                self.assertEqual(B.collect(self.state)[0][1], "unreadable")
                rejected = str(self.result) + ".unreadable" + (".%d" % index if index else "")
                self.assertEqual(Path(rejected).read_bytes(), original)
                self.assertFalse(self.verdict.exists())
                self.assertFalse(self.solution.exists())
                self.assertIsNone(self.match["winner"])

    def test_invalid_utf8_is_rejected_without_replacement_characters(self):
        self.result.write_bytes(b'{"solution": "\xff"}')
        self.assertEqual(B.collect(self.state)[0][1], "unreadable")
        self.assertEqual(Path(str(self.result) + ".unreadable").read_bytes(), b'{"solution": "\xff"}')

    def test_valid_answer_can_discuss_an_arena_schema(self):
        example = {"match": self.match["id"], "scores": {}, "winner": self.match["a"]}
        solution = "Example schema for your documentation:\n" + json.dumps(example)
        self.put(dict(self.good, solution=solution))
        self.assertEqual(B.collect(self.state)[0][1], "recorded")
        self.assertEqual(self.solution.read_text(encoding="utf-8"), solution)

    def test_capacity_plans_and_invalid_wave(self):
        for n, mode, waves in [(2, "lean", [3, 2, 2, 2]), (4, "lean", [7, 4, 4, 3]),
                               (4, "classic", [19, 10, 10, 7])]:
            for capacity, expected in enumerate(waves, start=1):
                self.assertEqual(B.plan_totals(n, capacity, mode)["waves"], expected)
        for invalid in [0, -1, True, 1.5]:
            with self.assertRaisesRegex(B.ArenaError, "wave"):
                B.plan_totals(2, invalid)

    def test_missing_result_cannot_fall_back_to_stale_two_file_outputs(self):
        self.verdict.write_text(json.dumps(self.good), encoding="utf-8")
        self.solution.write_text("stale answer", encoding="utf-8")
        self.assertEqual(B.collect(self.state)[0][1], "missing")
        self.assertIsNone(self.match["winner"])
        self.assertEqual(B.phase_jobs(self.state, "judge")[0]["outputs"], [str(self.result)])

    def test_atomic_replace_failure_keeps_match_open_and_source_retryable(self):
        self.put()
        self.verdict.write_bytes(b"prior verdict")
        original = self.result.read_bytes()
        replace = os.replace

        def fail_verdict(source, target):
            if str(target) == str(self.verdict):
                raise PermissionError("simulated locked verdict")
            return replace(source, target)

        with mock.patch.object(B.os, "replace", side_effect=fail_verdict):
            with self.assertRaisesRegex(B.ArenaError, "match unrecorded"):
                B.collect(self.state)
        self.assertIsNone(self.match["winner"])
        self.assertEqual(self.result.read_bytes(), original)
        self.assertEqual(self.verdict.read_bytes(), b"prior verdict")
        self.assertEqual(list(self.result.parent.glob(".arena-extract-*")), [])
        self.assertEqual(B.collect(self.state)[0][1], "recorded")
        self.assertEqual(self.solution.read_bytes(), self.good["solution"].encode("utf-8"))

    def test_stage_failure_does_not_publish_either_derived_file(self):
        self.put()
        with mock.patch.object(B.os, "fsync", side_effect=OSError("disk full")):
            with self.assertRaisesRegex(B.ArenaError, "source retained"):
                B.collect(self.state)
        self.assertTrue(self.result.exists())
        self.assertFalse(self.verdict.exists())
        self.assertFalse(self.solution.exists())
        self.assertIsNone(self.match["winner"])

    def test_legacy_two_file_state_collects_without_reinterpreting_contract(self):
        self.state.pop("lean_result_format")
        B.validate_state(self.state, "arena.json", self.temp.name)
        self.verdict.write_text(json.dumps({k: v for k, v in self.good.items() if k != "solution"}), encoding="utf-8")
        self.solution.write_text(self.good["solution"], encoding="utf-8")
        jobs = B.phase_jobs(self.state, "judge")
        prompt = B.render_job(self.state, jobs[0], B.load_templates(), "Task")
        self.assertIn(str(self.solution), prompt)
        self.assertNotIn('"solution":', prompt)
        self.assertEqual(B.collect(self.state)[0][1], "recorded")
        self.assertFalse(self.result.exists())


if __name__ == "__main__":
    unittest.main()
