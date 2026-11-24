"""Tests for static page generation."""

import json
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


def test_character_and_location_detail_breadcrumbs(tmp_path: Path) -> None:
    """Include the character or location index in detail breadcrumbs."""
    relac = Relac(YamlRepoLoader(Path(__file__).parent / 'simple_project'))
    relac.import_data()
    output = tmp_path / 'output'
    relac.create_static_webpage('relac_theme_default', output)

    character_page = (output / 'character.william_stoner.html').read_text(
        encoding='utf-8'
    )
    assert re.search(
        r'<nav class="breadcrumbs".*?'
        r'<a href="works.html">Works</a>.*?'
        r'<a href="characters.html">Characters</a>.*?'
        r'<span aria-current="page">William Stoner</span>.*?</nav>',
        character_page,
        re.DOTALL,
    )

    location_page = (output / 'location.university_missouri.html').read_text(
        encoding='utf-8'
    )
    assert re.search(
        r'<nav class="breadcrumbs".*?'
        r'<a href="works.html">Works</a>.*?'
        r'<a href="locations.html">Locations</a>.*?'
        r'<span aria-current="page">University of Missouri</span>.*?</nav>',
        location_page,
        re.DOTALL,
    )


def test_character_nicknames_are_rendered_on_work_character_page(
    tmp_path: Path,
) -> None:
    """Render character nicknames in the work's character table."""
    relac = Relac(YamlRepoLoader(Path(__file__).parent / 'simple_project'))
    relac.import_data()
    output = tmp_path / 'output'
    relac.create_static_webpage('relac_theme_default', output)

    character_page = (output / 'character.william_stoner.html').read_text(
        encoding='utf-8'
    )
    assert '<dt>Nicknames</dt>' in character_page
    assert 'Will, Bill, Stoner' in character_page

    work_characters_page = (
        output / 'literary_analysis_characters.work.john_williams__stoner.html'
    ).read_text(encoding='utf-8')
    assert '<th scope="col">Nicknames</th>' in work_characters_page
    assert 'Will, Bill, Stoner' in work_characters_page


def test_character_nicknames_are_rendered(tmp_path: Path) -> None:
    """Render character nicknames on detail and index pages."""
    repo_path = tmp_path / 'repo'
    repo_path.mkdir()
    (repo_path / 'main.yml').write_text(
        'relac:\n'
        '  title: Test Library\n'
        '  owner: owner.test\n'
        'owner.test:\n'
        '  name: Test Owner\n'
        'character.with_nicknames:\n'
        '  name: Example Character\n'
        '  nicknames:\n'
        '    - Ace\n'
        '    - "A & B"\n'
        'character.without_nicknames:\n'
        '  name: Another Character\n',
        encoding='utf-8',
    )

    relac = Relac(YamlRepoLoader(repo_path))
    relac.import_data()
    output = tmp_path / 'output'
    relac.create_static_webpage('relac_theme_default', output)

    character_page = (output / 'character.with_nicknames.html').read_text(
        encoding='utf-8'
    )
    assert '<dt>Nicknames</dt>' in character_page
    assert 'Ace, A &amp; B' in character_page

    characters_page = (output / 'characters.html').read_text(encoding='utf-8')
    assert '<th scope="col">Nicknames</th>' in characters_page
    assert 'Ace, A &amp; B' in characters_page
    assert 'character.without_nicknames.html' in characters_page


