"""Lossless card units and lexical indexes for the compact figure prompt.

These indexes select source text; they do not extract new historical claims or
grade generated answers. Every semicolon-delimited item stays intact, including
negations, attribution and alternative accounts.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any


FIELD_TERMS = {
    "人物": "person name",
    "英文名": "english name",
    "别名": "alias nickname",
    "性别": "gender",
    "时代": "era lifetime dates 朝代 年代 生卒 出生年 去世年",
    "出生地": "birth born birthplace childhood",
    "身份": "occupation identity",
    "简介": "biography overview",
    "生平": "life chronology journey year",
    "身边的人": "friend companion friendship people",
    "代表作品": "poem poetry work writing",
    "名句": "quote verse lines",
    "后人传说": "legend folklore tradition",
    "时代边界": "future modern posthumous",
}
ITEM_FIELDS = {"生平", "身边的人", "代表作品", "名句", "后人传说"}
IGNORED_WORDS = ["he", "she", "his", "her", "the", "and", "was", "that", "with", "from"]


def tokens(text: str) -> list[str]:
    """Chinese adjacent characters and ASCII words, without regex heuristics."""
    result: set[str] = set()
    previous, word = "", ""
    for character in text.lower():
        if "\u3400" <= character <= "\u9fff":
            if previous:
                result.add(previous + character)
            previous = character
        else:
            previous = ""
        if "a" <= character <= "z" or "0" <= character <= "9":
            word += character
        else:
            if len(word) >= 2 and word not in IGNORED_WORDS:
                result.add(word)
            word = ""
    if len(word) >= 2 and word not in IGNORED_WORDS:
        result.add(word)
    return sorted(result)


def units(repo: Path, data: dict[str, Any]) -> list[dict[str, Any]]:
    path = repo / "cards" / "figure" / f"{data['figure']['name']}.txt"
    aliases = {role["name"]: role["aliases"]
               for role in [data["companion"], *data["guests"]]}
    result = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        field, _, value = line.partition("：")
        parts = value.split("；") if field in ITEM_FIELDS else [value]
        for number, part in enumerate(parts, 1):
            # No shortening or sentence splitting: parentheses and qualifiers
            # remain attached to the claim they qualify.
            text = part.strip()
            indexed = field + " " + text + " " + FIELD_TERMS[field]
            indexed += " ".join(" " + " ".join(names)
                                for name, names in aliases.items() if name in text)
            unit = {"field": field, "line": line_number, "part": number,
                    "text": text, "terms": tokens(indexed)}
            if field == "身边的人":
                name, separator, _ = text.partition("——")
                if separator:
                    # Reserve the source entry for an explicitly named person.
                    # Names come from the card, aliases from the existing cast.
                    unit["mentions"] = sorted({value.lower() for value in
                                               [name, *aliases.get(name, [])]})
            result.append(unit)
    frequencies = Counter(term for unit in result for term in set(unit["terms"]))
    for unit in result:
        unit["terms"] = {term: max(1, 100 // frequencies[term]) for term in unit["terms"]}
        unit["rendered"] = unit["field"] + "：" + unit["text"]
        unit["characters"] = len(unit["rendered"]) + 1  # trailing newline
    return result
