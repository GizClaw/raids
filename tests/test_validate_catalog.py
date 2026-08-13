from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

import yaml

from scripts.validate_catalog import (
    PUBLIC_DEFAULT_TOKEN,
    CatalogValidationError,
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

    def test_assistant_enforces_prefix_and_suffix_length_requests(self) -> None:
        workflow = self.load("workflows/flowcraft/chat-assistant.yaml")
        nodes = {
            node["id"]: node
            for node in workflow["spec"]["flowcraft"]["graph"]["nodes"]
        }
        source = nodes["bound_answer"]["config"]["source"]
        self.assertIn("(?:不超过|最多)", source)
        self.assertIn("以内/", source)
        self.assertFalse(nodes["draft_answer"]["publish"])
        self.assertFalse(nodes["observe_conversation"]["config"]["wait_for_completion"])
        memory = self.load("memory-layouts/user-chat-with-assistant.yaml")
        self.assertEqual(memory["spec"]["flowcraft"]["write"]["mode"], "async_semantic")

    def test_murder_is_open_ended_bounded_and_durable(self) -> None:
        workflow = self.load("workflows/flowcraft/murder-mystery.yaml")
        memory = self.load("memory-layouts/adventure.yaml")
        flowcraft = workflow["spec"]["flowcraft"]
        nodes = {node["id"]: node for node in flowcraft["graph"]["nodes"]}
        self.assertEqual(nodes["draft_game_master"]["config"]["max_tokens"], 256)
        self.assertFalse(nodes["draft_game_master"]["publish"])
        self.assertEqual(nodes["answer"]["type"], "script")
        self.assertTrue(nodes["answer"]["publish"])
        self.assertIn('host.emit("token"', nodes["answer"]["config"]["source"])
        self.assertIn(
            ".slice(0, 180)", nodes["bound_game_master"]["config"]["source"]
        )
        self.assertTrue(
            nodes["observe_case"]["config"]["wait_for_completion"]
        )
        prompt = nodes["prepare_game_master"]["config"]["source"]
        self.assertIn("自由调查任何合理地点", prompt)
        self.assertIn("最新明确更正覆盖旧值", prompt)
        self.assertEqual(
            memory["spec"]["flowcraft"]["extraction"]["mode"],
            "single_pass",
        )

    def test_journey_has_one_recall_and_hard_output_budget(self) -> None:
        workflow = self.load("workflows/flowcraft/journey-guide.yaml")
        flowcraft = workflow["spec"]["flowcraft"]
        nodes = {node["id"]: node for node in flowcraft["graph"]["nodes"]}
        self.assertEqual(flowcraft["max_iterations"], 10)
        self.assertEqual(
            [node["id"] for node in flowcraft["graph"]["nodes"] if node["type"] == "memory_recall"],
            ["recall_story"],
        )
        self.assertFalse(nodes["draft_story"]["publish"])
        self.assertIn("journey_progress", nodes["commit_progress"]["config"]["source"])
        self.assertIn("journey_progress_fact", nodes["commit_progress"]["config"]["source"])
        self.assertIn("history", nodes["commit_progress"]["config"]["source"])
        self.assertEqual(
            nodes["recall_story"]["config"]["query"]["lanes"],
            ["story_progress"],
        )
        self.assertEqual(
            nodes["observe_story"]["config"]["observations"][0]["facts"][0]["text_from"],
            "journey_progress_fact",
        )
        self.assertIn(".slice(0, 40)", nodes["bound_story"]["config"]["source"])
        self.assertEqual(nodes["answer"]["type"], "script")
        self.assertTrue(nodes["observe_story"]["config"]["wait_for_completion"])

    def test_pet_graph_has_bounded_iteration_headroom(self) -> None:
        workflow = self.load("workflows/pet/pet-care.yaml")
        flowcraft = workflow["spec"]["pet"]["flowcraft"]
        self.assertEqual(flowcraft["max_iterations"], 11)
        nodes = {node["id"]: node for node in flowcraft["graph"]["nodes"]}
        self.assertFalse(nodes["draft_answer"]["publish"])
        self.assertEqual(nodes["answer"]["type"], "script")
        self.assertFalse(nodes["observe_pet_memory"]["config"]["wait_for_completion"])
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
                    self.assertEqual(turn["first_response"], "12s")
                    self.assertEqual(turn["total_response"], "12s")

    def test_translation_targets_use_language_specific_voices(self) -> None:
        profile = self.load("runtime-profiles/default.yaml")
        voices = profile["spec"]["resources"]["voices"]
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
