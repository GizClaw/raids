#!/usr/bin/env python3
"""Validate Raids catalog syntax and the public default bootstrap closure."""

from __future__ import annotations

import argparse
import re
import uuid
from collections import defaultdict
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import yaml

API_VERSION = "gizclaw.admin/v1alpha1"
MAX_RESOURCE_ID_CHARACTERS = 1024
PUBLIC_DEFAULT_TOKEN_NAMESPACE_URL = (
    "https://github.com/GizClaw/raids/registration-tokens"
)
PUBLIC_DEFAULT_TOKEN_NAME = "default-runtime/v1"
PUBLIC_DEFAULT_TOKEN_NAMESPACE = uuid.uuid5(
    uuid.NAMESPACE_URL, PUBLIC_DEFAULT_TOKEN_NAMESPACE_URL
)
PUBLIC_DEFAULT_TOKEN = str(
    uuid.uuid5(PUBLIC_DEFAULT_TOKEN_NAMESPACE, PUBLIC_DEFAULT_TOKEN_NAME)
)
CATALOG_DIRECTORIES = {
    "credentials",
    "memory-layouts",
    "models",
    "petdefs",
    "registration-tokens",
    "runtime-profiles",
    "tenants",
    "voices",
    "workflows",
}
RESOURCE_KINDS = {
    "models": "Model",
    "voices": "Voice",
    "tools": "Tool",
    "pet_defs": "PetDef",
    "game_defs": "GameDef",
    "badge_defs": "BadgeDef",
}
TENANT_KINDS = {
    "DashScopeTenant",
    "DeepSeekTenant",
    "GeminiTenant",
    "MiniMaxTenant",
    "OpenAITenant",
    "VolcTenant",
}
PROVIDER_RESOURCE_KINDS = {
    "dashscope-tenant": "DashScopeTenant",
    "deepseek-tenant": "DeepSeekTenant",
    "gemini-tenant": "GeminiTenant",
    "minimax-tenant": "MiniMaxTenant",
    "openai-tenant": "OpenAITenant",
    "volc-tenant": "VolcTenant",
}
RUNTIME_ALIAS_PATTERN = re.compile(
    r"^[a-z0-9]+(?:-[a-z0-9]+)*(?:\.[a-z0-9]+(?:-[a-z0-9]+)*)*$"
)
MAX_RUNTIME_ALIAS_BYTES = 63
WORKFLOW_MODEL_ALIASES = {
    "ast-translate-ja-zh": {"ast-translate-ja-zh.model"},
    "ast-translate-ko-zh": {"ast-translate-ko-zh.model"},
    "ast-translate-zh-en-auto": {"ast-translate-zh-en-auto.model"},
    "ast-translate-zh-es": {"ast-translate-zh-es.model"},
    "ast-translate-zh-fr": {"ast-translate-zh-fr.model"},
    "ast-translate-zh-ja": {"ast-translate-zh-ja.model"},
    "ast-translate-zh-ko": {"ast-translate-zh-ko.model"},
    "chatroom": {"asr"},
    "doubao-realtime-conversation": {"doubao-realtime-conversation.model"},
    "flowcraft-chat-assistant": {"asr", "flowcraft-chat-assistant.model"},
    "flowcraft-journey-guide": {"asr", "flowcraft-journey-guide.model"},
    "flowcraft-murder-mystery": {"asr", "flowcraft-murder-mystery.model"},
    "pet-care": {"asr", "pet-care.model"},
}
WORKFLOW_VOICE_ALIASES = {
    "ast-translate-ja-zh": {"ast-translate-ja-zh.translator"},
    "ast-translate-ko-zh": {"ast-translate-ko-zh.translator"},
    "ast-translate-zh-en-auto": {"ast-translate-zh-en-auto.translator"},
    "ast-translate-zh-es": {"ast-translate-zh-es.translator"},
    "ast-translate-zh-fr": {"ast-translate-zh-fr.translator"},
    "ast-translate-zh-ja": {"ast-translate-zh-ja.translator"},
    "ast-translate-zh-ko": {"ast-translate-zh-ko.translator"},
    "chatroom": set(),
    "doubao-realtime-conversation": {"doubao-realtime-conversation.assistant"},
    "flowcraft-chat-assistant": {"flowcraft-chat-assistant.assistant"},
    "flowcraft-journey-guide": {
        "flowcraft-journey-guide.arrival-narrator",
        "flowcraft-journey-guide.heaven-narrator",
        "flowcraft-journey-guide.kingdoms-narrator",
        "flowcraft-journey-guide.narrator",
        "flowcraft-journey-guide.origin-narrator",
        "flowcraft-journey-guide.pilgrimage-narrator",
        "flowcraft-journey-guide.trials-narrator",
    },
    "flowcraft-murder-mystery": {
        "flowcraft-murder-mystery.detective",
        "flowcraft-murder-mystery.game-master",
    },
    "pet-care": {"pet-care.pet"},
}
MEMORY_LAYOUT_MODEL_ALIASES = {
    "adventure": {"adventure.extract"},
    "pet-care": {"pet-care.extract"},
    "story-teller": {"story-teller.extract"},
    "user-chat-with-assistant": {"user-chat-with-assistant.extract"},
}
MEMORY_CONNECTIONS = {
    "flowcraft_bbh": {
        "driver": "flowcraft",
        "required": {"type"},
        "optional": set(),
    },
    "flowcraft_object_store": {
        "driver": "flowcraft",
        "required": {"type", "directory"},
        "optional": set(),
    },
    "flowcraft_postgresql": {
        "driver": "flowcraft",
        "required": {"type", "dsn"},
        "optional": set(),
    },
    "mem0": {
        "driver": "mem0",
        "required": {"type", "project_id", "endpoint", "api_key"},
        "optional": {"poll_interval"},
    },
    "volc_mem0": {
        "driver": "volc_mem0",
        "required": {"type", "memory_project_id", "endpoint", "api_key"},
        "optional": {"poll_interval"},
    },
}
DEFAULT_WORKFLOW_MEMORY_ALIASES = {
    "flowcraft-chat-assistant": "user-chat-with-assistant",
    "flowcraft-journey-guide": "story-teller",
    "flowcraft-murder-mystery": "adventure",
    "pet-care": "pet-care",
}
PLACEHOLDER_PATTERN = re.compile(r"<[^>]+>|\$\{[^}]+\}")
GO_TRIM_SPACE_CHARACTERS = (
    "\t\n\v\f\r \u0085\u00a0\u1680"
    "\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a"
    "\u2028\u2029\u202f\u205f\u3000"
)
PROHIBITED_DEFAULT_KEYS = {
    "cloud_region",
    "endpoint",
    "environment",
    "environment_name",
    "firmware_id",
    "node_address",
    "private_key",
    "server_address",
}