def test_work_character_notes_render_below_the_row(tmp_path: Path) -> None:
    """Render character notes as full-width rows below their characters."""
    repo_path = tmp_path / 'repo'
    repo_path.mkdir()
    (repo_path / 'main.yml').write_text(
        'relac:\n'
        '  title: Test Library\n'
        '  owner: owner.test\n'
        'owner.test:\n'
        '  name: Test Owner\n'
        'character.first:\n'
        '  name: First Character\n'
        'character.second:\n'
        '  name: Second Character\n'
        'character.third:\n'
        '  name: Third Character\n'
        'work.example:\n'
        '  title: Example Work\n'
        '  authors: []\n'
        '  characters:\n'
        '    - character: character.first\n'
        '      note: "A lengthy **bold** note & its details."\n'
        '    - character: character.second\n'
        '      note: Another note.\n'
        '    - character: character.third\n',
        encoding='utf-8',
    )

    relac = Relac(YamlRepoLoader(repo_path))
    relac.import_data()
    output = tmp_path / 'output'
    relac.create_static_webpage('relac_theme_default', output)

    page = (
        output / 'literary_analysis_characters.work.example.html'
    ).read_text(encoding='utf-8')
    assert '<th scope="col">Note</th>' not in page
    assert re.search(
        r'<button class="character-note-toggle".*?'
        r'data-row-detail-toggle.*?aria-expanded="false".*?'
        r'aria-controls="character-note-1".*?'
        r'aria-label="Expand note for First Character".*?</button>',
        page,
        re.DOTALL,
    )
    assert (
        '<tr id="character-note-1" '
        'class="literary-analysis-character-note" '
        'data-row-detail-for="character-1" hidden>'
    ) in page
    assert re.search(
        r'<span class="character-note-toggle-spacer" aria-hidden="true">'
        r'</span>\s*<a href="character.third.html">Third Character</a>',
        page,
    )
    third_row = re.search(
        r'<tr data-row-group="character-3">(.*?)</tr>',
        page,
        re.DOTALL,
    )
    assert third_row is not None
    third_cells = re.findall(
        r'<td(?:\s[^>]*)?>(.*?)</td>',
        third_row.group(1),
        re.DOTALL,
    )
    assert len(third_cells) == 9
    assert not third_cells[7].strip()
    assert re.search(
        r'<tr data-row-group="character-1" class="character-with-note">'
        r'.*?</tr>\s*'
        r'<tr id="character-note-1" '
        r'class="literary-analysis-character-note" '
        r'data-row-detail-for="character-1" hidden>\s*'
        r'<td colspan="9">\s*<p>A lengthy <strong>bold</strong> note '
        r'&amp; its details\.</p>\s*</td>\s*</tr>',
        page,
        re.DOTALL,
    )

    character_page = (output / 'character.first.html').read_text(
        encoding='utf-8'
    )
    assert '<table id="character-works-table"' in character_page
    assert '<th scope="col">Note</th>' not in character_page
    assert (
        'data-sort-value="Example Work" data-filter-values=\'["Example Work"]\''
    ) in character_page
    assert re.search(
        r'<button class="character-note-toggle".*?'
        r'aria-controls="character-work-note-1".*?'
        r'aria-label="Expand note for Example Work".*?</button>',
        character_page,
        re.DOTALL,
    )
    assert re.search(
        r'<tr id="character-work-note-1" '
        r'class="literary-analysis-character-note" '
        r'data-row-detail-for="character-work-1" hidden>\s*'
        r'<td colspan="3">\s*<p>A lengthy <strong>bold</strong> note '
        r'&amp; its details\.</p>\s*</td>\s*</tr>',
        character_page,
        re.DOTALL,
    )


