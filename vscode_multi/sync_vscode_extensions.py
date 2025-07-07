import logging
from pathlib import Path
from typing import Any, Dict

import click

from vscode_multi.paths import paths
from vscode_multi.sync_vscode_helpers import VSCodeFileMerger

logger = logging.getLogger(__name__)


class ExtensionsFileMerger(VSCodeFileMerger):
    def _get_destination_json_path(self) -> Path:
        return paths.vscode_extensions_path

    def _get_source_json_path(self, repo_path: Path) -> Path:
        return paths.get_vscode_config_dir(repo_path) / "extensions.json"

    def _post_process_json(self, merged_json: Dict[str, Any]) -> Dict[str, Any]:
        # Ensure we have a recommendations array
        if "recommendations" not in merged_json:
            merged_json["recommendations"] = []

        # Remove any duplicates while preserving order
        recommendations = merged_json["recommendations"]
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)

        merged_json["recommendations"] = unique_recommendations
        return merged_json


def merge_extensions_json() -> None:
    merger = ExtensionsFileMerger()
    merger.merge()


@click.command(name="extensions")
def merge_extensions_cmd():
    """Merge extensions.json files from all repositories into the root .vscode directory.

    This command will:
    1. Merge extension recommendations from all repos.
    2. Remove duplicate recommendations while preserving order.
    """
    logger.info("Merging extensions.json files from all repositories...")
    merge_extensions_json()