class CatalogValidationError(Exception):
    """Raised when one or more catalog invariants fail."""

    def __init__(self, errors: Iterable[str]):
        self.errors = tuple(errors)
        super().__init__("\n".join(self.errors))


def _yaml_paths(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix in {".yaml", ".yml"}
        and ".git" not in path.parts
    )


def _load_yaml(path: Path, root: Path, errors: list[str]) -> list[Any]:
    relative = path.relative_to(root)
    try:
        with path.open(encoding="utf-8") as stream:
            return list(yaml.safe_load_all(stream))
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        errors.append(f"{relative}: {error}")
        return []


def _resource_identity(
    document: Any, relative: Path, errors: list[str]
) -> tuple[str, str] | None:
    if not isinstance(document, Mapping):
        errors.append(f"{relative}: catalog document must be a mapping")
        return None
    if document.get("apiVersion") != API_VERSION:
        errors.append(f"{relative}: apiVersion must be {API_VERSION}")
    kind = document.get("kind")
    metadata = document.get("metadata")
    resource_id = metadata.get("id") if isinstance(metadata, Mapping) else None
    if not isinstance(kind, str) or not kind:
        errors.append(f"{relative}: kind must be a non-empty string")
    if not isinstance(resource_id, str) or not resource_id.strip():
        errors.append(f"{relative}: metadata.id must be a non-empty string")
    elif resource_id != resource_id.strip():
        errors.append(f"{relative}: metadata.id must not have surrounding whitespace")
    elif len(resource_id) > MAX_RESOURCE_ID_CHARACTERS:
        errors.append(
            f"{relative}: metadata.id exceeds the "
            f"{MAX_RESOURCE_ID_CHARACTERS}-character limit"
        )
    elif resource_id in {".", ".."}:
        errors.append(f"{relative}: metadata.id must not be a URI dot segment")
    elif PLACEHOLDER_PATTERN.search(resource_id):
        errors.append(f"{relative}: metadata.id must be concrete")
    if isinstance(metadata, Mapping) and "name" in metadata:
        errors.append(f"{relative}: metadata.name is legacy and must not be used")
    if (
        not isinstance(kind, str)
        or not kind
        or not isinstance(resource_id, str)
        or not resource_id.strip()
    ):
        return None
    return kind, resource_id


def _walk(
    value: Any, path: tuple[str, ...] = ()
) -> Iterable[tuple[tuple[str, ...], Any]]:
    yield path, value
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield from _walk(child, (*path, str(key)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, (*path, str(index)))


def _validate_public_values(
    document: Mapping[str, Any], relative: Path, errors: list[str]
) -> None:
    for path, value in _walk(document):
        if path and path[-1] in PROHIBITED_DEFAULT_KEYS:
            errors.append(f"{relative}: prohibited default field {'.'.join(path)}")
        if isinstance(value, str) and PLACEHOLDER_PATTERN.search(value):
            errors.append(f"{relative}: unresolved placeholder at {'.'.join(path)}")


def _require_mapping(value: Any, label: str, errors: list[str]) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    errors.append(f"{label} must be a mapping")
    return {}


def _validate_catalog_reference(
    value: Any,
    label: str,
    resource_kind: str,
    resources: Mapping[tuple[str, str], Path],
    errors: list[str],
) -> str | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label} must be a non-empty {resource_kind} ID")
        return None
    if value != value.strip():
        errors.append(
            f"{label} must not have surrounding whitespace in the {resource_kind} ID"
        )
        return value
    if len(value) > MAX_RESOURCE_ID_CHARACTERS:
        errors.append(
            f"{label} exceeds the {MAX_RESOURCE_ID_CHARACTERS}-character "
            f"{resource_kind} ID limit"
        )
        return value
    if value in {".", ".."}:
        errors.append(f"{label} must not be a URI dot segment")
        return value
    if PLACEHOLDER_PATTERN.search(value):
        errors.append(f"{label} must be a concrete {resource_kind} ID")
        return value
    if (resource_kind, value) in resources:
        return value
    other_kinds = sorted(
        kind for kind, resource_id in resources if resource_id == value
    )
    if other_kinds:
        errors.append(
            f"{label} references {resource_kind}/{value}, but {value} is defined "
            f"as {', '.join(other_kinds)}"
        )
    else:
        errors.append(f"{label} references missing {resource_kind}/{value}")
    return value