def test_book_language_is_shown_in_tables_and_detail_metadata(
    tmp_path: Path,
) -> None:
    """Render each book language as an independent filter value."""
    repo_path = tmp_path / 'repo'
    repo_path.mkdir()
    (repo_path / 'library.yml').write_text(
        'relac:\n'
        '  title: Test Library\n'
        '  owner: owner.test\n'
        'owner.test:\n'
        '  name: Test Owner\n'
        'contributor.author:\n'
        '  name: Example Author\n'
        'work.example:\n'
        '  title: Example Work\n'
        '  authors:\n'
        '    - contributor.author\n'
        'work_edition.example.en:\n'
        '  title: Example Work\n'
        '  work: work.example\n'
        '  language: en\n'
        '  edition_type: original\n'
        'work_edition.example.nl:\n'
        '  title: Voorbeeld\n'
        '  work: work.example\n'
        '  language: nl\n'
        '  edition_type: translation\n'
        'book.multi_language:\n'
        '  title: Multi-language book\n'
        '  medium: ebook\n'
        '  format: epub-drm\n'
        '  work_editions:\n'
        '    - work_edition.example.en\n'
        '    - work_edition.example.nl\n',
        encoding='utf-8',
    )
    relac = Relac(YamlRepoLoader(repo_path))
    relac.import_data()
    output = tmp_path / 'output'
    relac.create_static_webpage('relac_theme_default', output)

    books_page = (output / 'books.html').read_text(encoding='utf-8')
    assert '<th scope="col">Medium and format</th>' in books_page
    assert (
        '<th scope="col" class="right fit-content">Language</th>' in books_page
    )
    medium_format_cell = re.search(
        r'<td data-sort-value="ebook" data-filter-values=\'([^\']*)\' '
        r'data-filter-groups=\'([^\']*)\'>',
        books_page,
    )
    assert medium_format_cell is not None
    assert json.loads(medium_format_cell.group(1)) == [
        'eBook',
        'ePub (DRM)',
    ]
    assert json.loads(medium_format_cell.group(2)) == {
        'Format': ['ePub (DRM)'],
        'Medium': ['eBook'],
    }
    assert '<span class="table-secondary-text">ePub (DRM)</span>' in books_page
    language_cell = re.search(
        r"""<td class="right fit-content" """
        r"""data-filter-values='([^']*)'>(.*?)</td>""",
        books_page,
    )
    assert language_cell is not None
    assert set(json.loads(language_cell.group(1))) == {'Dutch', 'English'}
    assert set(language_cell.group(2).split(', ')) == {'Dutch', 'English'}

    book_page = (output / 'book.multi_language.html').read_text(
        encoding='utf-8'
    )
    assert '<dt>Medium and format</dt>' in book_page
    assert 'eBook' in book_page
    assert 'ePub (DRM)' in book_page
    language_fact = re.search(
        r'<dt>Language</dt>\s*<dd>\s*(.*?)\s*</dd>',
        book_page,
        re.DOTALL,
    )
    assert language_fact is not None
    assert set(language_fact.group(1).split(', ')) == {'Dutch', 'English'}


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


