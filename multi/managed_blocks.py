from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class ManagedBlock:
    name: str
    comment_prefix: str = "#"

    @property
    def begin_marker(self) -> str:
        return f"{self.comment_prefix} BEGIN multi-managed: {self.name}"

    @property
    def end_marker(self) -> str:
        return f"{self.comment_prefix} END multi-managed: {self.name}"


def _find_block_bounds(lines: list[str], block: ManagedBlock) -> tuple[int, int] | None:
    begin_indices = [
        index for index, line in enumerate(lines) if line == block.begin_marker
    ]
    end_indices = [index for index, line in enumerate(lines) if line == block.end_marker]

    if not begin_indices and not end_indices:
        return None

    if len(begin_indices) != 1 or len(end_indices) != 1:
        raise ValueError(f"Managed block '{block.name}' is malformed.")

    begin_index = begin_indices[0]
    end_index = end_indices[0]
    if begin_index > end_index:
        raise ValueError(f"Managed block '{block.name}' is malformed.")

    return begin_index, end_index


def has_managed_block(text: str, block: ManagedBlock) -> bool:
    return _find_block_bounds(text.splitlines(), block) is not None


def get_managed_block_lines(text: str, block: ManagedBlock) -> list[str]:
    lines = text.splitlines()
    bounds = _find_block_bounds(lines, block)
    if bounds is None:
        return []
    begin_index, end_index = bounds
    return lines[begin_index + 1 : end_index]


def replace_managed_block_in_text(
    text: str,
    block: ManagedBlock,
    lines: Sequence[str],
) -> str:
    existing_lines = text.splitlines()
    bounds = _find_block_bounds(existing_lines, block)

    if bounds is None:
        prefix_lines = existing_lines
        suffix_lines: list[str] = []
    else:
        begin_index, end_index = bounds
        prefix_lines = existing_lines[:begin_index]
        suffix_lines = existing_lines[end_index + 1 :]

        if prefix_lines and suffix_lines and prefix_lines[-1] == "" and suffix_lines[0] == "":
            suffix_lines = suffix_lines[1:]

    if not lines:
        result_lines = prefix_lines + suffix_lines
    else:
        managed_lines = [block.begin_marker, *list(lines), block.end_marker]
        result_lines = prefix_lines.copy()
        if result_lines and result_lines[-1] != "":
            result_lines.append("")
        result_lines.extend(managed_lines)
        if suffix_lines:
            if suffix_lines[0] != "":
                result_lines.append("")
            result_lines.extend(suffix_lines)

    if not result_lines:
        return ""
    return "\n".join(result_lines).rstrip("\n") + "\n"


def replace_managed_block(path: Path, block: ManagedBlock, lines: Sequence[str]) -> None:
    existing_text = path.read_text(encoding="utf-8") if path.exists() else ""
    next_text = replace_managed_block_in_text(existing_text, block, lines)

    if not next_text:
        if path.exists():
            path.unlink()
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(next_text, encoding="utf-8")