def _reject_legacy_field(
    object_: Mapping[str, Any], field: str, label: str, errors: list[str]
) -> None:
    if field in object_:
        errors.append(f"{label}.{field} is legacy and must not be used")


def _validate_current_resource_shape(
    kind: str,
    resource_id: str,
    document: Mapping[str, Any],
    relative: Path,
    resources: Mapping[tuple[str, str], Path],
    errors: list[str],
) -> None:
    spec = _require_mapping(
        document.get("spec"), f"{relative}: {kind}/{resource_id}.spec", errors
    )
    label = f"{relative}: {kind}/{resource_id}.spec"

    if kind in TENANT_KINDS:
        _reject_legacy_field(spec, "credential_name", label, errors)
        _validate_catalog_reference(
            spec.get("credential_id"),
            f"{label}.credential_id",
            "Credential",
            resources,
            errors,
        )
        return

    if kind in {"Model", "Voice"}:
        provider = _require_mapping(spec.get("provider"), f"{label}.provider", errors)
        _reject_legacy_field(provider, "name", f"{label}.provider", errors)
        provider_kind = provider.get("kind")
        if not isinstance(provider_kind, str) or not provider_kind:
            errors.append(f"{label}.provider.kind must be a non-empty string")
        else:
            resource_kind = PROVIDER_RESOURCE_KINDS.get(provider_kind)
            if resource_kind is None:
                errors.append(
                    f"{label}.provider.kind {provider_kind!r} is not supported"
                )
            else:
                _validate_catalog_reference(
                    provider.get("id"),
                    f"{label}.provider.id",
                    resource_kind,
                    resources,
                    errors,
                )
        _reject_legacy_field(spec, "name", label, errors)
        display_name = spec.get("display_name")
        if not isinstance(display_name, str) or not display_name.strip():
            errors.append(f"{label}.display_name must be a non-empty string")
        return

    if kind == "RegistrationToken":
        _reject_legacy_field(spec, "runtime_profile_name", label, errors)
        _validate_catalog_reference(
            spec.get("runtime_profile_id"),
            f"{label}.runtime_profile_id",
            "RuntimeProfile",
            resources,
            errors,
        )


def _validate_binding(
    binding: Any,
    label: str,
    resource_kind: str,
    resources: Mapping[tuple[str, str], Path],
    errors: list[str],
) -> str | None:
    binding = _require_mapping(binding, label, errors)
    resource_id = binding.get("resource_id")
    _validate_catalog_reference(
        resource_id,
        f"{label}.resource_id",
        resource_kind,
        resources,
        errors,
    )
    i18n = _require_mapping(binding.get("i18n"), f"{label}.i18n", errors)
    for locale in ("en", "zh-CN"):
        text = _require_mapping(i18n.get(locale), f"{label}.i18n.{locale}", errors)
        if not isinstance(text.get("display_name"), str) or not text["display_name"]:
            errors.append(f"{label}.i18n.{locale}.display_name must be non-empty")
    return resource_id if isinstance(resource_id, str) and resource_id else None


def _selected_workflows(
    profile: Mapping[str, Any],
    resources: Mapping[tuple[str, str], Path],
    errors: list[str],
) -> set[str]:
    spec = _require_mapping(profile.get("spec"), "RuntimeProfile/default.spec", errors)
    workflows = _require_mapping(
        spec.get("workflows"), "RuntimeProfile/default.spec.workflows", errors
    )
    system = _require_mapping(
        workflows.get("system"), "RuntimeProfile/default.spec.workflows.system", errors
    )
    expected_system = {
        "friend_chatroom": "chatroom",
        "group_chatroom": "chatroom",
        "pet": "pet-care",
    }
    if dict(system) != expected_system:
        errors.append(
            "RuntimeProfile/default.spec.workflows.system must bind "
            "friend_chatroom and group_chatroom to chatroom and pet to pet-care"
        )
    selected = {value for value in system.values() if isinstance(value, str) and value}
    collections = _require_mapping(
        workflows.get("collections"),
        "RuntimeProfile/default.spec.workflows.collections",
        errors,
    )
    for collection_name, collection in collections.items():
        collection = _require_mapping(
            collection,
            f"RuntimeProfile/default.spec.workflows.collections.{collection_name}",
            errors,
        )
        for alias, binding in collection.items():
            resource_id = _validate_binding(
                binding,
                (
                    "RuntimeProfile/default.spec.workflows.collections."
                    f"{collection_name}.{alias}"
                ),
                "Workflow",
                resources,
                errors,
            )
            if resource_id:
                selected.add(resource_id)
    for resource_id in selected:
        if ("Workflow", resource_id) not in resources:
            errors.append(
                f"RuntimeProfile/default: Workflow/{resource_id} does not exist"
            )
    return selected


