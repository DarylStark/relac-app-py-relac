"""Module with data helpers."""

from datetime import date

from isbnlib import mask
from markdown_it import MarkdownIt
from markupsafe import Markup
from pycountry import countries, languages

_MARKDOWN = MarkdownIt('commonmark', {'html': False})


def _format_isbn(value: int | None) -> str:
    """Format an ISBN for display, leaving missing values blank."""
    return mask(str(value)) if value is not None else ''


def _render_markdown(text: str) -> Markup:
    """Render Markdown while treating source HTML as plain text."""
    return Markup(_MARKDOWN.render(text))


def _calculate_age(
    birthdate: date | None, reference_date: date | None = None
) -> int | None:
    """Calculate an age in whole years at the reference date."""
    if birthdate is None:
        return None

    reference_date = reference_date or date.today()
    age = reference_date.year - birthdate.year
    if (reference_date.month, reference_date.day) < (
        birthdate.month,
        birthdate.day,
    ):
        age -= 1
    return age


def _format_enum_label(value: str) -> str:
    """Format enum values for display without changing their stored values."""
    labels = {
        'unavailable': 'Unavailable',
        'available-direct': 'Available',
        'available-indirect': 'Available (indirect)',
        'available-to-loan': 'Available to loan',
        'available-to-buy': 'Available to buy',
        'ebook': 'eBook',
        'epub': 'ePub',
        'epub-drm': 'ePub (DRM)',
        'epub-watermark': 'ePub (watermarked)',
        'graphical-novel-adaption': 'Graphic novel adaptation',
    }
    return labels.get(value, value.replace('-', ' ').capitalize())


def _code_to_language(language_code: str) -> str:
    """Get the name for a language code."""
    lang = languages.get(alpha_2=language_code)
    return lang.name if lang else language_code


def _code_to_country(country_code: str | None) -> str:
    """Get the name for a country code."""
    if not country_code:
        return ''
    country = countries.get(alpha_2=country_code)
    return country.name if country else country_code
