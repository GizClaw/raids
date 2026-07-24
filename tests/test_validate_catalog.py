from __future__ import annotations

from pathlib import Path
import tempfile
import textwrap
import unittest

from scripts.validate_catalog import (
    PUBLIC_DEFAULT_TOKEN,
    CatalogValidationError,
    validate_catalog,
)


PROFILE = """
apiVersion: gizclaw.admin/v1alpha1
kind: RuntimeProfile
metadata:
  name: default
spec:
  workflows:
    system:
      friend_chatroom: chatroom
      group_chatroom: chatroom
      pet: pet-care
    collections: {}
  resources:
    models:
      asr:
        resource_id: asr-model
        i18n:
          en: {display_name: ASR}
          zh-CN: {display_name: 语音识别}
"""

TOKEN = f"""
apiVersion: gizclaw.admin/v1alpha1
kind: RegistrationToken
metadata:
  name: default-runtime
spec:
  token: {PUBLIC_DEFAULT_TOKEN}
  runtime_profile_name: default
"""

CHATROOM = """
apiVersion: gizclaw.admin/v1alpha1
kind: Workflow
metadata:
  name: chatroom
spec:
  driver: chatroom
  chatroom:
    transcript:
      enabled: true
      asr_model: asr
"""

PET = """
apiVersion: gizclaw.admin/v1alpha1
kind: Workflow
metadata:
  name: pet-care
spec:
  driver: pet
  pet: {}
"""

MODEL = """
apiVersion: gizclaw.admin/v1alpha1
kind: Model
metadata:
  name: asr-model
spec: {}
"""


class CatalogValidationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.write("runtime-profiles/default.yaml", PROFILE)
        self.write("registration-tokens/default.yaml", TOKEN)
        self.write("workflows/chatroom/social.yaml", CHATROOM)
        self.write("workflows/pet/pet-care.yaml", PET)
        self.write("models/asr-model.yaml", MODEL)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write(self, relative: str, contents: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(contents).lstrip(), encoding="utf-8")

    def assert_invalid(self, expected: str) -> None:
        with self.assertRaises(CatalogValidationError) as raised:
            validate_catalog(self.root)
        self.assertIn(expected, "\n".join(raised.exception.errors))

    def test_accepts_complete_default_bootstrap_closure(self) -> None:
        validate_catalog(self.root)

    def test_public_default_token_uuidv5_derivation_is_stable(self) -> None:
        self.assertEqual(
            PUBLIC_DEFAULT_TOKEN,
            "28c4e4e9-a05f-5a7e-815e-9cf9afb6878f",
        )

    def test_rejects_missing_resource_reference(self) -> None:
        self.write(
            "models/asr-model.yaml",
            MODEL.replace("name: asr-model", "name: another-model"),
        )
        self.assert_invalid("Model/asr-model does not exist")

    def test_rejects_unbound_workflow_alias(self) -> None:
        self.write(
            "workflows/chatroom/social.yaml",
            CHATROOM.replace("asr_model: asr", "asr_model: missing"),
        )
        self.assert_invalid("required models alias 'missing' is not bound")

    def test_rejects_duplicate_token_value(self) -> None:
        self.write(
            "registration-tokens/other.yaml",
            TOKEN.replace("name: default-runtime", "name: other"),
        )
        self.assert_invalid("token value duplicates RegistrationToken/default-runtime")

    def test_rejects_duplicate_normalized_token_value(self) -> None:
        for case, token in {
            "ascii": f" {PUBLIC_DEFAULT_TOKEN} ",
            "unicode": f"\u00a0{PUBLIC_DEFAULT_TOKEN}\u00a0",
        }.items():
            with self.subTest(case=case):
                self.write(
                    "registration-tokens/other.yaml",
                    TOKEN.replace("name: default-runtime", "name: other").replace(
                        f"token: {PUBLIC_DEFAULT_TOKEN}", f'token: "{token}"'
                    ),
                )
                self.assert_invalid(
                    "token value duplicates RegistrationToken/default-runtime"
                )

    def test_rejects_missing_empty_or_non_string_token(self) -> None:
        cases = {
            "missing": "",
            "empty": '  token: "   "\n',
            "non-string": "  token: 123\n",
        }
        for case, token_line in cases.items():
            with self.subTest(case=case):
                other = TOKEN.replace("name: default-runtime", "name: other").replace(
                    f"  token: {PUBLIC_DEFAULT_TOKEN}\n", token_line
                )
                self.write("registration-tokens/other.yaml", other)
                self.assert_invalid(
                    "RegistrationToken/other.spec.token must be a non-empty string"
                )

    def test_rejects_registration_token_with_missing_profile(self) -> None:
        self.write(
            "registration-tokens/other.yaml",
            TOKEN.replace("name: default-runtime", "name: other")
            .replace(f"token: {PUBLIC_DEFAULT_TOKEN}", "token: other")
            .replace("runtime_profile_name: default", "runtime_profile_name: missing"),
        )
        self.assert_invalid(
            "RegistrationToken/other.spec.runtime_profile_name references "
            "missing RuntimeProfile/missing"
        )

    def test_rejects_placeholder_in_default_profile(self) -> None:
        self.write(
            "runtime-profiles/default.yaml",
            PROFILE.replace("resource_id: asr-model", "resource_id: <model-id>"),
        )
        self.assert_invalid("unresolved placeholder")

    def test_rejects_public_default_firmware_binding(self) -> None:
        self.write(
            "registration-tokens/default.yaml",
            TOKEN + "  firmware_id: h106\n",
        )
        self.assert_invalid("prohibited default field spec.firmware_id")


if __name__ == "__main__":
    unittest.main()
