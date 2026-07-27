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
    memories:
      pet-care:
        layout_id: pet-care
        driver: flowcraft
        connection:
          type: flowcraft_bbh
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
  memory: pet-care
  pet: {}
"""

MEMORY_LAYOUT = """
apiVersion: gizclaw.admin/v1alpha1
kind: MemoryLayout
metadata:
  name: pet-care
spec:
  flowcraft:
    extraction:
      model: asr
      mode: single_pass
    bbh: {}
    lanes:
      - name: pet-care
        kind: note
        description: Durable pet facts.
        extract: Extract durable pet facts.
        recall: Use relevant pet facts.
    write:
      mode: sync
      tier: general
  mem0:
    custom_instructions: Keep durable pet facts.
    custom_categories:
      pet-care: Durable pet facts.
  volc_mem0:
    strategies:
      - {name: pet-care, type: semantic, custom_instructions: Keep durable pet facts.}
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
        self.write("memory-layouts/pet-care.yaml", MEMORY_LAYOUT)
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

    def test_rejects_missing_memory_layout(self) -> None:
        self.write(
            "memory-layouts/pet-care.yaml",
            MEMORY_LAYOUT.replace("name: pet-care", "name: another-layout"),
        )
        self.assert_invalid("MemoryLayout/pet-care does not exist")

    def test_rejects_unbound_workflow_memory_alias(self) -> None:
        self.write(
            "workflows/pet/pet-care.yaml",
            PET.replace("memory: pet-care", "memory: missing"),
        )
        self.assert_invalid(
            "memory alias 'missing' is not bound by RuntimeProfile/default"
        )

    def test_rejects_memory_layout_id_that_does_not_match_alias(self) -> None:
        self.write(
            "runtime-profiles/default.yaml",
            PROFILE.replace("layout_id: pet-care", "layout_id: another-layout"),
        )
        self.assert_invalid(
            "layout_id must match its stable memory alias 'pet-care'"
        )

    def test_rejects_wrong_scenario_memory_alias(self) -> None:
        self.write(
            "workflows/pet/pet-care.yaml",
            PET.replace("memory: pet-care", "memory: another-memory"),
        )
        self.write(
            "runtime-profiles/default.yaml",
            PROFILE.replace(
                "pet-care:\n        layout_id: pet-care",
                "another-memory:\n        layout_id: pet-care",
            ),
        )
        self.assert_invalid("Workflow/pet-care.spec.memory must be 'pet-care'")

    def test_rejects_incompatible_memory_driver_and_connection(self) -> None:
        self.write(
            "runtime-profiles/default.yaml",
            PROFILE.replace("driver: flowcraft", "driver: mem0"),
        )
        self.assert_invalid(
            "driver 'mem0' cannot use connection type 'flowcraft_bbh'"
        )

    def test_rejects_unbound_memory_layout_model_alias(self) -> None:
        self.write(
            "memory-layouts/pet-care.yaml",
            MEMORY_LAYOUT.replace("model: asr", "model: missing"),
        )
        self.assert_invalid(
            "MemoryLayout/pet-care: required models alias 'missing' is not bound"
        )

    def test_rejects_memory_layout_without_lane_guidance(self) -> None:
        self.write(
            "memory-layouts/pet-care.yaml",
            MEMORY_LAYOUT.replace(
                "        extract: Extract durable pet facts.",
                "        extract: ''",
            ),
        )
        self.assert_invalid(
            "MemoryLayout/pet-care.spec.flowcraft.lanes.0.extract "
            "must be a non-empty string"
        )

    def test_rejects_memory_layout_with_incomplete_mem0_categories(self) -> None:
        self.write(
            "memory-layouts/pet-care.yaml",
            MEMORY_LAYOUT.replace(
                "    custom_categories:\n      pet-care: Durable pet facts.",
                "    custom_categories: {}",
            ),
        )
        self.assert_invalid(
            "Mem0 categories must exactly match Flowcraft lanes: missing pet-care"
        )

    def test_rejects_memory_layout_with_incomplete_volc_strategy(self) -> None:
        self.write(
            "memory-layouts/pet-care.yaml",
            MEMORY_LAYOUT.replace(
                "custom_instructions: Keep durable pet facts.}",
                "custom_instructions: ''}",
            ),
        )
        self.assert_invalid(
            "MemoryLayout/pet-care.spec.volc_mem0.strategies.0"
            ".custom_instructions must be a non-empty string"
        )

    def test_rejects_legacy_nested_flowcraft_memory(self) -> None:
        self.write(
            "workflows/pet/pet-care.yaml",
            """
            apiVersion: gizclaw.admin/v1alpha1
            kind: Workflow
            metadata:
              name: pet-care
            spec:
              driver: pet
              memory: pet-care
              pet:
                driver: flowcraft
                flowcraft:
                  agent:
                    graph: {}
                  memory: {}
            """,
        )
        with self.assertRaises(CatalogValidationError) as raised:
            validate_catalog(self.root)
        errors = "\n".join(raised.exception.errors)
        self.assertIn("spec.pet.flowcraft.agent is legacy", errors)
        self.assertIn("spec.pet.flowcraft.memory is legacy", errors)

    def test_rejects_memory_graph_without_outer_alias(self) -> None:
        self.write(
            "workflows/pet/pet-care.yaml",
            """
            apiVersion: gizclaw.admin/v1alpha1
            kind: Workflow
            metadata:
              name: pet-care
            spec:
              driver: pet
              pet:
                driver: flowcraft
                flowcraft:
                  graph:
                    name: pet
                    entry: recall
                    nodes:
                      - id: recall
                        type: memory_recall
                        config:
                          query: {text_from: input}
                          output: memory
                          top_k: 1
                    edges:
                      - {from: recall, to: __end__}
            """,
        )
        self.assert_invalid(
            "uses memory graph nodes and must declare outer spec.memory"
        )

    def test_rejects_external_fields_in_public_memory_connection(self) -> None:
        self.write(
            "runtime-profiles/default.yaml",
            PROFILE.replace(
                "type: flowcraft_bbh",
                "type: flowcraft_bbh\n          directory: /tmp/memory",
            ),
        )
        self.assert_invalid("connection has unsupported fields: directory")

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
