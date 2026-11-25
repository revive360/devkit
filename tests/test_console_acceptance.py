import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("console_acceptance",ROOT/"scripts/accept_console.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.record=json.loads((ROOT/"docs/console-acceptance-2026-11-25.json").read_text())
        self.build={"source_commit":self.record["source_commit"],"xex_sha256":self.record["xex_sha256"],"console_validation":"pending"}

    def test_acceptance_records_exact_scope_and_does_not_mutate_build(self):
        accepted=module.apply_acceptance(self.build,self.record)
        self.assertEqual(accepted["console_validation"],"accepted")
        self.assertEqual(accepted["console_validation_date"],"2026-11-25")
        self.assertEqual(accepted["console_validation_record"]["console_count"],1)
        self.assertEqual(accepted["source_commit"],self.build["source_commit"])
        self.assertEqual(self.build["console_validation"],"pending")

    def test_changed_source_or_binary_does_not_inherit_acceptance(self):
        for key,value in [("source_commit","0"*40),("xex_sha256","0"*64)]:
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,"does not match"):
                module.apply_acceptance({**self.build,key:value},self.record)

    def test_pending_record_cannot_be_used_as_acceptance(self):
        with self.assertRaisesRegex(ValueError,"explicit"):
            module.apply_acceptance(self.build,{**self.record,"console_validation":"pending"})