def test_generates_reading_challenge_index_and_detail_pages(  # noqa: PLR0915
    tmp_path: Path,
) -> None:
    """Render challenge counts, outcomes, and only matching sessions."""
    relac = Relac(YamlRepoLoader(Path(__file__).parent / 'simple_project'))
    relac.import_data()
    output = tmp_path / 'output'
    relac.create_static_webpage('relac_theme_default', output)

    index_page = (output / 'index.html').read_text(encoding='utf-8')
    assert '<div class="content dashboard-content">' in index_page
    assert 'href="contributors.html">contributors</a>' in index_page
    assert 'href="work-editions.html">editions</a>' in index_page
    assert 'href="works.html">works</a>' in index_page
    assert 'href="collections.html">book collections</a>' in index_page
    assert 'href="books.html">books</a>' in index_page
    for href in (
        'contributors.html',
        'work-editions.html',
        'works.html',
        'collections.html',
        'books.html',
    ):
        assert re.search(rf'<a href="{href}">\d+</a>', index_page)
    assert '<h2><a href="reading-sessions.html">Currently reading</a></h2>' in (
        index_page
    )
    assert (
        '<h2><a href="reading-challenges.html">Reading challenges</a></h2>'
        in index_page
    )
    assert (
        '<h3 class="table-card-title"><a href="reading_list.'
        'my_reading_list.html">'
        'My reading list</a></h3>'
    ) in index_page
    dashboard_list = re.search(
        r'<table id="dashboard-reading-list-1".*?</table>',
        index_page,
        re.DOTALL,
    )
    assert dashboard_list is not None
    assert (
        'work.john_williams__butchers_crossing.html' in dashboard_list.group()
    )
    assert 'work.freida_mcfadden__the_witch.html' in dashboard_list.group()
    assert 'work.john_williams__stoner.html' in dashboard_list.group()
    assert (
        'work_edition.stephen_king__mr_harrigans_phone__nl.html'
        in dashboard_list.group()
    )
    assert 'De telefoon van meneer Harrigan' in dashboard_list.group()
    assert (
        '<th scope="col" class="fit-content">Language / edition type</th>'
        in dashboard_list.group()
    )
    assert '<th scope="col">Note</th>' in dashboard_list.group()
    reading_list_page = (
        output / 'reading_list.my_reading_list.html'
    ).read_text(encoding='utf-8')
    assert '<dt>Inherited lists</dt>' in reading_list_page
    assert (
        '<a href="reading_list.dutch_translations.html">Dutch translations</a>'
    ) in reading_list_page
    assert '<dt>Prune read items</dt>' in reading_list_page
    assert '<dd>No</dd>' in reading_list_page
    assert re.search(
        r'<a href="work_edition\.john_williams__stoner__original\.html">'
        r'Stoner</a>\s*<span class="table-secondary-text">'
        r'<a href="work\.john_williams__stoner\.html">Stoner</a></span>',
        reading_list_page,
    )
    assert (
        '<th scope="col" class="fit-content">Language / edition type</th>'
        in reading_list_page
    )
    assert reading_list_page.index('<th scope="col">Series</th>') < (
        reading_list_page.index(
            '<th scope="col" class="fit-content">Language / edition type</th>'
        )
    )
    assert '<th scope="col" class="center fit-content">Editions</th>' not in (
        reading_list_page
    )
    assert '<th scope="col">Note</th>' in reading_list_page
    assert reading_list_page.index(
        '<th scope="col" class="right fit-content">Availability</th>'
    ) < reading_list_page.index('<th scope="col">Note</th>')
    assert re.search(
        r'<tr data-href="work\.john_williams__stoner\.html">'
        r'.*?<td>Try the original edition first\.</td>\s*</tr>',
        reading_list_page,
        re.DOTALL,
    )
    assert re.search(
        r'<td class="fit-content" data-filter-values=\'\["English", "Or'
        r'iginal"\]\' '
        r'data-filter-groups=\'\{"Edition type": \["Original"\], '
        r'"Language": \["English"\]\}\'>\s*English\s*'
        r'<span class="table-secondary-text">Original</span>\s*</td>',
        reading_list_page,
    )
    assert (
        len(
            re.findall(
                r'<tr data-href="work\.john_williams__stoner\.html">',
                reading_list_page,
            )
        )
        == 1
    )
    assert re.search(
        r'<tr data-href="work\.stephen_king__mr_harrigans_phone\.html">'
        r'.*?<pre>5</pre>',
        reading_list_page,
        re.DOTALL,
    )
    assert (
        'href="work_edition.stephen_king__mr_harrigans_phone__nl.html">'
        'De telefoon van meneer Harrigan</a>'
    ) in reading_list_page
    lists_page = (output / 'lists.html').read_text(encoding='utf-8')
    assert re.search(
        r'<tr data-href="reading_list\.my_reading_list\.html">'
        r'.*?<pre>\s*6\s*</pre>',
        lists_page,
        re.DOTALL,
    )
    assert (
        'data-filter-groups=\'{"Work": ["Stoner"], '
        '"Work Edition": ["Stoner"]}\''
    ) in reading_list_page
    butchers_crossing_row = re.search(
        r'<tr data-href="work\.john_williams__butchers_crossing\.html">'
        r'(.*?)</tr>',
        reading_list_page,
        re.DOTALL,
    )
    assert butchers_crossing_row is not None
    assert 'work_edition' not in butchers_crossing_row.group(1)
    assert 'data-filter-groups=' in butchers_crossing_row.group(1)
    assert '"Work": ["Butcher' in butchers_crossing_row.group(1)
    assert '"Work Edition": []' in butchers_crossing_row.group(1)
    assert (
        re.search(
            r'<td class="fit-content" data-filter-values=\'\[\]\' '
            r'data-filter-groups=\'\{"Edition '
            r'type": \[\], "Language": \[\]\}\'>'
            r'\s*</td>',
            butchers_crossing_row.group(1),
        )
        is not None
    )
    assert re.search(r'<td>\s*</td>\s*$', butchers_crossing_row.group(1))
    assert 'class="reading-challenge-list"' in index_page
    assert (
        'class="reading-challenge-status reading-challenge-status--in-progress"'
        in index_page
    )
    assert '2 of 2 sessions' in index_page
    assert re.search(r'<pre>100\.0%</pre>\s*2 of 2 sessions', index_page)
    assert re.search(
        r'<div class="reading-challenge-meter" role="progressbar" '
        r'aria-label="Finish 2 sessions in 2026 progress" aria-valuemin="0" '
        r'aria-valuemax="2" aria-valuenow="2">\s*'
        r'<span class="reading-challenge-meter-fill" '
        r'style="width: 100(?:\.0)?%;"></span>\s*</div>',
        index_page,
    )
    assert 'Finish 3 sessions in 2026' in index_page
    assert 'Closed challenge: finish 3 sessions in 2026' not in index_page
    assert re.search(
        r'<a class="reading-challenge-entry" '
        r'href="reading_challenge\.challenge_2026\.html">.*?'
        r'class="reading-challenge-progress".*?</a>',
        index_page,
        re.DOTALL,
    )

    challenges_page = (output / 'reading-challenges.html').read_text(
        encoding='utf-8'
    )
    assert '<a href="reading-sessions.html">Reading sessions</a>' in (
        challenges_page
    )
    assert '<span aria-current="page">Reading challenges</span>' in (
        challenges_page
    )
    assert 'Finish 2 sessions in 2026' in challenges_page
    assert (
        '<a href="reading-sessions.html" class="active">Reading sessions</a>'
    ) in challenges_page
    assert (
        '<a href="reading-challenges.html" class="active" '
        'aria-current="page">Reading challenges</a>'
    ) in challenges_page
    assert re.search(r'<pre>2</pre>\s*/\s*<pre>2</pre>', challenges_page)
    assert re.search(r'<pre>2</pre>\s*/\s*<pre>3</pre>', challenges_page)
    assert 'Reached' in challenges_page
    assert 'In progress' in challenges_page
    assert 'Not reached' in challenges_page
    assert 'reading-challenge-result--reached' in challenges_page
    assert 'reading-challenge-result--in-progress' in challenges_page
    assert 'reading-challenge-result--not-reached' in challenges_page
    assert 'reading-challenge-state--in-progress' in challenges_page
    assert 'reading-challenge-state--closed' in challenges_page
    assert 'href="reading_challenge.challenge_2026.html"' in challenges_page
    assert 'Finish 3 sessions in 2026' in challenges_page
    assert 'Closed challenge: finish 3 sessions in 2026' in challenges_page

    sessions_page = (output / 'reading-sessions.html').read_text(
        encoding='utf-8'
    )
    assert (
        '<a href="reading-sessions.html" class="active" '
        'aria-current="page">Reading sessions</a>'
    ) in sessions_page
    assert re.search(
        r'<a href="reading-challenges\.html"\s*>Reading challenges</a>',
        sessions_page,
    )
    assert (
        '<th scope="col" class="fit-content">Language / edition type</th>'
        in (sessions_page)
    )
    assert '<th scope="col" class="fit-content">Work structure</th>' in (
        sessions_page
    )
    assert '<th scope="col" class="fit-content">Work category</th>' in (
        sessions_page
    )
    assert '<th scope="col" class="fit-content">Primary genre</th>' in (
        sessions_page
    )
    assert '<th scope="col">Series</th>' in sessions_page
    assert sessions_page.index('<th scope="col">Book</th>') < (
        sessions_page.index(
            '<th scope="col" class="fit-content">Work structure</th>'
        )
    )
    assert sessions_page.index(
        '<th scope="col" class="fit-content">Work structure</th>'
    ) < sessions_page.index(
        '<th scope="col" class="fit-content">Work category</th>'
    )
    assert sessions_page.index(
        '<th scope="col" class="fit-content">Work category</th>'
    ) < sessions_page.index(
        '<th scope="col" class="fit-content">Language / edition type</th>'
    )
    assert re.search(
        r'<td class="fit-content" '
        r'data-filter-values=\'\["English", "Original"\]'
        r'\' data-filter-groups=\'\{"Edition type": \["Original"\], '
        r'"Language": \["English"\]\}\'>\s*English\s*'
        r'<span class="table-secondary-text">Original</span>\s*</td>',
        sessions_page,
    )
    assert (
        '<td class="fit-content" data-filter-values=\'["Novel"]\'>Novel</td>'
        in (sessions_page)
    )
    stoner_session_row = re.search(
        r'<tr data-href="reading_session\.stoner_finished_2026\.html">'
        r'(.*?)</tr>',
        sessions_page,
        re.DOTALL,
    )
    assert stoner_session_row is not None
    stoner_row = stoner_session_row.group(1)
    assert stoner_row.index(
        'book.john_williams__stoner__vintage_classic_red_spine.html'
    ) < (
        stoner_row.index(
            '<td class="fit-content" data-filter-values=\'["Novel"]\'>'
        )
    )
    assert stoner_row.index(
        '<td class="fit-content" data-filter-values=\'["Novel"]\'>'
    ) < (
        stoner_row.rindex(
            '<td class="fit-content"'
            ' data-filter-values=\'["Literary fiction"]\'>'
        )
    )
    assert stoner_row.rindex(
        '<td class="fit-content" data-filter-values=\'["Literary fiction"]\'>'
    ) < stoner_row.index(
        '<td class="fit-content" data-filter-values=\'["English", "Original"]\''
    )
    assert (
        stoner_row.count(
            '<td class="fit-content"'
            ' data-filter-values=\'["Literary fiction"]\'>'
            'Literary fiction</td>'
        )
        == 2
    )
    assert re.search(
        r"<td data-filter-values='\[\]'>\s*</td>",
        stoner_row,
    )
    assert (
        '<td class="fit-content" data-filter-values=\'["Literary fiction"]\'>'
        'Literary fiction</td>'
    ) in sessions_page

    challenge_page = (
        output / 'reading_challenge.challenge_2026.html'
    ).read_text(encoding='utf-8')
    assert '<a href="reading-sessions.html">Reading sessions</a>' in (
        challenge_page
    )
    assert '<a href="reading-challenges.html">Reading challenges</a>' in (
        challenge_page
    )
    assert re.search(
        r'<pre>2</pre>\s*/\s*<pre>2</pre>\s*\(\s*<pre>100%</pre>\s*\)',
        challenge_page,
    )
    assert (
        'class="availability-badge reading-challenge-result '
        'reading-challenge-result--reached">Reached</span>'
    ) in challenge_page
    assert (
        'class="availability-badge reading-challenge-state '
        'reading-challenge-state--in-progress">In progress</span>'
    ) in challenge_page
    assert 'Reading sessions in this challenge' in challenge_page
    assert (
        'data-href="reading_session.nineteen_eighty_four_no_end_date__finished.html"'
        in challenge_page
    )
    assert (
        'data-href="reading_session.stoner_finished_2026.html"'
        in challenge_page
    )
    assert (
        'reading_session.nineteen_eighty_four_finished_2025.html'
        not in challenge_page
    )
    assert 'reading_session.nineteen_eighty_four.html' not in challenge_page

    closed_challenge_page = (
        output / 'reading_challenge.challenge_2026_closed.html'
    ).read_text(encoding='utf-8')
    assert re.search(
        r'<pre>2</pre>\s*/\s*<pre>3</pre>\s*\(\s*<pre>67%</pre>\s*\)',
        closed_challenge_page,
    )
    assert (
        'class="availability-badge reading-challenge-result '
        'reading-challenge-result--not-reached">Not reached</span>'
    ) in closed_challenge_page
    assert (
        'class="availability-badge reading-challenge-state '
        'reading-challenge-state--closed">Closed</span>'
    ) in closed_challenge_page


