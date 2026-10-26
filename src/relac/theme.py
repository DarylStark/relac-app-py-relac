"""Module with a Theme class."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class RelacTheme:
    """Metadata class for a Relac Theme."""

    name: str
    source_dir: Path
    index_template: str