def _profile_aliases(
    profile: Mapping[str, Any],
    resources: Mapping[tuple[str, str], Path],
    errors: list[str],
) -> dict[str, set[str]]:
    spec = _require_mapping(profile.get("spec"), "RuntimeProfile/default.spec", errors)
    groups = _require_mapping(
        spec.get("resources"), "RuntimeProfile/default.spec.resources", errors
    )
    aliases: dict[str, set[str]] = defaultdict(set)
    for group, resource_kind in RESOURCE_KINDS.items():
        bindings = groups.get(group, {})
        bindings = _require_mapping(
            bindings, f"RuntimeProfile/default.spec.resources.{group}", errors
        )
        for alias, binding in bindings.items():
            alias = str(alias)
            _validate_runtime_alias(
                alias,
                f"RuntimeProfile/default.spec.resources.{group} alias",
                errors,
            )
            aliases[group].add(alias)
            _validate_binding(
                binding,
                f"RuntimeProfile/default.spec.resources.{group}.{alias}",
                resource_kind,
                resources,
                errors,
            )
    return aliases


def _validate_runtime_alias(alias: str, label: str, errors: list[str]) -> None:
    if len(
        alias.encode("utf-8")
    ) > MAX_RUNTIME_ALIAS_BYTES or not RUNTIME_ALIAS_PATTERN.fullmatch(alias):
        errors.append(
            f"{label} {alias!r} must be 1-63 bytes of dot-separated "
            "lowercase kebab-case segments"
        )


def _profile_alias_key_sets(
    profile: Mapping[str, Any], label: str, errors: list[str]
) -> dict[str, set[str]]:
    spec = _require_mapping(profile.get("spec"), f"{label}.spec", errors)
    resources = _require_mapping(
        spec.get("resources"), f"{label}.spec.resources", errors
    )
    aliases: dict[str, set[str]] = {}
    for group in ("models", "voices"):
        bindings = _require_mapping(
            resources.get(group), f"{label}.spec.resources.{group}", errors
        )
        aliases[group] = {str(alias) for alias in bindings}
        for alias in sorted(aliases[group]):
            _validate_runtime_alias(
                alias, f"{label}.spec.resources.{group} alias", errors
            )
    return aliases


def _profile_memory_bindings(
    profile: Mapping[str, Any],
    resources: Mapping[tuple[str, str], Path],
    errors: list[str],
) -> dict[str, str]:
    spec = _require_mapping(profile.get("spec"), "RuntimeProfile/default.spec", errors)
    groups = _require_mapping(
        spec.get("resources"), "RuntimeProfile/default.spec.resources", errors
    )
    memories = _require_mapping(
        groups.get("memories"),
        "RuntimeProfile/default.spec.resources.memories",
        errors,
    )
    bindings: dict[str, str] = {}
    for raw_alias, raw_binding in memories.items():
        alias = str(raw_alias)
        label = f"RuntimeProfile/default.spec.resources.memories.{alias}"
        binding = _require_mapping(raw_binding, label, errors)
        expected_binding_keys = {"layout_id", "driver", "connection"}
        if set(binding) != expected_binding_keys:
            errors.append(
                f"{label} must contain exactly layout_id, driver, and connection"
            )
        layout_id = binding.get("layout_id")
        if not isinstance(layout_id, str) or not layout_id:
            errors.append(f"{label}.layout_id must be a non-empty string")
        else:
            bindings[alias] = layout_id
            if layout_id != alias:
                errors.append(
                    f"{label}.layout_id must match its stable memory alias {alias!r}"
                )
            _validate_catalog_reference(
                layout_id,
                f"{label}.layout_id",
                "MemoryLayout",
                resources,
                errors,
            )
        driver = binding.get("driver")
        if driver not in {"flowcraft", "mem0", "volc_mem0"}:
            errors.append(f"{label}.driver must be flowcraft, mem0, or volc_mem0")
        connection = _require_mapping(
            binding.get("connection"), f"{label}.connection", errors
        )
        connection_type = connection.get("type")
        contract = MEMORY_CONNECTIONS.get(connection_type)
        if contract is None:
            errors.append(f"{label}.connection.type is not supported")
            continue
        if driver != contract["driver"]:
            errors.append(
                f"{label}: driver {driver!r} cannot use connection "
                f"type {connection_type!r}"
            )
        allowed = contract["required"] | contract["optional"]
        missing = contract["required"] - set(connection)
        extra = set(connection) - allowed
        if missing:
            errors.append(
                f"{label}.connection is missing required fields: "
                + ", ".join(sorted(missing))
            )
        if extra:
            errors.append(
                f"{label}.connection has unsupported fields: "
                + ", ".join(sorted(extra))
            )
        for key in allowed - {"type"}:
            if key in connection and (
                not isinstance(connection[key], str) or not connection[key]
            ):
                errors.append(f"{label}.connection.{key} must be a non-empty string")
        if driver != "flowcraft" or dict(connection) != {"type": "flowcraft_bbh"}:
            errors.append(
                f"{label} must use the portable public flowcraft_bbh connection "
                "without external connection fields"
            )
    return bindings


