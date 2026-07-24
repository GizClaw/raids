#!/usr/bin/env python3
"""Validate Raids catalog syntax and the public default bootstrap closure."""

from __future__ import annotations

import argparse
from collections import defaultdict
from collections.abc import Iterable, Mapping
from pathlib import Path
import re
from typing import Any

import yaml


API_VERSION = "gizclaw.admin/v1alpha1"
CATALOG_DIRECTORIES = {
    "credentials",
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
    name = metadata.get("name") if isinstance(metadata, Mapping) else None
    if not isinstance(kind, str) or not kind:
        errors.append(f"{relative}: kind must be a non-empty string")
    if not isinstance(name, str) or not name:
        errors.append(f"{relative}: metadata.name must be a non-empty string")
    if not isinstance(kind, str) or not kind or not isinstance(name, str) or not name:
        return None
    return kind, name


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


def _validate_binding(
    binding: Any,
    label: str,
    resource_kind: str,
    resources: Mapping[tuple[str, str], Path],
    errors: list[str],
) -> str | None:
    binding = _require_mapping(binding, label, errors)
    resource_id = binding.get("resource_id")
    if not isinstance(resource_id, str) or not resource_id:
        errors.append(f"{label}.resource_id must be a non-empty string")
        return None
    if (resource_kind, resource_id) not in resources:
        errors.append(f"{label}: {resource_kind}/{resource_id} does not exist")
    i18n = _require_mapping(binding.get("i18n"), f"{label}.i18n", errors)
    for locale in ("en", "zh-CN"):
        text = _require_mapping(i18n.get(locale), f"{label}.i18n.{locale}", errors)
        if not isinstance(text.get("display_name"), str) or not text["display_name"]:
            errors.append(f"{label}.i18n.{locale}.display_name must be non-empty")
    return resource_id


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
            aliases[group].add(str(alias))
            _validate_binding(
                binding,
                f"RuntimeProfile/default.spec.resources.{group}.{alias}",
                resource_kind,
                resources,
                errors,
            )
    return aliases


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

    yaml_paths = _yaml_paths(root)
    for path in yaml_paths:
        relative = path.relative_to(root)
        loaded = _load_yaml(path, root, errors)
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
                f"{relative}: duplicate {identity[0]}/{identity[1]} also defined "
                f"by {resources[identity]}"
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
                    other_name, other_path = token_values[normalized_token]
                    errors.append(
                        f"{relative}: token value duplicates RegistrationToken/"
                        f"{other_name} from {other_path}"
                    )
                else:
                    token_values[normalized_token] = (identity[1], relative)

    profile_path = Path("runtime-profiles/default.yaml")
    token_path = Path("registration-tokens/default.yaml")
    profile = path_documents.get(profile_path)
    token = path_documents.get(token_path)
    if profile is None:
        errors.append(f"{profile_path}: required public default profile is missing")
    if token is None:
        errors.append(f"{token_path}: required public default token is missing")

    if profile is not None:
        if (profile.get("kind"), profile.get("metadata", {}).get("name")) != (
            "RuntimeProfile",
            "default",
        ):
            errors.append(f"{profile_path}: identity must be RuntimeProfile/default")
        _validate_public_values(profile, profile_path, errors)
        selected = _selected_workflows(profile, resources, errors)
        all_workflows = {name for kind, name in resources if kind == "Workflow"}
        missing_from_profile = all_workflows - selected
        if missing_from_profile:
            errors.append(
                "RuntimeProfile/default does not select published Workflows: "
                + ", ".join(sorted(missing_from_profile))
            )
        aliases = _profile_aliases(profile, resources, errors)
        _validate_workflow_alias_closure(selected, documents, aliases, errors)
        _validate_gameplay_aliases(profile, aliases, errors)

    if token is not None:
        if (token.get("kind"), token.get("metadata", {}).get("name")) != (
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
        if dict(spec) != {"token": "default", "runtime_profile_name": "default"}:
            errors.append(
                "RegistrationToken/default-runtime.spec must contain exactly "
                "token=default and runtime_profile_name=default"
            )

    for (kind, name), document in documents.items():
        if kind != "RegistrationToken":
            continue
        spec = _require_mapping(
            document.get("spec"), f"RegistrationToken/{name}.spec", errors
        )
        profile_name = spec.get("runtime_profile_name")
        if not isinstance(profile_name, str) or not profile_name:
            errors.append(
                f"RegistrationToken/{name}.spec.runtime_profile_name must be "
                "a non-empty string"
            )
        elif ("RuntimeProfile", profile_name) not in resources:
            errors.append(
                f"RegistrationToken/{name}.spec.runtime_profile_name references "
                f"missing RuntimeProfile/{profile_name}"
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
