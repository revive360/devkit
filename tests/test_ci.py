"""Behavior checks for recipe invalidation and pinned compiler stage splitting."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'ci' / (name + '.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

class ImageTests(unittest.TestCase):
    def test_stage_boundary_preserves_builder(self):
        mod = module('toolchain-stage')
        source = 'before\n' + mod.ANCHOR + ' options\nafter\n'
        result = mod.split(source)
        self.assertIn('!= bootstrap ] || exit 0\n' + mod.ANCHOR, result)
        self.assertEqual(result.replace('[ "${REVIVE360_TOOLCHAIN_STAGE:-}" != bootstrap ] || exit 0\n', ''), source)
        for invalid in ('no boundary', source + source):
            with self.assertRaises(ValueError):
                mod.split(invalid)

    def test_hash_tracks_content_and_names(self):
        mod = module('recipe-id')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in ('upstreams.lock.json', 'scripts/bootstrap.sh', 'scripts/fetch.py', 'ci/Dockerfile'):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(name)
            original = mod.recipe_id(root)
            (root / 'ci/Dockerfile').write_text('changed')
            self.assertNotEqual(original, mod.recipe_id(root))
            (root / 'ci/Dockerfile').write_text('ci/Dockerfile')
            self.assertEqual(original, mod.recipe_id(root))
            (root / 'ci/Dockerfile').rename(root / 'ci/renamed')
            self.assertNotEqual(original, mod.recipe_id(root))