def _string_values_for_keys(value: Any, keys: set[str]) -> set[str]:
    found: set[str] = set()
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key in keys and isinstance(child, str) and child:
                found.add(child)
            found.update(_string_values_for_keys(child, keys))
    elif isinstance(value, list):
        for child in value:
            found.update(_string_values_for_keys(child, keys))
    return found


def _workflow_aliases(workflow: Mapping[str, Any]) -> dict[str, set[str]]:
    spec = workflow.get("spec")
    if not isinstance(spec, Mapping):
        return {"models": set(), "voices": set()}
    models = _string_values_for_keys(spec, {"asr_model", "model", "translation_model"})
    voices = _string_values_for_keys(spec, {"default_voice", "tts_voice", "voice"})
    for path, value in _walk(spec):
        if path and path[-1] == "node_voices" and isinstance(value, Mapping):
            voices.update(
                item for item in value.values() if isinstance(item, str) and item
            )
    return {"models": models, "voices": voices}


def _validate_flowcraft_shape(flowcraft: Any, label: str, errors: list[str]) -> bool:
    flowcraft = _require_mapping(flowcraft, label, errors)
    if "agent" in flowcraft:
        errors.append(f"{label}.agent is legacy; graph must be flattened")
    if "memory" in flowcraft:
        errors.append(f"{label}.memory is legacy; use outer Workflow spec.memory")
    if not isinstance(flowcraft.get("graph"), Mapping):
        errors.append(f"{label}.graph must be a mapping")
        return False
    return any(
        isinstance(node, Mapping)
        and node.get("type") in {"memory_recall", "memory_observe"}
        for node in flowcraft["graph"].get("nodes", [])
    )


def _validate_workflow_shape(
    workflow_id: str, workflow: Mapping[str, Any], errors: list[str]
) -> None:
    spec = _require_mapping(
        workflow.get("spec"), f"Workflow/{workflow_id}.spec", errors
    )
    driver = spec.get("driver")
    uses_memory = False
    if driver == "flowcraft":
        uses_memory = _validate_flowcraft_shape(
            spec.get("flowcraft"), f"Workflow/{workflow_id}.spec.flowcraft", errors
        )
    if driver == "pet":
        pet = _require_mapping(
            spec.get("pet"), f"Workflow/{workflow_id}.spec.pet", errors
        )
        if "memory" in pet:
            errors.append(
                f"Workflow/{workflow_id}.spec.pet.memory is invalid; "
                "the outer Workflow owns spec.memory"
            )
        if pet.get("driver") == "flowcraft":
            uses_memory = _validate_flowcraft_shape(
                pet.get("flowcraft"),
                f"Workflow/{workflow_id}.spec.pet.flowcraft",
                errors,
            )
    if uses_memory and (not isinstance(spec.get("memory"), str) or not spec["memory"]):
        errors.append(
            f"Workflow/{workflow_id} uses memory graph nodes and must declare "
            "outer spec.memory"
        )


def _memory_layout_model_aliases(layout: Mapping[str, Any]) -> set[str]:
    spec = layout.get("spec")
    if not isinstance(spec, Mapping):
        return set()
    flowcraft = spec.get("flowcraft")
    if not isinstance(flowcraft, Mapping):
        return set()
    aliases: set[str] = set()
    for policy_name in ("extraction", "embedding", "rerank"):
        policy = flowcraft.get(policy_name)
        if not isinstance(policy, Mapping):
            continue
        model = policy.get("model")
        if isinstance(model, str) and model:
            aliases.add(model)
    return aliases