def test_language_edition_filter_example_has_distinct_combinations(
    tmp_path: Path,
) -> None:
    """Provide original and translated editions for filter examples."""
    relac = Relac(YamlRepoLoader(Path(__file__).parent / 'simple_project'))
    relac.import_data()
    output = tmp_path / 'output'
    relac.create_static_webpage('relac_theme_default', output)

    filter_example_page = (
        output / 'reading_list.language_edition_filter_example.html'
    ).read_text(encoding='utf-8')
    lists_page = (output / 'lists.html').read_text(encoding='utf-8')
    assert re.search(
        r'<tr data-href="reading_list\.language_edition_filter_example\.html">'
        r'\s*<td>Language and edition type filter example</td>',
        lists_page,
    )

    rows = re.findall(
        r'<tr data-href="[^"]+">(.*?)</tr>',
        filter_example_page,
        re.DOTALL,
    )
    assert len(rows) == 3

    combinations = set()
    for row in rows:
        group_data = next(
            value
            for value in re.findall(
                r"data-filter-groups='([^']+)'",
                row,
            )
            if '"Language"' in value
        )
        groups = json.loads(group_data)
        combinations.add((groups['Language'][0], groups['Edition type'][0]))

    assert combinations == {
        ('English', 'Original'),
        ('English', 'Translation'),
        ('Spanish', 'Original'),
    }
