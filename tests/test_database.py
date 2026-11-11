"""Tests for the database."""

import pytest

from relac.model import Contributor, ResourceBase
from relac.relac_database import RelacDatabase


def test_adding_one_contributor() -> None:
    """Test if we can add one contributor."""
    db = RelacDatabase()
    contrib_id = 'contributor.testcontrib'
    contrib = Contributor(name='TestContrib')

    db.add_object(contrib_id, contrib)

    contribs = db.get_all(Contributor)
    assert len(contribs) == 1
    assert contribs[contrib_id].name == 'TestContrib'


def test_adding_more_contributors() -> None:
    """Test if we can add more then one contributor."""
    db = RelacDatabase()

    for idx in range(0, 10):
        contrib_id = f'contributor.testcontrib_{idx}'
        contrib = Contributor(name=f'TestContrib_{idx}')
        db.add_object(contrib_id, contrib)

    contribs = db.get_all(Contributor)
    assert len(contribs) == 10
    assert contribs['contributor.testcontrib_1'].name == 'TestContrib_1'


def test_adding_more_contribs_same_id() -> None:
    """Test if we can add more then one contributor with the same id.

    Should raise an error
    """
    db = RelacDatabase()
    contrib_id = 'contributor.testcontrib'
    contrib = Contributor(name='TestContrib')

    db.add_object(contrib_id, contrib)

    with pytest.raises(ValueError):
        db.add_object(contrib_id, contrib)


def test_adding_incorrect_data() -> None:
    """Test if we are not allowed to add wrong data."""

    class IncorrectModel(ResourceBase): ...

    db = RelacDatabase()
    with pytest.raises(TypeError):
        db.add_object('incorrect', IncorrectModel())
