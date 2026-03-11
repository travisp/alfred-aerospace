"""Parse Alfred-specific shortcut metadata from AeroSpace config comments."""

from __future__ import annotations

import re
import tomllib
from typing import Any, Dict, Optional


ALFRED_NAME_COMMENT_RE = re.compile(
    r"alfred-name\s*:\s*(?P<name>.+?)\s*$", re.IGNORECASE
)
ALFRED_SKIP_COMMENT_RE = re.compile(r"alfred-skip\b", re.IGNORECASE)
MULTILINE_STRING_DELIMITERS = ("'''", '"""')


def _find_comment_start(line: str) -> Optional[int]:
    quote: Optional[str] = None
    escaped = False

    for idx, char in enumerate(line):
        if quote == '"':
            if escaped:
                escaped = False
                continue
            if char == "\\":
                escaped = True
                continue
            if char == quote:
                quote = None
            continue

        if quote == "'":
            if char == quote:
                quote = None
            continue

        if char == "#":
            return idx
        if char in {"'", '"'}:
            quote = char

    return None


def _split_toml_comment(line: str) -> tuple[str, str]:
    comment_start = _find_comment_start(line)
    if comment_start is None:
        return line, ""
    return line[:comment_start], line[comment_start + 1 :]


def _parse_toml_key(segment: str) -> Optional[str]:
    candidate = segment.strip()
    if not candidate:
        return None

    try:
        parsed = tomllib.loads(f"{candidate} = ''")
    except tomllib.TOMLDecodeError:
        return None

    if len(parsed) != 1:
        return None

    key, value = next(iter(parsed.items()))
    if isinstance(value, dict):
        return None
    return key if isinstance(key, str) else None


def _binding_section_mode(section_header: str) -> Optional[str]:
    try:
        parsed = tomllib.loads(f"{section_header}\n")
    except tomllib.TOMLDecodeError:
        return None

    mode_config = parsed.get("mode")
    if not isinstance(mode_config, dict) or len(mode_config) != 1:
        return None

    mode_name, mode_section = next(iter(mode_config.items()))
    if not isinstance(mode_section, dict) or mode_section != {"binding": {}}:
        return None
    return mode_name if isinstance(mode_name, str) else None


def _extract_comment_metadata(comment: str) -> Dict[str, Any]:
    metadata: Dict[str, Any] = {}
    normalized_comment = comment.strip()

    name_match = ALFRED_NAME_COMMENT_RE.search(normalized_comment)
    if name_match:
        alfred_name = " ".join(name_match.group("name").split()).strip()
        if alfred_name:
            metadata["name"] = alfred_name

    if ALFRED_SKIP_COMMENT_RE.search(normalized_comment):
        metadata["skip"] = True
    return metadata


def _parse_binding_line(code: str) -> tuple[Optional[str], Optional[str]]:
    stripped = code.strip()
    if not stripped or "=" not in stripped:
        return None, None

    key_text, value = stripped.split("=", 1)
    binding_key = _parse_toml_key(key_text)
    if binding_key is None:
        return None, None

    value = value.lstrip()
    for delimiter in MULTILINE_STRING_DELIMITERS:
        if value.startswith(delimiter) and value.count(delimiter) == 1:
            return binding_key, delimiter
    return binding_key, None


def _comment_after_closing_delimiter(line: str, delimiter: str) -> Optional[str]:
    if delimiter not in line:
        return None

    _, _, tail = line.rpartition(delimiter)
    if "#" not in tail:
        return ""

    _, comment = tail.split("#", 1)
    return comment


def extract_shortcut_metadata(
    config_text: str,
) -> Dict[tuple[str, str], Dict[str, Any]]:
    metadata: Dict[tuple[str, str], Dict[str, Any]] = {}
    current_mode: Optional[str] = None
    multiline_binding: Optional[tuple[str, str, str]] = None

    for line in config_text.splitlines():
        if multiline_binding is not None:
            mode_name, binding_key, delimiter = multiline_binding
            comment = _comment_after_closing_delimiter(line, delimiter)
            if comment is None:
                continue

            entry = _extract_comment_metadata(comment)
            if entry:
                metadata[(mode_name, binding_key)] = entry
            multiline_binding = None
            continue

        code, comment = _split_toml_comment(line)
        stripped = code.strip()

        if stripped.startswith("[") and stripped.endswith("]"):
            current_mode = _binding_section_mode(stripped)
            continue

        if current_mode is None:
            continue

        binding_key, multiline_delimiter = _parse_binding_line(code)
        if binding_key is None:
            continue

        if multiline_delimiter is not None:
            multiline_binding = (current_mode, binding_key, multiline_delimiter)
            continue

        entry = _extract_comment_metadata(comment)
        if entry:
            metadata[(current_mode, binding_key)] = entry

    return metadata
