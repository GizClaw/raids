from __future__ import annotations

from pathlib import Path
import tempfile
import textwrap
import unittest

from scripts.validate_pixa import PixaValidationError, validate_pixa


PETDEF = """
apiVersion: gizclaw.admin/v1alpha1
kind: PetDef
metadata:
  name: petdef-codex
spec:
  visual:
    refs: {images: [], videos: []}
    bindings:
      behaviors: {feed: waiting, bathe: jumping, play: running, heal: waving}
      states: {idle: idle, sick: failed, dead: failed}
    pixa:
      asset_ref: asset://codex/pets/codex.pixa
      metadata:
        version: "1"
        canvas: {width: 96, height: 104}
        clips:
          - {id: idle, pixa_clip_name: idle}
          - {id: waiting, pixa_clip_name: waiting}
          - {id: jumping, pixa_clip_name: jumping}
          - {id: running, pixa_clip_name: running}
          - {id: waving, pixa_clip_name: waving}
          - {id: failed, pixa_clip_name: failed}
"""


class PixaValidationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.write(PETDEF)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write(self, contents: str) -> None:
        path = self.root / "petdefs/petdef-codex.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(contents).lstrip(), encoding="utf-8")

    def assert_invalid(self, expected: str) -> None:
        with self.assertRaises(PixaValidationError) as raised:
            validate_pixa(self.root)
        self.assertIn(expected, "\n".join(raised.exception.errors))

    def test_accepts_complete_pixa_declaration(self) -> None:
        validate_pixa(self.root)

    def test_rejects_unsupported_asset_reference(self) -> None:
        self.write(
            PETDEF.replace(
                "asset://codex/pets/codex.pixa",
                "https://example.com/codex.pixa",
            )
        )
        self.assert_invalid(
            "spec.visual.pixa.asset_ref must start with asset://codex/pets/"
        )

    def test_rejects_duplicate_pixa_clip_name(self) -> None:
        self.write(
            PETDEF.replace(
                "{id: waiting, pixa_clip_name: waiting}",
                "{id: waiting, pixa_clip_name: idle}",
            )
        )
        self.assert_invalid("pixa_clip_name 'idle' is duplicated")

    def test_rejects_binding_without_metadata_clip(self) -> None:
        self.write(PETDEF.replace("feed: waiting", "feed: eating"))
        self.assert_invalid(
            "spec.visual.bindings.behaviors.feed 'eating' is not declared"
        )

    def test_rejects_oversized_pixa_clip_name(self) -> None:
        self.write(
            PETDEF.replace(
                "pixa_clip_name: waiting",
                "pixa_clip_name: " + "x" * 33,
            )
        )
        self.assert_invalid("pixa_clip_name must be at most 32 UTF-8 bytes")


if __name__ == "__main__":
    unittest.main()
