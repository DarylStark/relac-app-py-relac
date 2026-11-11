"""Tests for the database."""

import pytest

from relac.model import Contributor, Label, ResourceBase
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


def test_resolving_fields_many_to_many() -> None:
    """Test if we can resolve fields."""

    class IncorrectModel(ResourceBase): ...

    db = RelacDatabase()
    db.add_object('label.test_label_1', Label(name='test_label_1'))
    db.add_object('label.test_label_2', Label(name='test_label_2'))
    db.add_object('label.test_label_3', Label(name='test_label_3'))
    db.add_object(
        'contributor.john_williams',
        Contributor(
            name='test_label',
            labels=[
                'label.test_label_1',
                'label.test_label_2',
                'label.test_label_3',
            ],
        ),
    )
    db.resolve_all()

    contributors = db.get_all(Contributor)
    assert len(contributors['contributor.john_williams'].label_objs) == 3
    assert (
        contributors['contributor.john_williams'].label_objs[0].name
        == 'test_label_1'
    )

    labels = db.get_all(Label)
    assert len(labels['label.test_label_1'].book_objs) == 1