def _validate_memory_layout_policy(
    layout_id: str, layout: Mapping[str, Any], errors: list[str]
) -> None:
    label = f"MemoryLayout/{layout_id}.spec"
    spec = _require_mapping(layout.get("spec"), label, errors)
    flowcraft = _require_mapping(spec.get("flowcraft"), f"{label}.flowcraft", errors)
    raw_lanes = flowcraft.get("lanes")
    if not isinstance(raw_lanes, list) or not raw_lanes:
        errors.append(f"{label}.flowcraft.lanes must be a non-empty list")
        raw_lanes = []
    lane_names: set[str] = set()
    for index, raw_lane in enumerate(raw_lanes):
        lane_label = f"{label}.flowcraft.lanes.{index}"
        lane = _require_mapping(raw_lane, lane_label, errors)
        lane_name = lane.get("name")
        if not isinstance(lane_name, str) or not lane_name.strip():
            errors.append(f"{lane_label}.name must be a non-empty string")
        else:
            normalized_lane_name = lane_name.strip()
            if normalized_lane_name in lane_names:
                errors.append(
                    f"{label}.flowcraft.lanes contains duplicate "
                    f"{normalized_lane_name!r}"
                )
            else:
                lane_names.add(normalized_lane_name)
        for field in ("description", "extract", "recall"):
            value = lane.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{lane_label}.{field} must be a non-empty string")

    mem0 = _require_mapping(spec.get("mem0"), f"{label}.mem0", errors)
    instructions = mem0.get("custom_instructions")
    if not isinstance(instructions, str) or not instructions.strip():
        errors.append(f"{label}.mem0.custom_instructions must be a non-empty string")
    categories = _require_mapping(
        mem0.get("custom_categories"), f"{label}.mem0.custom_categories", errors
    )
    category_names: set[str] = set()
    for raw_name, raw_description in categories.items():
        category_name = str(raw_name).strip()
        if category_name in category_names:
            errors.append(
                f"{label}.mem0.custom_categories contains duplicate {category_name!r}"
            )
        else:
            category_names.add(category_name)
        if not isinstance(raw_description, str) or not raw_description.strip():
            errors.append(
                f"{label}.mem0.custom_categories.{category_name} "
                "must be a non-empty string"
            )
    if category_names != lane_names:
        errors.append(
            f"{label}: Mem0 categories must exactly match Flowcraft lanes"
            + _set_difference_details(lane_names, category_names)
        )

    volc_mem0 = _require_mapping(spec.get("volc_mem0"), f"{label}.volc_mem0", errors)
    raw_strategies = volc_mem0.get("strategies")
    if not isinstance(raw_strategies, list) or not raw_strategies:
        errors.append(f"{label}.volc_mem0.strategies must be a non-empty list")
        raw_strategies = []
    strategy_names: set[str] = set()
    for index, raw_strategy in enumerate(raw_strategies):
        strategy_label = f"{label}.volc_mem0.strategies.{index}"
        strategy = _require_mapping(raw_strategy, strategy_label, errors)
        strategy_name = strategy.get("name")
        if not isinstance(strategy_name, str) or not strategy_name.strip():
            errors.append(f"{strategy_label}.name must be a non-empty string")
        else:
            normalized_strategy_name = strategy_name.strip()
            if normalized_strategy_name in strategy_names:
                errors.append(
                    f"{label}.volc_mem0.strategies contains duplicate "
                    f"{normalized_strategy_name!r}"
                )
            else:
                strategy_names.add(normalized_strategy_name)
        strategy_instructions = strategy.get("custom_instructions")
        if (
            not isinstance(strategy_instructions, str)
            or not strategy_instructions.strip()
        ):
            errors.append(
                f"{strategy_label}.custom_instructions must be a non-empty string"
            )
    if strategy_names != lane_names:
        errors.append(
            f"{label}: Volc Mem0 strategies must exactly match Flowcraft lanes"
            + _set_difference_details(lane_names, strategy_names)
        )


def _set_difference_details(expected: set[str], actual: set[str]) -> str:
    details: list[str] = []
    missing = expected - actual
    extra = actual - expected
    if missing:
        details.append("missing " + ", ".join(sorted(missing)))
    if extra:
        details.append("extra " + ", ".join(sorted(extra)))
    return ": " + "; ".join(details) if details else ""


def _validate_memory_closure(
    selected: set[str],
    bindings: Mapping[str, str],
    documents: Mapping[tuple[str, str], Mapping[str, Any]],
    aliases: Mapping[str, set[str]],
    errors: list[str],
) -> None:
    selected_memory_aliases: set[str] = set()
    for workflow_name in sorted(selected):
        workflow = documents.get(("Workflow", workflow_name))
        if workflow is None:
            continue
        spec = workflow.get("spec")
        if not isinstance(spec, Mapping) or "memory" not in spec:
            continue
        memory_alias = spec.get("memory")
        if not isinstance(memory_alias, str) or not memory_alias:
            errors.append(
                f"Workflow/{workflow_name}.spec.memory must be a non-empty string"
            )
            continue
        expected_alias = DEFAULT_WORKFLOW_MEMORY_ALIASES.get(workflow_name)
        if expected_alias is not None and memory_alias != expected_alias:
            errors.append(
                f"Workflow/{workflow_name}.spec.memory must be {expected_alias!r}"
            )
        selected_memory_aliases.add(memory_alias)
        if memory_alias not in bindings:
            errors.append(
                f"Workflow/{workflow_name}: memory alias {memory_alias!r} "
                "is not bound by RuntimeProfile/default"
            )

    unused_bindings = set(bindings) - selected_memory_aliases
    if unused_bindings:
        errors.append(
            "RuntimeProfile/default has memory bindings not selected by a Workflow: "
            + ", ".join(sorted(unused_bindings))
        )

    published_layouts = {
        resource_id for kind, resource_id in documents if kind == "MemoryLayout"
    }
    bound_layouts = set(bindings.values())
    unbound_layouts = published_layouts - bound_layouts
    if unbound_layouts:
        errors.append(
            "RuntimeProfile/default does not bind published MemoryLayouts: "
            + ", ".join(sorted(unbound_layouts))
        )

    for layout_id in sorted(bound_layouts):
        layout = documents.get(("MemoryLayout", layout_id))
        if layout is None:
            continue
        for alias in sorted(
            _memory_layout_model_aliases(layout) - aliases.get("models", set())
        ):
            errors.append(
                f"MemoryLayout/{layout_id}: required models alias {alias!r} "
                "is not bound by RuntimeProfile/default"
            )


