from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

import yaml

from scripts.validate_catalog import (
    PUBLIC_DEFAULT_TOKEN,
    CatalogValidationError,
    _validate_default_behavior_contracts,
    _validate_flowcraft_semantics,
    validate_catalog,
)

PROFILE = """
apiVersion: gizclaw.admin/v1alpha1
kind: RuntimeProfile
metadata:
  id: default
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
      pet-care.extract:
        resource_id: extract-model
        i18n:
          en: {display_name: Extraction}
          zh-CN: {display_name: 信息提取}
      pet-care.model:
        resource_id: chat-model
        i18n:
          en: {display_name: Pet Care Model}
          zh-CN: {display_name: 宠物模型}
    voices:
      pet-care.pet:
        resource_id: voice
        i18n:
          en: {display_name: Pet}
          zh-CN: {display_name: 宠物}
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
  id: default-runtime
spec:
  token: {PUBLIC_DEFAULT_TOKEN}
  runtime_profile_id: default
"""

CHATROOM = """
apiVersion: gizclaw.admin/v1alpha1
kind: Workflow
metadata:
  id: chatroom
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
  id: pet-care
spec:
  driver: pet
  memory: pet-care
  pet:
    asr_model: asr
    model: pet-care.model
    voice: pet-care.pet
"""

MEMORY_LAYOUT = """
apiVersion: gizclaw.admin/v1alpha1
kind: MemoryLayout
metadata:
  id: pet-care
spec:
  flowcraft:
    extraction:
      model: pet-care.extract
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
  id: asr-model
spec:
  kind: asr
  source: manual
  provider:
    kind: openai-tenant
    id: openai
  display_name: ASR Model
  provider_data: {}
"""

CREDENTIAL = """
apiVersion: gizclaw.admin/v1alpha1
kind: Credential
metadata:
  id: credential
spec:
  provider: openai
  body: {api_key: test}
"""

TENANT = """
apiVersion: gizclaw.admin/v1alpha1
kind: OpenAITenant
metadata:
  id: openai
spec:
  kind: compatible
  credential_id: credential
  base_url: https://example.com/v1
  api_mode: chat_completions
"""

VOICE = """
apiVersion: gizclaw.admin/v1alpha1
kind: Voice
metadata:
  id: voice
spec:
  source: manual
  provider:
    kind: openai-tenant
    id: openai
  display_name: Test Voice
  provider_data: {}
"""

EXAMPLE = """
apiVersion: gizclaw.admin/v1alpha1
kind: RuntimeProfile
metadata:
  id: raids
spec:
  resources:
    models:
      asr: {}
      pet-care.extract: {}
      pet-care.model: {}
    voices:
      pet-care.pet: {}
"""


class CatalogValidationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.write("runtime-profiles/default.yaml", PROFILE)
        self.write("runtime-profile.example.yaml", EXAMPLE)
        self.write("registration-tokens/default.yaml", TOKEN)
        self.write("workflows/chatroom/social.yaml", CHATROOM)
        self.write("workflows/pet/pet-care.yaml", PET)
        self.write("memory-layouts/pet-care.yaml", MEMORY_LAYOUT)
        self.write("credentials/credential.yaml", CREDENTIAL)
        self.write("tenants/openai.yaml", TENANT)
        self.write("models/asr-model.yaml", MODEL)
        self.write(
            "models/extract-model.yaml",
            MODEL.replace("id: asr-model", "id: extract-model").replace(
                "kind: asr", "kind: llm"
            ),
        )
        self.write(
            "models/chat-model.yaml",
            MODEL.replace("id: asr-model", "id: chat-model").replace(
                "kind: asr", "kind: llm"
            ),
        )
        self.write("voices/openai/voice.yaml", VOICE)

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

    def replace_pet_contract_alias(self, old: str, new: str) -> None:
        self.write("runtime-profiles/default.yaml", PROFILE.replace(old, new))
        self.write("runtime-profile.example.yaml", EXAMPLE.replace(old, new))
        self.write("workflows/pet/pet-care.yaml", PET.replace(old, new))

    def replace_pet_memory_model_alias(self, old: str, new: str) -> None:
        self.write("runtime-profiles/default.yaml", PROFILE.replace(old, new))
        self.write("runtime-profile.example.yaml", EXAMPLE.replace(old, new))
        self.write("memory-layouts/pet-care.yaml", MEMORY_LAYOUT.replace(old, new))

    def test_accepts_complete_default_bootstrap_closure(self) -> None:
        validate_catalog(self.root)

    def test_rejects_flowcraft_iteration_budget_without_headroom(self) -> None:
        errors: list[str] = []
        _validate_flowcraft_semantics(
            {
                "graph": {
                    "entry": "start",
                    "nodes": [
                        {"id": "start", "type": "script"},
                        {"id": "answer", "type": "llm"},
                    ],
                    "edges": [
                        {"from": "start", "to": "answer"},
                        {"from": "answer", "to": "__end__"},
                    ],
                },
                "max_iterations": 2,
            },
            "Workflow/test.spec.flowcraft",
            errors,
        )
        self.assertIn(
            "max_iterations 2 leaves headroom 0 for longest route 2; want 2..8",
            "\n".join(errors),
        )

    def test_rejects_mixed_turn_and_direct_fact_observation(self) -> None:
        errors: list[str] = []
        _validate_flowcraft_semantics(
            {
                "graph": {
                    "entry": "observe",
                    "nodes": [
                        {
                            "id": "observe",
                            "type": "memory_observe",
                            "config": {
                                "observations": [
                                    {"turns_from": "conversation"},
                                    {"facts": [{"text_from": "progress"}]},
                                ]
                            },
                        }
                    ],
                    "edges": [{"from": "observe", "to": "__end__"}],
                },
                "max_iterations": 3,
            },
            "Workflow/test.spec.flowcraft",
            errors,
        )
        self.assertIn(
            "memory_observe node 'observe' must not combine turns_from with "
            "direct facts",
            "\n".join(errors),
        )

    def test_accepts_bounded_cycle_with_exit_route(self) -> None:
        errors: list[str] = []
        _validate_flowcraft_semantics(
            {
                "graph": {
                    "entry": "start",
                    "nodes": [
                        {"id": "start", "type": "script"},
                        {"id": "loop", "type": "script"},
                    ],
                    "edges": [
                        {"from": "start", "to": "loop"},
                        {"from": "loop", "to": "loop"},
                        {"from": "loop", "to": "__end__"},
                    ],
                },
                "max_iterations": 4,
            },
            "Workflow/test.spec.flowcraft",
            errors,
        )
        self.assertEqual(errors, [])

    def test_rejects_wrong_workflow_model_namespace_even_when_bound(self) -> None:
        self.replace_pet_contract_alias("pet-care.model", "another-raid.model")
        self.assert_invalid(
            "Workflow/pet-care: models aliases must match its Workflow-owned contract"
        )

    def test_rejects_unsupported_workflow_voice_role_even_when_bound(self) -> None:
        self.replace_pet_contract_alias("pet-care.pet", "pet-care.narrator")
        self.assert_invalid(
            "Workflow/pet-care: voices aliases must match its Workflow-owned contract"
        )

    def test_rejects_legacy_pet_model_alias_even_when_bound(self) -> None:
        self.replace_pet_contract_alias("pet-care.model", "pet-chat")
        self.assert_invalid(
            "Workflow/pet-care: models aliases must match its Workflow-owned contract"
        )

    def test_rejects_wrong_memory_layout_extraction_namespace_even_when_bound(
        self,
    ) -> None:
        self.replace_pet_memory_model_alias("pet-care.extract", "story-teller.extract")
        self.assert_invalid(
            "MemoryLayout/pet-care: model aliases must match its "
            "MemoryLayout-owned extraction contract"
        )

    def test_rejects_malformed_dotted_alias(self) -> None:
        self.replace_pet_contract_alias("pet-care.model", "pet-care_model")
        self.assert_invalid(
            "must be 1-63 bytes of dot-separated lowercase kebab-case segments"
        )

    def test_rejects_unowned_model_binding(self) -> None:
        extra_binding = """
      unused.model:
        resource_id: chat-model
        i18n:
          en: {display_name: Unused}
          zh-CN: {display_name: 未使用}
"""
        self.write(
            "runtime-profiles/default.yaml",
            PROFILE.replace("    voices:\n", extra_binding + "    voices:\n"),
        )
        self.write(
            "runtime-profile.example.yaml",
            EXAMPLE.replace("    voices:\n", "      unused.model: {}\n    voices:\n"),
        )
        self.assert_invalid(
            "RuntimeProfile/default.spec.resources.models aliases must exactly "
            "match first-party consumers"
        )

    def test_rejects_documentation_example_alias_drift(self) -> None:
        self.write(
            "runtime-profile.example.yaml",
            EXAMPLE.replace("      pet-care.model: {}\n", ""),
        )
        self.assert_invalid(
            "RuntimeProfile/raids documentation example models aliases must "
            "match RuntimeProfile/default"
        )

    def test_rejects_memory_layout_legacy_extraction_alias_even_when_bound(
        self,
    ) -> None:
        self.write(
            "memory-layouts/pet-care.yaml",
            MEMORY_LAYOUT.replace("model: pet-care.extract", "model: extraction"),
        )
        self.write(
            "runtime-profiles/default.yaml",
            PROFILE.replace("      pet-care.extract:\n", "      extraction:\n"),
        )
        self.write(
            "runtime-profile.example.yaml",
            EXAMPLE.replace("      pet-care.extract: {}\n", "      extraction: {}\n"),
        )
        self.assert_invalid(
            "MemoryLayout/pet-care: model aliases must match its "
            "MemoryLayout-owned extraction contract"
        )

    def test_public_default_token_uuidv5_derivation_is_stable(self) -> None:
        self.assertEqual(
            PUBLIC_DEFAULT_TOKEN,
            "28c4e4e9-a05f-5a7e-815e-9cf9afb6878f",
        )

    def test_rejects_missing_resource_reference(self) -> None:
        self.write(
            "models/asr-model.yaml",
            MODEL.replace("id: asr-model", "id: another-model"),
        )
        self.assert_invalid("references missing Model/asr-model")

    def test_rejects_missing_metadata_id(self) -> None:
        self.write(
            "models/asr-model.yaml",
            MODEL.replace("  id: asr-model\n", ""),
        )
        self.assert_invalid(
            "models/asr-model.yaml: metadata.id must be a non-empty string"
        )

    def test_rejects_empty_metadata_id(self) -> None:
        self.write(
            "models/asr-model.yaml",
            MODEL.replace("  id: asr-model", "  id: ''"),
        )
        self.assert_invalid(
            "models/asr-model.yaml: metadata.id must be a non-empty string"
        )

    def test_rejects_metadata_id_with_surrounding_whitespace(self) -> None:
        self.write(
            "models/asr-model.yaml",
            MODEL.replace("  id: asr-model", '  id: " asr-model "'),
        )
        self.assert_invalid("metadata.id must not have surrounding whitespace")

    def test_rejects_metadata_id_over_character_limit(self) -> None:
        self.write(
            "models/asr-model.yaml",
            MODEL.replace("  id: asr-model", f"  id: {'a' * 1025}"),
        )
        self.assert_invalid("metadata.id exceeds the 1024-character limit")

    def test_rejects_metadata_id_uri_dot_segments(self) -> None:
        for resource_id in (".", ".."):
            with self.subTest(resource_id=resource_id):
                self.write(
                    "models/asr-model.yaml",
                    MODEL.replace("  id: asr-model", f"  id: {resource_id}"),
                )
                self.assert_invalid("metadata.id must not be a URI dot segment")

    def test_rejects_legacy_metadata_name(self) -> None:
        self.write(
            "models/asr-model.yaml",
            MODEL.replace("  id: asr-model", "  id: asr-model\n  name: legacy"),
        )
        self.assert_invalid("models/asr-model.yaml: metadata.name is legacy")

    def test_rejects_environment_dependent_metadata_id(self) -> None:
        self.write(
            "models/asr-model.yaml",
            MODEL.replace("  id: asr-model", "  id: ${MODEL_ID}"),
        )
        self.assert_invalid("models/asr-model.yaml: metadata.id must be concrete")

    def test_rejects_environment_dependent_resource_reference(self) -> None:
        self.write(
            "tenants/openai.yaml",
            TENANT.replace(
                "credential_id: credential", "credential_id: ${CREDENTIAL_ID}"
            ),
        )
        self.assert_invalid("credential_id must be a concrete Credential ID")

    def test_rejects_resource_reference_with_surrounding_whitespace(self) -> None:
        self.write(
            "tenants/openai.yaml",
            TENANT.replace(
                "credential_id: credential", 'credential_id: " credential "'
            ),
        )
        self.assert_invalid(
            "credential_id must not have surrounding whitespace in the Credential ID"
        )

    def test_rejects_resource_reference_over_character_limit(self) -> None:
        self.write(
            "tenants/openai.yaml",
            TENANT.replace("credential_id: credential", f"credential_id: {'a' * 1025}"),
        )
        self.assert_invalid("exceeds the 1024-character Credential ID limit")

    def test_rejects_resource_reference_uri_dot_segments(self) -> None:
        for resource_id in (".", ".."):
            with self.subTest(resource_id=resource_id):
                self.write(
                    "tenants/openai.yaml",
                    TENANT.replace(
                        "credential_id: credential", f"credential_id: {resource_id}"
                    ),
                )
                self.assert_invalid("credential_id must not be a URI dot segment")

    def test_rejects_missing_documentation_example(self) -> None:
        (self.root / "runtime-profile.example.yaml").unlink()
        self.assert_invalid("required documentation example is missing")

    def test_rejects_legacy_name_in_documentation_example(self) -> None:
        self.write(
            "runtime-profile.example.yaml",
            """
            apiVersion: gizclaw.admin/v1alpha1
            kind: RuntimeProfile
            metadata:
              name: raids
            spec: {}
            """,
        )
        self.assert_invalid("runtime-profile.example.yaml: metadata.name is legacy")

    def test_rejects_ambiguous_duplicate_resource(self) -> None:
        self.write("models/duplicate.yaml", MODEL)
        self.assert_invalid("ambiguous duplicate Model/asr-model")

    def test_rejects_legacy_tenant_credential_name(self) -> None:
        self.write(
            "tenants/openai.yaml",
            TENANT.replace("credential_id: credential", "credential_name: credential"),
        )
        self.assert_invalid("spec.credential_name is legacy")

    def test_rejects_missing_tenant_credential_reference(self) -> None:
        self.write(
            "tenants/openai.yaml",
            TENANT.replace("credential_id: credential", "credential_id: missing"),
        )
        self.assert_invalid("references missing Credential/missing")

    def test_rejects_wrong_kind_tenant_credential_reference(self) -> None:
        self.write(
            "tenants/openai.yaml",
            TENANT.replace("credential_id: credential", "credential_id: asr-model"),
        )
        self.assert_invalid(
            "references Credential/asr-model, but asr-model is defined as Model"
        )

    def test_rejects_empty_tenant_credential_reference(self) -> None:
        self.write(
            "tenants/openai.yaml",
            TENANT.replace("credential_id: credential", "credential_id: ''"),
        )
        self.assert_invalid("credential_id must be a non-empty Credential ID")

    def test_rejects_legacy_model_provider_name(self) -> None:
        self.write(
            "models/asr-model.yaml",
            MODEL.replace("    id: openai", "    name: openai"),
        )
        self.assert_invalid("spec.provider.name is legacy")

    def test_rejects_legacy_model_display_name(self) -> None:
        self.write(
            "models/asr-model.yaml",
            MODEL.replace("  display_name: ASR Model", "  name: ASR Model"),
        )
        self.assert_invalid("Model/asr-model.spec.name is legacy")

    def test_rejects_legacy_voice_fields(self) -> None:
        self.write(
            "voices/openai/voice.yaml",
            VOICE.replace("    id: openai", "    name: openai").replace(
                "  display_name: Test Voice", "  name: Test Voice"
            ),
        )
        self.assert_invalid("Voice/voice.spec.provider.name is legacy")
        self.assert_invalid("Voice/voice.spec.name is legacy")

    def test_rejects_unbound_workflow_alias(self) -> None:
        self.write(
            "workflows/chatroom/social.yaml",
            CHATROOM.replace("asr_model: asr", "asr_model: missing"),
        )
        self.assert_invalid("required models alias 'missing' is not bound")

    def test_rejects_missing_memory_layout(self) -> None:
        self.write(
            "memory-layouts/pet-care.yaml",
            MEMORY_LAYOUT.replace("id: pet-care", "id: another-layout"),
        )
        self.assert_invalid(
            "references MemoryLayout/pet-care, but pet-care is defined as Workflow"
        )

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
        self.assert_invalid("layout_id must match its stable memory alias 'pet-care'")

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
        self.assert_invalid("driver 'mem0' cannot use connection type 'flowcraft_bbh'")

    def test_rejects_unbound_memory_layout_model_alias(self) -> None:
        self.write(
            "memory-layouts/pet-care.yaml",
            MEMORY_LAYOUT.replace("model: pet-care.extract", "model: missing"),
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
              id: pet-care
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
              id: pet-care
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
            TOKEN.replace("id: default-runtime", "id: other"),
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
                    TOKEN.replace("id: default-runtime", "id: other").replace(
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
                other = TOKEN.replace("id: default-runtime", "id: other").replace(
                    f"  token: {PUBLIC_DEFAULT_TOKEN}\n", token_line
                )
                self.write("registration-tokens/other.yaml", other)
                self.assert_invalid(
                    "RegistrationToken/other.spec.token must be a non-empty string"
                )

    def test_rejects_registration_token_with_missing_profile(self) -> None:
        self.write(
            "registration-tokens/other.yaml",
            TOKEN.replace("id: default-runtime", "id: other")
            .replace(f"token: {PUBLIC_DEFAULT_TOKEN}", "token: other")
            .replace("runtime_profile_id: default", "runtime_profile_id: missing"),
        )
        self.assert_invalid(
            "RegistrationToken/other.spec.runtime_profile_id references "
            "missing RuntimeProfile/missing"
        )

    def test_rejects_legacy_registration_token_profile_name(self) -> None:
        self.write(
            "registration-tokens/default.yaml",
            TOKEN.replace(
                "runtime_profile_id: default", "runtime_profile_name: default"
            ),
        )
        self.assert_invalid("spec.runtime_profile_name is legacy")

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


class PublicDefaultE2ERegressionTest(unittest.TestCase):
    root = Path(__file__).resolve().parents[1]

    def load(self, relative: str) -> dict[str, object]:
        document = yaml.safe_load((self.root / relative).read_text(encoding="utf-8"))
        self.assertIsInstance(document, dict)
        return document

    def default_behavior_errors(self, *, max_tokens: int = 2048, answer_source: str = '') -> list[str]:
        if not answer_source:
            answer_source = (
                'const answer = String(board.getVar("tmp_answer") || "").trim();\n'
                'host.emit("token", {content: answer});'
            )
        workflow = {
            "spec": {
                "driver": "flowcraft",
                "flowcraft": {
                    "graph": {
                        "nodes": [
                            {
                                "id": "prompt",
                                "type": "script",
                                "config": {"source": "never rely on programmatic truncation"},
                            },
                            {
                                "id": "draft",
                                "type": "llm",
                                "publish": False,
                                "config": {"max_tokens": max_tokens},
                            },
                            {
                                "id": "answer",
                                "type": "script",
                                "publish": True,
                                "config": {"source": answer_source},
                            },
                            {
                                "id": "observe",
                                "type": "memory_observe",
                                "config": {"wait_for_completion": False},
                            },
                        ]
                    }
                },
            }
        }
        errors: list[str] = []
        _validate_default_behavior_contracts(
            {}, {("Workflow", "flowcraft-chat-assistant"): workflow}, errors
        )
        return errors

    def test_default_behavior_rejects_small_generation_budget(self) -> None:
        errors = self.default_behavior_errors(max_tokens=512)
        self.assertIn("must reserve at least 1024 max_tokens", "\n".join(errors))

    def test_default_behavior_rejects_generated_reply_truncation(self) -> None:
        errors = self.default_behavior_errors(
            answer_source=(
                'const raw = String(board.getVar("tmp_answer") || "");\n'
                'const answer = Array.from(raw).slice(0, 80).join("");\n'
                'host.emit("token", {content: answer});'
            )
        )
        self.assertIn("must not truncate a generated reply", "\n".join(errors))

    def test_assistant_prompts_for_complete_bounded_replies_without_truncation(self) -> None:
        workflow = self.load("workflows/flowcraft/chat-assistant.yaml")
        nodes = {
            node["id"]: node
            for node in workflow["spec"]["flowcraft"]["graph"]["nodes"]
        }
        self.assertEqual(nodes["draft_answer"]["config"]["max_tokens"], 2048)
        self.assertNotIn("bound_answer", nodes)
        self.assertFalse(nodes["draft_answer"]["publish"])
        self.assertFalse(nodes["observe_conversation"]["config"]["wait_for_completion"])
        prompt = nodes["style_prompt"]["config"]["source"]
        self.assertIn("explicitly repeat every new or replacement value", prompt)
        self.assertIn("without offering reminders, asking confirmation", prompt)
        self.assertIn("never end with a question or Chinese question particles", prompt)
        self.assertIn("Never format spoken facts as separate lines", prompt)
        self.assertIn("never rely on programmatic truncation", prompt)
        self.assertNotIn(".slice(0,", nodes["answer"]["config"]["source"])
        memory = self.load("memory-layouts/user-chat-with-assistant.yaml")
        self.assertEqual(memory["spec"]["flowcraft"]["write"]["mode"], "async_semantic")

    def test_murder_is_open_ended_complete_and_durable(self) -> None:
        workflow = self.load("workflows/flowcraft/murder-mystery.yaml")
        tester = self.load("workflows/eino/tests/flowcraft-murder-mystery_test.yaml")
        memory = self.load("memory-layouts/adventure.yaml")
        flowcraft = workflow["spec"]["flowcraft"]
        nodes = {node["id"]: node for node in flowcraft["graph"]["nodes"]}
        self.assertEqual(nodes["draft_game_master"]["config"]["max_tokens"], 2048)
        self.assertFalse(nodes["draft_game_master"]["publish"])
        self.assertNotIn("bound_game_master", nodes)
        self.assertEqual(nodes["answer"]["type"], "script")
        self.assertTrue(nodes["answer"]["publish"])
        self.assertIn('host.emit("token"', nodes["answer"]["config"]["source"])
        self.assertEqual(flowcraft["max_iterations"], 10)
        self.assertNotIn("observe_case_turns", nodes)
        self.assertFalse(nodes["observe_case_state"]["config"]["wait_for_completion"])
        self.assertEqual(
            nodes["observe_case_state"]["config"]["observations"][0]["facts"][0]["text_from"],
            "case_visible_state_fact",
        )
        self.assertIn("raid_case_visible_state_v1", nodes["prepare_case_state"]["config"]["source"])
        self.assertIn("same_source_shoe_size", nodes["prepare_case_state"]["config"]["source"])
        self.assertEqual(
            [edge for edge in flowcraft["graph"]["edges"] if edge["from"] == "prepare_case_state"],
            [{"from": "prepare_case_state", "to": "observe_case_state"}],
        )
        prompt = nodes["prepare_game_master"]["config"]["source"]
        self.assertIn("自由调查任何合理地点", prompt)
        self.assertIn("最新明确更正覆盖旧值", prompt)
        self.assertIn("严禁临时发明", prompt)
        self.assertIn("私密真相只供主持人维持一致", prompt)
        self.assertIn("最关键的四至五项", prompt)
        self.assertIn("花园水池和围墙只确认无关键痕迹", prompt)
        self.assertIn("必须逐项回答", prompt)
        self.assertIn("一律用第三人称转述", prompt)
        self.assertIn("不得用‘我’冒充被采访者", prompt)
        self.assertIn("对话第一轮无论玩家", prompt)
        self.assertIn("21:10至21:12停电", prompt)
        self.assertIn("20:50开始在后厨揉面", prompt)
        self.assertIn("留声机只用于声音和时间误导", prompt)
        self.assertIn("严禁声称唱盘拉线锁门", prompt)
        self.assertIn("固定案情不可漂移", prompt)
        self.assertIn("固定可见来源表不可混用", prompt)
        self.assertIn("后门内锁且无撬动、木蜡或细线", prompt)
        self.assertIn("周围灰尘无异常且附近无其他物品", prompt)
        self.assertIn("只有玩家明确寻找线、纤维或拉扯痕迹时", prompt)
        self.assertIn("区分证据关联和证词矛盾", prompt)
        self.assertIn("不得虚构他否认木蜡", prompt)
        self.assertIn("调查后廊前不得把鞋印称为后廊鞋印", prompt)
        self.assertIn("后廊鞋印本身不得称为同源", prompt)
        self.assertIn("不得补充感情好坏、公开矛盾", prompt)
        self.assertIn("不得判断后廊是否连通阳台、厨房、卧室", prompt)
        self.assertIn("不得声称没有连接其他区域的痕迹", prompt)
        self.assertIn("必须先明确回答已确认连通书房与门厅", prompt)
        self.assertIn("不得含糊改写成无法判断是否连通此前调查过的区域", prompt)
        self.assertIn("任何理论评估、复盘或其他回复都不得提书房锁具细线纤维", prompt)
        self.assertIn("严禁概括成所有、全部、其他物证或其他证词都与厨师证词一致", prompt)
        self.assertIn("阳台地面没有固定检查结果", prompt)
        self.assertIn("即使调查后也只能写特征一致，不得升级为匹配或同源", prompt)
        self.assertIn("此时正值雨夜", prompt)
        self.assertIn("不得补写没有其他异常、没有其他痕迹、异常痕迹", prompt)
        self.assertIn("不得组合成‘主钥匙备用钥匙’", prompt)
        self.assertIn("无关来源不得用来支持厨师证词", prompt)
        self.assertIn('latest.includes("厨师")', prompt)
        self.assertIn("本轮是厨房证词核对，优先执行", prompt)
        self.assertIn("禁止写‘没有其他线索能印证或反驳’", prompt)
        self.assertIn("死者当晚活动物品没有固定检查结果", prompt)
        self.assertIn("不得声称没有其他能印证或反驳厨师证词的线索", prompt)
        self.assertIn("首次报告用确认，不得称为更正", prompt)
        self.assertIn("不得在律师受访前声称律师已经证实", prompt)
        self.assertIn("不得把窗框只有木蜡", prompt)
        self.assertIn("管家不知道壁炉内另有备用钥匙", prompt)
        self.assertIn("这些结果与厨师证词一致、没有矛盾", prompt)
        self.assertIn("唱针停在磨损对应位置", prompt)
        self.assertIn("不得编造比例或数额", prompt)
        self.assertIn("细线不得声称同批、同源或匹配", prompt)
        self.assertIn("后来明确调查锁具纤维时", prompt)
        self.assertIn("严格只写三句且总共不超过130个字符", prompt)
        self.assertIn("不得依赖程序截断", prompt)
        self.assertIn("约80至320个Unicode字符", prompt)
        self.assertIn("可以写到480个字符", prompt)
        self.assertNotIn("每次回复不超过180个字符", prompt)
        self.assertIn("不得用‘我查看了’‘我检查了’冒充玩家", prompt)
        self.assertIn("不得在任何检查末尾追加", prompt)
        self.assertIn("管家没有固定证词", prompt)
        self.assertIn("不得添加侦探身份、受邀、报案、赶到现场、发现者、进入或开门方式", prompt)
        self.assertIn("不得添加落叶、泥土、雨水、攀爬、翻越", prompt)
        self.assertIn("都必须逐字且只输出以下三句", prompt)
        self.assertIn("你可以自由调查任何感兴趣的地点、物品或相关人物", prompt)
        self.assertIn("鞋柜有39码湿雨靴", prompt)
        tester_prompt = next(
            message["template"]
            for node in tester["spec"]["eino"]["graph"]["nodes"]
            if node["id"] == "prepare-judge"
            for message in node["messages"]
            if message["role"] == "system"
        )
        self.assertIn(
            "请开始主持《雨夜留声机》，只给出初始案情和自由调查邀请。",
            tester_prompt,
        )
        self.assertIn("不得把预期的主持人开场当成玩家台词", tester_prompt)
        self.assertIn("在 challenge-chef，只能判定厨房挂钟和后门检查与厨师证词一致", tester_prompt)
        self.assertIn("必须将 factuality 与 instruction_following 判 fail", tester_prompt)
        self.assertEqual(
            memory["spec"]["flowcraft"]["extraction"]["mode"],
            "single_pass",
        )
        self.assertEqual(
            memory["spec"]["flowcraft"]["write"]["mode"],
            "async_semantic",
        )

    def test_journey_has_one_recall_and_complete_scene_budget(self) -> None:
        workflow = self.load("workflows/flowcraft/journey-guide.yaml")
        flowcraft = workflow["spec"]["flowcraft"]
        nodes = {node["id"]: node for node in flowcraft["graph"]["nodes"]}
        self.assertEqual(nodes["draft_story"]["config"]["max_tokens"], 2048)
        self.assertEqual(flowcraft["max_iterations"], 10)
        self.assertEqual(
            [node["id"] for node in flowcraft["graph"]["nodes"] if node["type"] == "memory_recall"],
            ["recall_story"],
        )
        self.assertFalse(nodes["draft_story"]["publish"])
        self.assertNotIn("bound_story", nodes)
        self.assertIn("journey_progress", nodes["commit_progress"]["config"]["source"])
        self.assertIn("journey_progress_fact", nodes["commit_progress"]["config"]["source"])
        self.assertIn("history", nodes["commit_progress"]["config"]["source"])
        self.assertIn("始终用第二人称", nodes["prepare_story"]["config"]["source"])
        self.assertIn("同样不得推进场景、替玩家调查", nodes["prepare_story"]["config"]["source"])
        self.assertIn("不得把两个此前没有建立关系的事件倒填成确定因果", nodes["prepare_story"]["config"]["source"])
        self.assertIn("完整的场景段落", nodes["prepare_story"]["config"]["source"])
        self.assertIn("约100至260个Unicode字符", nodes["prepare_story"]["config"]["source"])
        self.assertIn("复杂的连续动作可以写到360个字符", nodes["prepare_story"]["config"]["source"])
        self.assertNotIn("每次回复最多40个Unicode字符", nodes["prepare_story"]["config"]["source"])
        self.assertIn("不得出现‘不对’‘重新来’", nodes["prepare_story"]["config"]["source"])
        self.assertIn("不能停在‘准备’‘将要’‘找到人’或‘快完成’", nodes["prepare_story"]["config"]["source"])
        self.assertIn("不得越过用户明确要求的停止点", nodes["prepare_story"]["config"]["source"])
        self.assertIn("后续相关行动必须保留姓名‘明月’", nodes["prepare_story"]["config"]["source"])
        self.assertIn("不得因为这些规则举例提到‘明月’或‘清禾’就提前引入", nodes["prepare_story"]["config"]["source"])
        self.assertIn("事实建立、纠正或纯回忆回合只直接回答用户要求", nodes["prepare_story"]["config"]["source"])
        self.assertIn("先完整回答每项事实，再自然承接当前场景", nodes["prepare_story"]["config"]["source"])
        self.assertEqual(
            nodes["recall_story"]["config"]["query"]["lanes"],
            ["story_progress"],
        )
        self.assertEqual(
            nodes["observe_story"]["config"]["observations"][0]["facts"][0]["text_from"],
            "journey_progress_fact",
        )
        self.assertIn("不得依赖程序截断", nodes["prepare_story"]["config"]["source"])
        self.assertNotIn(".slice(0,", nodes["answer"]["config"]["source"])
        self.assertEqual(nodes["answer"]["type"], "script")
        self.assertFalse(nodes["observe_story"]["config"]["wait_for_completion"])
        memory = self.load("memory-layouts/story-teller.yaml")
        self.assertEqual(memory["spec"]["flowcraft"]["write"]["mode"], "async_semantic")

    def test_paired_story_workflows_keep_distinct_prompts_and_equal_budgets(self) -> None:
        scenarios = {
            "story-aesop": ("乌龟和小鸟同时发现了一颗种子", "第三章‘合作照料’"),
            "story-alice": ("一只戴着两块表的兔子", "第三章‘绿色小门’"),
            "adventure-space-rescue": ("一艘科研飞船失去动力", "第三阶段‘准备安全会合’"),
            "adventure-monster-maze": ("迷宫门上有月亮、星星和太阳三个按钮", "第四区‘怪兽合作’"),
            "adventure-castle-mystery": ("城堡钟楼在午夜提前响了", "第三阶段‘竞争假设’"),
        }
        corrected_facts = {
            "story-aesop": "乌龟先吃一点现有食物再和小鸟一起照料幼苗",
            "story-alice": "password=茶杯向右",
            "adventure-space-rescue": "coordinate=B-21",
            "adventure-monster-maze": "marker_color=蓝色",
            "adventure-castle-mystery": "footprint_size=39码",
        }
        prompts: set[str] = set()
        for scenario, (opening, durable_checkpoint) in scenarios.items():
            with self.subTest(scenario=scenario):
                flowcraft = self.load(f"workflows/flowcraft/{scenario}.yaml")
                eino = self.load(f"workflows/eino/{scenario}.yaml")
                flow_nodes = {
                    node["id"]: node
                    for node in flowcraft["spec"]["flowcraft"]["graph"]["nodes"]
                }
                eino_nodes = {
                    node["id"]: node
                    for node in eino["spec"]["eino"]["graph"]["nodes"]
                }
                flow_route = flow_nodes["route-phase"]["config"]["source"]
                flow_narrators = [
                    node for node in flow_nodes.values() if node["type"] == "llm"
                ]
                flow_contract = flow_route + "\n" + "\n".join(
                    node["config"]["system_prompt"] for node in flow_narrators
                )
                narrator_prompts = [
                    node
                    for node in eino_nodes.values()
                    if node["type"] == "prompt" and "route" in node.get("inputs", {})
                ]
                self.assertEqual(len(narrator_prompts), 5)
                eino_prompt = "\n".join(
                    node["messages"][0]["template"] for node in narrator_prompts
                )
                route_nodes = [
                    node
                    for node in eino_nodes.values()
                    if node["type"] == "script" and node["id"].startswith("route-")
                ]
                self.assertEqual(len(route_nodes), 1)
                eino_contract = route_nodes[0]["source"] + "\n" + eino_prompt
                self.assertIn(opening, flow_contract)
                self.assertIn(opening, eino_contract)
                for recall_marker in ("重连", "隔了几轮"):
                    self.assertIn(recall_marker, flow_route)
                    self.assertIn(recall_marker, route_nodes[0]["source"])
                if scenario == "adventure-space-rescue":
                    self.assertIn(
                        "首句就必须逐字同时包含“备用电池”和“安全窗口”",
                        eino_contract,
                    )
                self.assertNotIn(eino_contract, prompts)
                prompts.add(eino_contract)
                self.assertEqual(len(flow_narrators), 5)
                self.assertTrue(
                    all(node["config"]["max_tokens"] == 2048 for node in flow_narrators)
                )
                self.assertTrue(all(node["publish"] for node in flow_narrators))
                self.assertTrue(
                    all(node["config"]["output_key"] == "tmp_answer" for node in flow_narrators)
                )
                model_nodes = [
                    node for node in eino_nodes.values() if node["type"] == "chat_model"
                ]
                # The deterministic route script owns chapter/stage planning;
                # only the narrator calls the model so the graph is not a
                # latency-heavy 2-pass chain.
                self.assertEqual(len(model_nodes), 1)
                self.assertTrue(all(node["max_tokens"] == 2048 for node in model_nodes))
                self.assertEqual(
                    eino["spec"]["memory"],
                    "story-teller" if scenario.startswith("story-") else "adventure",
                )
                node_types = {node["type"] for node in eino_nodes.values()}
                self.assertTrue(
                    {"script", "memory_recall", "prompt", "chat_model", "memory_observe"}
                    <= node_types
                )
                self.assertIn(durable_checkpoint, route_nodes[0]["source"])
                self.assertTrue(
                    all("route" in node["inputs"] for node in narrator_prompts)
                )
                branches = eino["spec"]["eino"]["graph"]["branches"]
                self.assertEqual(len(branches), 1)
                self.assertEqual(branches[0]["mode"], "first_match")
                self.assertEqual(len(branches[0]["routes"]), 4)
                self.assertEqual(branches[0]["default"], "prompt-explore")
                self.assertFalse(any(node_id.startswith("plan-") for node_id in eino_nodes))
                self.assertGreaterEqual(
                    eino["spec"]["eino"]["graph"]["compile"]["max_run_steps"], 16
                )
                observe = next(
                    node
                    for node in eino_nodes.values()
                    if node["type"] == "memory_observe"
                )
                # Persist progress without delaying the completed voice reply. The
                # following turn remains protected by injected history while the
                # long-term memory provider finishes asynchronously.
                self.assertFalse(observe["wait_for_completion"])
                self.assertEqual(
                    observe["facts"][0]["attributes"],
                    {"lane": "progress-lane", "kind": "progress-kind"},
                )
                commit = eino_nodes["commit-progress"]
                self.assertIn('"kind": "state"', commit["source"])
                self.assertIn('input["phase"] == "correction"', commit["source"])
                self.assertIn("correction_authority=latest_user_value", commit["source"])
                self.assertIn(corrected_facts[scenario], commit["source"])
                self.assertNotIn("latest_answer", commit["source"])
                self.assertEqual(
                    eino["spec"]["eino"]["graph"]["outputs"][0]["node"],
                    "narrator-model",
                )
                self.assertEqual(
                    flowcraft["spec"]["flowcraft"]["conversation"]["starts"],
                    "agent",
                )
                self.assertEqual(
                    flowcraft["spec"]["memory"],
                    "story-teller" if scenario.startswith("story-") else "adventure",
                )
                self.assertEqual(flowcraft["spec"]["flowcraft"]["max_iterations"], 10)
                self.assertEqual(
                    {node["type"] for node in flow_nodes.values()},
                    {"memory_recall", "script", "llm", "memory_observe"},
                )
                self.assertNotIn("answer", flow_nodes)
                for narrator in flow_narrators:
                    self.assertIn(
                        {"from": narrator["id"], "to": "reduce-state"},
                        flowcraft["spec"]["flowcraft"]["graph"]["edges"],
                    )
                self.assertIn("Array.isArray(message.parts)", flow_route)
                reducer = flow_nodes["reduce-state"]["config"]["source"]
                self.assertIn('phase === "correction"', reducer)
                self.assertIn("delete next.last_input", reducer)
                self.assertIn("next.last_correction", reducer)
                self.assertNotIn("next.turn", reducer)
                self.assertNotIn("last_answer", reducer)
                self.assertEqual(
                    eino["spec"]["eino"]["conversation"]["starts"], "peer"
                )
                self.assertIn("voice_adapter", flowcraft["spec"]["flowcraft"])
                self.assertIn(
                    "default_voice", flowcraft["spec"]["flowcraft"]["voice_adapter"]
                )
                self.assertIn("不得依赖程序截断", flow_contract)

        for relative in (
            "tools/raidtest/plans/benchmarks/story-aesop-comparison.yaml",
            "tools/raidtest/plans/benchmarks/story-alice-comparison.yaml",
            "tools/raidtest/plans/benchmarks/adventure-space-rescue-comparison.yaml",
            "tools/raidtest/plans/benchmarks/adventure-monster-maze-comparison.yaml",
            "tools/raidtest/plans/benchmarks/adventure-castle-mystery-comparison.yaml",
        ):
            plan = self.load(relative)
            self.assertEqual(plan["driver"], "scripted-comparison")
            self.assertTrue(plan["paired"])
            self.assertNotIn("persona", plan)
            turns = plan["cases"][0]["turns"]
            # Agent-start workflows contribute a formal opening before the first
            # simulated user message, so it is a separately judged checkpoint.
            self.assertEqual(len(turns), 13)
            self.assertTrue(all(turn["first_response"] == "6s" for turn in turns))
            self.assertEqual(turns[0]["id"], "opening")
            self.assertTrue(
                all(
                    key not in turn
                    for turn in turns
                    for key in ("user", "intent", "judge")
                )
            )
            reloads = [turn for turn in turns if turn.get("reload_before")]
            self.assertEqual(len(reloads), 1)

        aesop_turns = self.load(
            "tools/raidtest/plans/benchmarks/story-aesop-comparison.yaml"
        )["cases"][0]["turns"]
        growth = next(turn for turn in aesop_turns if turn["id"] == "recall-growth-time")
        self.assertEqual(
            growth["required_any"],
            [["幼苗", "幼芽", "小芽", "种子", "发芽"], ["天", "日"]],
        )
        maze_turns = self.load(
            "tools/raidtest/plans/benchmarks/adventure-monster-maze-comparison.yaml"
        )["cases"][0]["turns"]
        route = next(turn for turn in maze_turns if turn["id"] == "establish-route")
        self.assertIn("左手边", route["required_any"][0])
        theory = next(turn for turn in maze_turns if turn["id"] == "uncertain-theory")
        self.assertNotIn("一定知道", theory["forbidden"])
        rescue_turns = self.load(
            "tools/raidtest/plans/benchmarks/adventure-space-rescue-comparison.yaml"
        )["cases"][0]["turns"]
        communications = next(
            turn for turn in rescue_turns if turn["id"] == "restore-communications"
        )
        self.assertEqual(communications["required"], ["科研飞船"])
        self.assertEqual(
            communications["required_any"], [["通信", "天线", "收到", "传回"]]
        )

    def test_pr61_workflows_have_independent_eino_testers_and_testing_profile(self) -> None:
        targets = {
            "eino-adventure-castle-mystery",
            "eino-adventure-monster-maze",
            "eino-adventure-space-rescue",
            "eino-journey-history",
            "eino-journey-memory-async",
            "eino-journey-memory-recall",
            "eino-story-aesop",
            "eino-story-alice",
            "flowcraft-adventure-castle-mystery",
            "flowcraft-adventure-monster-maze",
            "flowcraft-adventure-space-rescue",
            "flowcraft-story-aesop",
            "flowcraft-story-alice",
            "flowcraft-murder-mystery",
        }
        prompts: set[str] = set()
        for target in targets:
            with self.subTest(target=target):
                tester = self.load(f"workflows/eino/tests/{target}_test.yaml")
                self.assertEqual(tester["metadata"]["id"], f"{target}-test")
                self.assertEqual(tester["spec"]["driver"], "eino")
                self.assertEqual(
                    tester["spec"]["toolkit"]["tool_ids"],
                    ["raidtest-acceptance-report"],
                )
                graph = tester["spec"]["eino"]["graph"]
                self.assertEqual(
                    tester["spec"]["eino"]["conversation"]["starts"], "peer"
                )
                model = next(
                    node for node in graph["nodes"] if node["type"] == "chat_model"
                )
                self.assertEqual(model["model"], f"{target}-test.model")
                self.assertGreaterEqual(model["max_tokens"], 1024)
                prompt_nodes = [
                    node for node in graph["nodes"] if node["type"] == "prompt"
                ]
                is_story_pair = "journey" not in target and target != "flowcraft-murder-mystery"
                if is_story_pair:
                    self.assertEqual(len(prompt_nodes), 6)
                    router = next(
                        node for node in graph["nodes"] if node["id"] == "route-checkpoint"
                    )
                    self.assertIn("raidtest-acceptance-report", router["source"])
                    self.assertIn("next_message", router["source"])
                    self.assertIn("evidence", router["source"])
                    self.assertIn("负向控制", router["source"])
                    self.assertGreaterEqual(router["source"].count("必须 fail"), 2)
                    self.assertNotIn(router["source"], prompts)
                    prompts.add(router["source"])
                    self.assertEqual(len(graph["branches"]), 1)
                    self.assertEqual(graph["branches"][0]["mode"], "first_match")
                    self.assertEqual(graph["branches"][0]["default"], "prompt-evidence")
                    self.assertEqual(len(graph["branches"][0]["routes"]), 5)
                    self.assertEqual(
                        {node["id"] for node in prompt_nodes},
                        {
                            "prompt-bootstrap",
                            "prompt-evidence",
                            "prompt-correction",
                            "prompt-challenge",
                            "prompt-conclusion",
                            "prompt-retry",
                        },
                    )
                    for prompt_node in prompt_nodes:
                        self.assertEqual(
                            prompt_node["messages"][1],
                            {"role": "user", "template": "{payload}"},
                        )
                        self.assertEqual(
                            set(prompt_node["inputs"]),
                            {"payload", "rules", "checkpoint", "contract", "next_message"},
                        )
                    self.assertNotIn("12轮", router["source"])
                else:
                    self.assertEqual(len(prompt_nodes), 1)
                    prompt_node = prompt_nodes[0]
                    self.assertEqual(
                        prompt_node["inputs"], {"payload": {"from": "input.text"}}
                    )
                    self.assertEqual(
                        prompt_node["messages"][1],
                        {"role": "user", "template": "{payload}"},
                    )
                    prompt = prompt_node["messages"][0]["template"]
                    self.assertIn("raidtest-acceptance-report", prompt)
                    self.assertIn("next_message", prompt)
                    self.assertIn("evidence", prompt)
                    self.assertNotIn(prompt, prompts)
                    prompts.add(prompt)

        testing = self.load("runtime-profiles/testing.yaml")["spec"]
        target_bindings = testing["workflows"]["collections"]["raidtest-targets"]
        tester_bindings = testing["workflows"]["collections"]["raidtest-testers"]
        self.assertEqual(
            {binding["resource_id"] for binding in target_bindings.values()}, targets
        )
        self.assertEqual(
            {binding["resource_id"] for binding in tester_bindings.values()},
            {f"{target}-test" for target in targets},
        )
        self.assertEqual(
            testing["resources"]["tools"]["raidtest-acceptance-report"]["resource_id"],
            "raidtest-acceptance-report",
        )
        self.assertIn("adventure.space-rescue", testing["workflows"]["collections"]["adventure"])
        self.assertNotIn("adventure.space_rescue", testing["workflows"]["collections"]["adventure"])

        default = self.load("runtime-profiles/default.yaml")["spec"]
        self.assertIn("adventure.space_rescue", default["workflows"]["collections"]["adventure"])
        token = self.load("registration-tokens/testing.yaml")
        self.assertEqual(token["metadata"]["id"], "testing-runtime")
        self.assertEqual(token["spec"]["runtime_profile_id"], "testing")
        tool = self.load("tool-resources/raidtest-acceptance-report.yaml")
        self.assertEqual(tool["spec"]["type"], "client_rpc")
        self.assertEqual(tool["spec"]["invoke_name"], "raidtest_acceptance_report")
        check_schema = tool["spec"]["input_schema"]["properties"]["checks"]["items"]
        self.assertIn("evidence", check_schema["required"])

        suite = self.load("tools/raidtest/suites/pr61-paired.yaml")
        self.assertEqual(suite["schema_version"], "raidtest.suite/v1")
        self.assertEqual(len(suite["pairs"]), 14)
        self.assertEqual(
            {pair["target_workflow_id"] for pair in suite["pairs"]}, targets
        )
        for pair in suite["pairs"]:
            target = self.load(pair["target_workflow_file"])
            self.assertEqual(target["spec"]["toolkit"]["tool_ids"], [])
            if "journey" not in pair["target_workflow_id"] and pair["target_workflow_id"] != "flowcraft-murder-mystery":
                self.assertEqual(pair["repeats"], 3)
        murder = next(
            pair
            for pair in suite["pairs"]
            if pair["target_workflow_id"] == "flowcraft-murder-mystery"
        )
        self.assertEqual(murder["expected_target_responses"], 26)
        self.assertEqual(murder["repeats"], 5)
        self.assertEqual(murder["reloads"][0]["before_response"], 20)


    def test_new_story_bindings_match_their_issue_contracts(self) -> None:
        profile = self.load("runtime-profiles/default.yaml")["spec"]["workflows"]["collections"]
        expected = {
            ("story-teller", "story.aesop"): (
                "flowcraft-story-aesop",
                "伊索寓言",
                "Aesop's Fables",
            ),
            ("story-teller", "story.alice"): (
                "flowcraft-story-alice",
                "爱丽丝梦游仙境",
                "Alice in Wonderland",
            ),
            ("adventure", "adventure.space_rescue"): (
                "flowcraft-adventure-space-rescue",
                "宇宙救援",
                "Space Rescue",
            ),
            ("adventure", "adventure.monster_maze"): (
                "flowcraft-adventure-monster-maze",
                "怪兽迷宫",
                "Monster Maze",
            ),
            ("adventure", "adventure.castle_mystery"): (
                "flowcraft-adventure-castle-mystery",
                "城堡谜案",
                "Castle Mystery",
            ),
        }
        for (collection, alias), (resource_id, zh_name, en_name) in expected.items():
            with self.subTest(alias=alias):
                binding = profile[collection][alias]
                self.assertEqual(binding["resource_id"], resource_id)
                self.assertEqual(binding["i18n"]["zh-CN"]["display_name"], zh_name)
                self.assertEqual(binding["i18n"]["en"]["display_name"], en_name)
                self.assertTrue(binding["i18n"]["zh-CN"]["description"])
                self.assertTrue(binding["i18n"]["en"]["description"])

        for alias, resource_id in (
            ("adventure.space_rescue-eino", "eino-adventure-space-rescue"),
            ("adventure.monster_maze-eino", "eino-adventure-monster-maze"),
            ("adventure.castle_mystery-eino", "eino-adventure-castle-mystery"),
        ):
            with self.subTest(alias=alias):
                self.assertEqual(profile["adventure"][alias]["resource_id"], resource_id)

    def test_pet_graph_has_bounded_iteration_headroom(self) -> None:
        workflow = self.load("workflows/pet/pet-care.yaml")
        flowcraft = workflow["spec"]["pet"]["flowcraft"]
        self.assertEqual(flowcraft["max_iterations"], 13)
        nodes = {node["id"]: node for node in flowcraft["graph"]["nodes"]}
        self.assertFalse(nodes["draft_answer"]["publish"])
        self.assertEqual(nodes["draft_answer"]["config"]["max_tokens"], 2048)
        self.assertNotIn("bound_answer", nodes)
        self.assertEqual(nodes["answer"]["type"], "script")
        self.assertFalse(nodes["observe_pet_memory"]["config"]["wait_for_completion"])
        self.assertFalse(nodes["observe_pet_state"]["config"]["wait_for_completion"])
        self.assertIn("raid_pet_durable_state_v1", nodes["prepare_pet_state"]["config"]["source"])
        self.assertIn("pet_durable_state_fact", nodes["prepare_pet_state"]["config"]["source"])
        self.assertEqual(
            nodes["observe_pet_state"]["config"]["observations"][0]["facts"][0]["text_from"],
            "pet_durable_state_fact",
        )
        pet_prompt = nodes["prepare_pet_context"]["config"]["source"]
        self.assertIn("acknowledge every named person, pet, place, object, and time", pet_prompt)
        self.assertIn("Do not invent touching, chasing, licking", pet_prompt)
        self.assertIn("never describe a paw as a hand", pet_prompt)
        self.assertIn("explicitly repeat its time and place", pet_prompt)
        self.assertIn("never rely on programmatic truncation", pet_prompt)
        self.assertIn("Never include a draft, self-correction, wrong intermediate value", pet_prompt)
        self.assertNotIn(".slice(0,", nodes["answer"]["config"]["source"])
        memory = self.load("memory-layouts/pet-care.yaml")
        self.assertEqual(memory["spec"]["flowcraft"]["write"]["mode"], "async_semantic")

    def test_history_backed_plans_enforce_non_blocking_turn_budgets(self) -> None:
        for relative in (
            "tools/raidtest/plans/default/assistant-general.yaml",
            "tools/raidtest/plans/default/pet-care.yaml",
        ):
            plan = self.load(relative)
            for case in plan["cases"]:
                for turn in case["turns"]:
                    self.assertEqual(turn["first_response"], "6s")
                    self.assertEqual(turn["total_response"], "12s")

        journey = self.load("tools/raidtest/plans/default/journey.yaml")
        for case in journey["cases"]:
            for turn in case["turns"]:
                self.assertEqual(turn["first_response"], "6s")
                self.assertEqual(turn["total_response"], "90s")

    def test_translation_targets_use_language_specific_voices(self) -> None:
        profile = self.load("runtime-profiles/default.yaml")
        voices = profile["spec"]["resources"]["voices"]
        self.assertEqual(
            voices["ast-translate-zh-en-auto.translator"]["resource_id"],
            "volc-tenant:volc-cn-beijing:zh_female_sophie_conversation_wvae_bigtts",
        )
        self.assertEqual(
            voices["ast-translate-zh-ja.translator"]["resource_id"],
            "minimax-tenant:minimax-cn:Japanese_CalmLady",
        )
        self.assertEqual(
            voices["ast-translate-zh-ko.translator"]["resource_id"],
            "minimax-tenant:minimax-cn:Korean_CalmLady",
        )
        self.assertEqual(
            voices["ast-translate-zh-es.translator"]["resource_id"],
            "minimax-tenant:minimax-cn:Spanish_SereneElder",
        )
        self.assertEqual(
            voices["ast-translate-zh-fr.translator"]["resource_id"],
            "minimax-tenant:minimax-cn:French_MovieLeadFemale",
        )

    def test_default_adoption_pool_preserves_external_pixa_contract(self) -> None:
        profile = self.load("runtime-profiles/default.yaml")
        pool = profile["spec"]["gameplay"]["adoption"]["pool"]
        self.assertEqual(len(pool), 9)
        self.assertEqual(
            {entry["pet_def"] for entry in pool},
            {
                "bsod",
                "codex",
                "dewey",
                "fireball",
                "hoots",
                "null-signal",
                "rocky",
                "seedy",
                "stacky",
            },
        )


class MiniMaxProviderContractRegressionTest(unittest.TestCase):
    root = Path(__file__).resolve().parents[1]

    def load(self, relative: str) -> dict[str, object]:
        document = yaml.safe_load((self.root / relative).read_text(encoding="utf-8"))
        self.assertIsInstance(document, dict)
        return document

    def test_tenants_do_not_require_app_ids(self) -> None:
        expected_specs = {
            "minimax-cn": {
                "group_id": "${GIZCLAW_MINIMAX_CN_GROUP_ID}",
                "credential_id": "minimax-cn-credential",
                "base_url": "https://api.minimaxi.com",
                "description": "MiniMax CN tenant",
            },
            "minimax-global": {
                "group_id": "${GIZCLAW_MINIMAX_GLOBAL_GROUP_ID}",
                "credential_id": "minimax-global-credential",
                "base_url": "https://api.minimax.io",
                "description": "MiniMax Global tenant",
            },
        }
        for tenant_id, expected_spec in expected_specs.items():
            with self.subTest(tenant_id=tenant_id):
                tenant = self.load(f"tenants/{tenant_id}.yaml")
                self.assertEqual(tenant["spec"], expected_spec)

        environment = (self.root / ".env.example").read_text(encoding="utf-8")
        for variable in (
            "GIZCLAW_MINIMAX_CN_APP_ID",
            "GIZCLAW_MINIMAX_GLOBAL_APP_ID",
        ):
            self.assertNotIn(variable, environment)
        for variable in (
            "GIZCLAW_MINIMAX_CN_API_KEY",
            "GIZCLAW_MINIMAX_CN_GROUP_ID",
            "GIZCLAW_MINIMAX_GLOBAL_API_KEY",
            "GIZCLAW_MINIMAX_GLOBAL_GROUP_ID",
        ):
            self.assertIn(f"{variable}=", environment)


if __name__ == "__main__":
    unittest.main()
