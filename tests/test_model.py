"""Tests for the Relac Model."""

import pytest

from relac.exceptions import DoubleModelNameError
from relac.model import ResourceBase, register_model


def test_register_model_with_double_model() -> None:
    """Test if we get an error when registering a double model name."""

    class MyModel(ResourceBase): ...

    register_model('test_model')(MyModel)

    with pytest.raises(DoubleModelNameError):
        register_model('test_model')(MyModel)