def _validate_workflow_alias_closure(
    selected: set[str],
    documents: Mapping[tuple[str, str], Mapping[str, Any]],
    aliases: Mapping[str, set[str]],
    errors: list[str],
) -> None:
    for workflow_name in sorted(selected):
        workflow = documents.get(("Workflow", workflow_name))
        if workflow is None:
            continue
        required = _workflow_aliases(workflow)
        for group, required_aliases in required.items():
            for alias in sorted(required_aliases - aliases.get(group, set())):
                errors.append(
                    f"Workflow/{workflow_name}: required {group} alias {alias!r} "
                    "is not bound by RuntimeProfile/default"
                )


def _validate_public_alias_contract(
    selected: set[str],
    documents: Mapping[tuple[str, str], Mapping[str, Any]],
    aliases: Mapping[str, set[str]],
    example: Mapping[str, Any] | None,
    errors: list[str],
) -> None:
    expected_profile_aliases = {"models": set(), "voices": set()}
    for workflow_id in sorted(selected):
        workflow = documents.get(("Workflow", workflow_id))
        if workflow is None:
            continue
        actual = _workflow_aliases(workflow)
        expected = {
            "models": WORKFLOW_MODEL_ALIASES.get(workflow_id),
            "voices": WORKFLOW_VOICE_ALIASES.get(workflow_id),
        }
        for group in ("models", "voices"):
            expected_aliases = expected[group]
            if expected_aliases is None:
                errors.append(
                    f"Workflow/{workflow_id}: public {group} alias contract is missing"
                )
                continue
            expected_profile_aliases[group].update(expected_aliases)
            if actual[group] != expected_aliases:
                errors.append(
                    f"Workflow/{workflow_id}: {group} aliases must match its "
                    "Workflow-owned contract"
                    + _set_difference_details(expected_aliases, actual[group])
                )

    published_layouts = {
        resource_id for kind, resource_id in documents if kind == "MemoryLayout"
    }
    for layout_id in sorted(published_layouts):
        layout = documents[("MemoryLayout", layout_id)]
        actual = _memory_layout_model_aliases(layout)
        expected = MEMORY_LAYOUT_MODEL_ALIASES.get(layout_id)
        if expected is None:
            errors.append(
                f"MemoryLayout/{layout_id}: public model alias contract is missing"
            )
            continue
        expected_profile_aliases["models"].update(expected)
        if actual != expected:
            errors.append(
                f"MemoryLayout/{layout_id}: model aliases must match its "
                "MemoryLayout-owned extraction contract"
                + _set_difference_details(expected, actual)
            )

    for group in ("models", "voices"):
        actual_aliases = aliases.get(group, set())
        expected_aliases = expected_profile_aliases[group]
        if actual_aliases != expected_aliases:
            errors.append(
                f"RuntimeProfile/default.spec.resources.{group} aliases must "
                "exactly match first-party consumers"
                + _set_difference_details(expected_aliases, actual_aliases)
            )

    if example is None:
        return
    example_aliases = _profile_alias_key_sets(
        example, "RuntimeProfile/raids documentation example", errors
    )
    for group in ("models", "voices"):
        if example_aliases[group] != expected_profile_aliases[group]:
            errors.append(
                f"RuntimeProfile/raids documentation example {group} aliases "
                "must match RuntimeProfile/default"
                + _set_difference_details(
                    expected_profile_aliases[group], example_aliases[group]
                )
            )


def _validate_gameplay_aliases(
    profile: Mapping[str, Any], aliases: Mapping[str, set[str]], errors: list[str]
) -> None:
    spec = profile.get("spec")
    if not isinstance(spec, Mapping):
        return
    gameplay = spec.get("gameplay")
    if not isinstance(gameplay, Mapping):
        return
    adoption = gameplay.get("adoption")
    if isinstance(adoption, Mapping):
        pool = adoption.get("pool", [])
        if not isinstance(pool, list):
            errors.append(
                "RuntimeProfile/default.spec.gameplay.adoption.pool must be a list"
            )
        else:
            for index, entry in enumerate(pool):
                if not isinstance(entry, Mapping):
                    errors.append(
                        "RuntimeProfile/default.spec.gameplay.adoption.pool"
                        f".{index} must be a mapping"
                    )
                    continue
                pet_def = entry.get("pet_def")
                if pet_def not in aliases.get("pet_defs", set()):
                    errors.append(
                        "RuntimeProfile/default.spec.gameplay.adoption.pool"
                        f".{index}: pet_defs alias {pet_def!r} is not bound"
                    )


