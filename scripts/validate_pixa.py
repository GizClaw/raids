#!/usr/bin/env python3
"""Validate the PetDef PIXA declarations published by the Raids catalog."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Any

import yaml


API_VERSION = "gizclaw.admin/v1alpha1"
ASSET_PREFIX = "asset://codex/pets/"
PIXA_VERSION = "1"
PIXA_CLIP_NAME_MAX_BYTES = 32
PIXA_CANVAS_MAX_SIZE = (1 << 16) - 1
REQUIRED_BINDINGS = {
    "behaviors": ("feed", "bathe", "play", "heal"),
    "states": ("idle", "sick", "dead"),
}
OPTIONAL_BINDINGS = {"states": ("sleep",)}


class PixaValidationError(Exception):
    """Raised when one or more PetDef PIXA declarations are invalid."""

    def __init__(self, errors: list[str]):
        self.errors = tuple(errors)
        super().__init__("\n".join(errors))


def _mapping(value: Any, label: str, errors: list[str]) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    errors.append(f"{label} must be a mapping")
    return {}


def _nonempty_string(
    value: Any, label: str, errors: list[str]
) -> str | None:
    if not isinstance(value, str) or not value:
        errors.append(f"{label} must be a non-empty string")
        return None
    if value != value.strip():
        errors.append(f"{label} must not contain leading or trailing whitespace")
        return None
    return value


def _validate_asset_ref(value: Any, label: str, errors: list[str]) -> None:
    asset_ref = _nonempty_string(value, label, errors)
    if asset_ref is None:
        return
    if not asset_ref.startswith(ASSET_PREFIX):
        errors.append(f"{label} must start with {ASSET_PREFIX}")
        return
    asset_name = asset_ref.removeprefix(ASSET_PREFIX)
    if (
        not asset_name
        or PurePosixPath(asset_name).name != asset_name
        or not asset_name.endswith(".pixa")
    ):
        errors.append(f"{label} must reference one .pixa file directly")


def _validate_canvas(value: Any, label: str, errors: list[str]) -> None:
    canvas = _mapping(value, label, errors)
    for dimension in ("width", "height"):
        size = canvas.get(dimension)
        if (
            isinstance(size, bool)
            or not isinstance(size, int)
            or not 1 <= size <= PIXA_CANVAS_MAX_SIZE
        ):
            errors.append(
                f"{label}.{dimension} must be an integer from 1 to "
                f"{PIXA_CANVAS_MAX_SIZE}"
            )


def _validate_clips(
    value: Any, label: str, errors: list[str]
) -> set[str]:
    if not isinstance(value, list) or not value:
        errors.append(f"{label} must be a non-empty list")
        return set()

    clip_ids: set[str] = set()
    pixa_clip_names: set[str] = set()
    for index, value in enumerate(value):
        clip_label = f"{label}.{index}"
        clip = _mapping(value, clip_label, errors)
        clip_id = _nonempty_string(clip.get("id"), f"{clip_label}.id", errors)
        pixa_clip_name = _nonempty_string(
            clip.get("pixa_clip_name"),
            f"{clip_label}.pixa_clip_name",
            errors,
        )
        if clip_id is not None:
            if clip_id in clip_ids:
                errors.append(f"{clip_label}.id {clip_id!r} is duplicated")
            clip_ids.add(clip_id)
        if pixa_clip_name is not None:
            if len(pixa_clip_name.encode("utf-8")) > PIXA_CLIP_NAME_MAX_BYTES:
                errors.append(
                    f"{clip_label}.pixa_clip_name must be at most "
                    f"{PIXA_CLIP_NAME_MAX_BYTES} UTF-8 bytes"
                )
            if pixa_clip_name in pixa_clip_names:
                errors.append(
                    f"{clip_label}.pixa_clip_name {pixa_clip_name!r} is duplicated"
                )
            pixa_clip_names.add(pixa_clip_name)
    return clip_ids


def _validate_bindings(
    value: Any, clip_ids: set[str], label: str, errors: list[str]
) -> None:
    bindings = _mapping(value, label, errors)
    for group_name, field_names in REQUIRED_BINDINGS.items():
        group = _mapping(
            bindings.get(group_name), f"{label}.{group_name}", errors
        )
        for field_name in field_names:
            field_label = f"{label}.{group_name}.{field_name}"
            clip_id = _nonempty_string(group.get(field_name), field_label, errors)
            if clip_id is not None and clip_id not in clip_ids:
                errors.append(
                    f"{field_label} {clip_id!r} is not declared by PIXA metadata"
                )

    for group_name, field_names in OPTIONAL_BINDINGS.items():
        group = bindings.get(group_name)
        if not isinstance(group, Mapping):
            continue
        for field_name in field_names:
            if field_name not in group:
                continue
            field_label = f"{label}.{group_name}.{field_name}"
            clip_id = _nonempty_string(group.get(field_name), field_label, errors)
            if clip_id is not None and clip_id not in clip_ids:
                errors.append(
                    f"{field_label} {clip_id!r} is not declared by PIXA metadata"
                )


def _validate_petdef(
    document: Any, relative: Path, errors: list[str]
) -> None:
    label = relative.as_posix()
    resource = _mapping(document, label, errors)
    if resource.get("apiVersion") != API_VERSION:
        errors.append(f"{label}: apiVersion must be {API_VERSION}")
    if resource.get("kind") != "PetDef":
        errors.append(f"{label}: kind must be PetDef")

    spec = _mapping(resource.get("spec"), f"{label}: spec", errors)
    visual = _mapping(spec.get("visual"), f"{label}: spec.visual", errors)
    pixa = _mapping(visual.get("pixa"), f"{label}: spec.visual.pixa", errors)
    metadata = _mapping(
        pixa.get("metadata"), f"{label}: spec.visual.pixa.metadata", errors
    )

    _validate_asset_ref(
        pixa.get("asset_ref"), f"{label}: spec.visual.pixa.asset_ref", errors
    )
    if metadata.get("version") != PIXA_VERSION:
        errors.append(
            f"{label}: spec.visual.pixa.metadata.version must be "
            f"the string {PIXA_VERSION!r}"
        )
    _validate_canvas(
        metadata.get("canvas"),
        f"{label}: spec.visual.pixa.metadata.canvas",
        errors,
    )
    clip_ids = _validate_clips(
        metadata.get("clips"),
        f"{label}: spec.visual.pixa.metadata.clips",
        errors,
    )
    _validate_bindings(
        visual.get("bindings"),
        clip_ids,
        f"{label}: spec.visual.bindings",
        errors,
    )


def validate_pixa(root: Path) -> None:
    root = root.resolve()
    petdef_root = root / "petdefs"
    paths = sorted(petdef_root.glob("*.yaml"))
    errors: list[str] = []
    if not paths:
        errors.append("petdefs: no PetDef YAML files found")

    for path in paths:
        relative = path.relative_to(root)
        try:
            documents = list(yaml.safe_load_all(path.read_text(encoding="utf-8")))
        except (OSError, UnicodeError, yaml.YAMLError) as error:
            errors.append(f"{relative}: {error}")
            continue
        nonempty = [document for document in documents if document is not None]
        if len(nonempty) != 1:
            errors.append(f"{relative}: PetDef file must contain one document")
            continue
        _validate_petdef(nonempty[0], relative, errors)

    if errors:
        raise PixaValidationError(errors)
    print(f"Validated {len(paths)} PetDef PIXA declarations.")


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
        validate_pixa(args.root)
    except PixaValidationError as error:
        for message in error.errors:
            print(f"ERROR: {message}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
