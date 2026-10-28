"""Module with a Theme class."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


@dataclass
class RelacTheme:
    """Metadata class for a Relac Theme."""

    name: str
    source_dir: Path
    index_template: str
    static_folder: Path | None = None
    index_pages: dict[Literal['books', 'works', 'authors'], str] = field(
        default_factory=dict
    )
    resource_pages: dict[Literal['book', 'work'], str] = field(
        default_factory=dict
    )