def validate_catalog(root: Path) -> None:
    root = root.resolve()
    errors: list[str] = []
    resources: dict[tuple[str, str], Path] = {}
    documents: dict[tuple[str, str], Mapping[str, Any]] = {}
    path_documents: dict[Path, Mapping[str, Any]] = {}
    token_values: dict[str, tuple[str, Path]] = {}
    example_path = Path("runtime-profile.example.yaml")
    example_found = False
    example: Mapping[str, Any] | None = None

    yaml_paths = _yaml_paths(root)
    for path in yaml_paths:
        relative = path.relative_to(root)
        loaded = _load_yaml(path, root, errors)
        if relative == example_path:
            example_found = True
            nonempty = [document for document in loaded if document is not None]
            if len(nonempty) != 1:
                errors.append(
                    f"{relative}: documentation example must contain exactly one document"
                )
            elif isinstance(nonempty[0], Mapping):
                example = nonempty[0]
                identity = _resource_identity(example, relative, errors)
                if identity != ("RuntimeProfile", "raids"):
                    errors.append(f"{relative}: identity must be RuntimeProfile/raids")
            else:
                errors.append(f"{relative}: documentation example must be a mapping")
            continue
        if not relative.parts or relative.parts[0] not in CATALOG_DIRECTORIES:
            continue
        nonempty = [document for document in loaded if document is not None]
        if len(nonempty) != 1:
            errors.append(f"{relative}: catalog file must contain exactly one document")
            continue
        document = nonempty[0]
        identity = _resource_identity(document, relative, errors)
        if identity is None or not isinstance(document, Mapping):
            continue
        if identity in resources:
            errors.append(
                f"{relative}: ambiguous duplicate {identity[0]}/{identity[1]} "
                f"also defined by {resources[identity]}"
            )
            continue
        resources[identity] = relative
        documents[identity] = document
        path_documents[relative] = document
        if identity[0] == "RegistrationToken":
            spec = document.get("spec")
            token = spec.get("token") if isinstance(spec, Mapping) else None
            normalized_token = (
                token.strip(GO_TRIM_SPACE_CHARACTERS)
                if isinstance(token, str)
                else None
            )
            if not normalized_token:
                errors.append(
                    f"{relative}: RegistrationToken/{identity[1]}.spec.token "
                    "must be a non-empty string"
                )
            else:
                if normalized_token in token_values:
                    other_id, other_path = token_values[normalized_token]
                    errors.append(
                        f"{relative}: token value duplicates RegistrationToken/"
                        f"{other_id} from {other_path}"
                    )
                else:
                    token_values[normalized_token] = (identity[1], relative)

    profile_path = Path("runtime-profiles/default.yaml")
    token_path = Path("registration-tokens/default.yaml")
    if not example_found:
        errors.append(f"{example_path}: required documentation example is missing")
    profile = path_documents.get(profile_path)
    token = path_documents.get(token_path)
    if profile is None:
        errors.append(f"{profile_path}: required public default profile is missing")
    if token is None:
        errors.append(f"{token_path}: required public default token is missing")

    for (kind, resource_id), document in documents.items():
        _validate_current_resource_shape(
            kind,
            resource_id,
            document,
            resources[(kind, resource_id)],
            resources,
            errors,
        )

    if profile is not None:
        if (profile.get("kind"), profile.get("metadata", {}).get("id")) != (
            "RuntimeProfile",
            "default",
        ):
            errors.append(f"{profile_path}: identity must be RuntimeProfile/default")
        _validate_public_values(profile, profile_path, errors)
        selected = _selected_workflows(profile, resources, errors)
        all_workflows = {
            resource_id for kind, resource_id in resources if kind == "Workflow"
        }
        missing_from_profile = all_workflows - selected
        if missing_from_profile:
            errors.append(
                "RuntimeProfile/default does not select published Workflows: "
                + ", ".join(sorted(missing_from_profile))
            )
        aliases = _profile_aliases(profile, resources, errors)
        memory_bindings = _profile_memory_bindings(profile, resources, errors)
        _validate_workflow_alias_closure(selected, documents, aliases, errors)
        _validate_memory_closure(selected, memory_bindings, documents, aliases, errors)
        _validate_public_alias_contract(selected, documents, aliases, example, errors)
        _validate_gameplay_aliases(profile, aliases, errors)

    for (kind, resource_id), document in documents.items():
        if kind == "Workflow":
            _validate_workflow_shape(resource_id, document, errors)
        if kind == "MemoryLayout":
            _validate_memory_layout_policy(resource_id, document, errors)

    if token is not None:
        if (token.get("kind"), token.get("metadata", {}).get("id")) != (
            "RegistrationToken",
            "default-runtime",
        ):
            errors.append(
                f"{token_path}: identity must be RegistrationToken/default-runtime"
            )
        _validate_public_values(token, token_path, errors)
        spec = _require_mapping(
            token.get("spec"), "RegistrationToken/default-runtime.spec", errors
        )
        if dict(spec) != {
            "token": PUBLIC_DEFAULT_TOKEN,
            "runtime_profile_id": "default",
        }:
            errors.append(
                "RegistrationToken/default-runtime.spec must contain exactly "
                f"token={PUBLIC_DEFAULT_TOKEN} and runtime_profile_id=default"
            )

    if errors:
        raise CatalogValidationError(errors)
    print(
        f"Validated {len(yaml_paths)} YAML files, {len(resources)} catalog "
        "resources, and the public default bootstrap closure."
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (defaults to the parent of scripts/)",
    )
    args = parser.parse_args()
    try:
        validate_catalog(args.root)
    except CatalogValidationError as error:
        for message in error.errors:
            print(f"ERROR: {message}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
