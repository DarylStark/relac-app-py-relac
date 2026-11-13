"""Tests for static page generation."""

import re
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
