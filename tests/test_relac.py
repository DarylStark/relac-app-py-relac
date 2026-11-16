"""Tests for static page generation."""

import re
import shutil
from pathlib import Path

from relac.relac import Relac
from relac.yaml_repo_loader import YamlRepoLoader


def test_generates_book_owner_detail_page(tmp_path: Path) -> None:
    """Generate an ownership page with owner, loan, and link details."""
    repo_path = tmp_path / 'repo'
    repo_path.mkdir()
    (repo_path / 'main.yml').write_text(
        'relac:\n  title: Test Library\n  owner: owner.daryl\n',
        encoding='utf-8',
    )
    (repo_path / 'owners.yml').write_text(
        'owner.daryl:\n  name: Daryl\nowner.library:\n  name: Library\n',
        encoding='utf-8',
    )
    (repo_path / 'books.yml').write_text(
        'book.stoner:\n'
        '  title: Stoner\n'
        '  links:\n'
        '    - title: Book reference\n'
        '      url: https://example.com/book\n'
        '      link_type: buy\n'
        '  owners:\n'
        '    - owner: owner.library\n'
        '      loans:\n'
        '        - loaned_to: owner.daryl\n'
        '          loaned_on: 2026-01-02\n'
        '          due_date: 2026-01-30\n'
        '          returned_on: 2026-01-29\n'
        '        - loaned_to: owner.daryl\n'
        '          loaned_on: 2026-02-01\n'
        '          due_date: 2026-03-01\n'
        '      link:\n'
        '        title: Loan record\n'
        '        url: https://example.com/loan\n'
        '    - owner: owner.daryl\n'
        '      since: 2020-01-01\n',
        encoding='utf-8',
    )

    relac = Relac(YamlRepoLoader(repo_path))
    relac.import_data()
    output = tmp_path / 'output'
    relac.create_static_webpage('relac_theme_default', output)

    ownership_page = output / 'book_owner.book.stoner.0.html'
    assert ownership_page.is_file()
    page_content = ownership_page.read_text(encoding='utf-8')
    assert '<dt>Book</dt>' in page_content
    assert 'href="book.stoner.html">Stoner</a>' in page_content
    assert 'Library' in page_content
    assert 'Loan history' in page_content
    assert 'Loaned to' in page_content
    assert 'Daryl' in page_content
    assert 'Returned' in page_content
    assert '2026-01-29' in page_content
    assert '2026-01-02' in page_content
    assert '2026-02-01' in page_content
    assert 'Due back' in page_content
    assert '2026-01-30' in page_content
    assert '2026-03-01' in page_content
    assert 'https://example.com/loan' in page_content
    assert 'Loan record' in page_content
    book_page = (output / 'book.stoner.html').read_text(encoding='utf-8')
    assert '<h3 class="table-card-title">Links</h3>' in book_page
    assert (
        '<a class="detail-link" href="https://example.com/book"'
        ' target="_blank" rel="noopener noreferrer">'
    ) in book_page
    assert '<span class="detail-link-title">Book reference</span>' in book_page
    assert '<span class="detail-link-type">Buy</span>' in book_page
    assert (
        'class="detail-link-url">https://example.com/book</span>' in book_page
    )
    assert book_page.rfind('<div class="card detail-links-card">') == (
        book_page.rfind('<div class="card')
    )
    assert '<th scope="col">Loaned to</th>' in book_page
    assert 'Daryl' in book_page
    assert 'Loaned on 2026-02-01' in book_page
    assert 'Due back 2026-03-01' in book_page
    assert '<th scope="col">Link</th>' in book_page
    assert 'href="https://example.com/loan"' in book_page
    assert 'Loan record' in book_page
    assert 'data-href="book_owner.book.stoner.0.html"' in book_page
    assert 'View details' not in book_page
    no_link_row = re.search(
        r'<tr data-href="book_owner\.book\.stoner\.1\.html">(.*?)</tr>',
        book_page,
        re.DOTALL,
    )
    assert no_link_row is not None
    cells = re.findall(r'<td>(.*?)</td>', no_link_row.group(1), re.DOTALL)
    assert len(cells) == 4
    assert not cells[-1].strip()


def test_book_language_is_shown_in_tables_and_detail_metadata(
    tmp_path: Path,
) -> None:
    """Render each book language as an independent filter value."""
    repo_path = tmp_path / 'repo'
    shutil.copytree(Path(__file__).parent / 'simple_project', repo_path)
    (repo_path / 'books.yml').write_text(
        'book.multi_language:\n'
        '  title: Multi-language book\n'
        '  work_editions:\n'
        '    - work_edition.stephen_king__mr_harrigans_phone__original\n'
        '    - work_edition.stephen_king__mr_harrigans_phone__nl\n',
        encoding='utf-8',
    )
    relac = Relac(YamlRepoLoader(repo_path))
    relac.import_data()
    output = tmp_path / 'output'
    relac.create_static_webpage('relac_theme_default', output)

    books_page = (output / 'books.html').read_text(encoding='utf-8')
    assert (
        '<th scope="col" class="right fit-content">Language</th>' in books_page
    )
    assert (
        '<td class="right fit-content" '
        'data-filter-values=\'["Dutch"]\'>Dutch</td>' in books_page
    )
    assert (
        '<td class="right fit-content" '
        'data-filter-values=\'["English", "Dutch"]\'>English, Dutch</td>'
        in books_page
    )

    book_page = (output / 'book.multi_language.html').read_text(
        encoding='utf-8'
    )
    assert '<dt>Language</dt>' in book_page
    assert 'English, Dutch' in book_page


def test_generated_analysis_pages_have_read_status_controls(
    tmp_path: Path,
) -> None:
    """Render stable read-status keys on work and chapter analysis pages."""
    repo_path = Path(__file__).parent / 'simple_project'
    relac = Relac(YamlRepoLoader(repo_path))
    relac.import_data()
    output = tmp_path / 'output'
    relac.create_static_webpage('relac_theme_default', output)

    analysis_page = (
        output / 'literary_analysis.work.john_williams__stoner.html'
    ).read_text(encoding='utf-8')
    analysis_key = 'work:work.john_williams__stoner:analysis'
    assert f'data-read-page-key="{analysis_key}"' in analysis_page
    assert 'Mark as read' in analysis_page
    assert 'literary-analysis-read-toggle-icon' in analysis_page
    assert 'static/literary-analysis-read-status.js' in analysis_page
    assert 'aria-label="Summary available"' in analysis_page
    assert 'aria-label="Analysis available"' in analysis_page

    chapter_page_path = (
        output / 'literary_analysis_chapter.work.john_williams__stoner.'
        'part-1.chapter-1.html'
    )
    chapter_page = chapter_page_path.read_text(encoding='utf-8')
    chapter_page_id = chapter_page_path.stem.removeprefix(
        'literary_analysis_chapter.work.john_williams__stoner.'
    )
    chapter_key = f'work:work.john_williams__stoner:chapter:{chapter_page_id}'
    assert f'data-read-page-key="{chapter_key}"' in chapter_page
    assert 'Mark as read' in chapter_page
    assert 'literary-analysis-read-toggle-icon' in chapter_page
    assert 'aria-label="Summary available"' in chapter_page
    assert 'aria-label="Analysis available"' in chapter_page
    assert 'data-read-group-label="Chapters"' in chapter_page
    assert 'data-read-group-label="Part 1"' in chapter_page
