"""Main theme for Relac dashboard."""

from pathlib import Path

from relac.theme import RelacTheme

relac_theme = RelacTheme(
    name='Default Relac Theme',
    source_dir=Path(__file__).parent / 'templates',
    index_template='index.html',
)
