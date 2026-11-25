from typing import Annotated, Any, Final, TypeAliasType

import pytest
import typing_extensions

from imgproxykit import Transform
from imgproxykit.internal.typing import unwrap_type_alias

_SMALL: Final = Transform(width=100)


@pytest.mark.parametrize('annotation', [str, Annotated[str, _SMALL]])
def test_unwrap_regular_type(*, annotation: Any) -> None:
    """Leave annotations that are not aliases unchanged."""
    assert unwrap_type_alias(annotation) is annotation


@pytest.mark.parametrize(
    'alias_factory',
    [TypeAliasType, typing_extensions.TypeAliasType],
)
def test_alias_implementations(*, alias_factory: Any) -> None:
    """Unwrap aliases constructed by either typing implementation."""
    annotation = Annotated[str, _SMALL]
    alias = alias_factory('Thumbnail', annotation)

    assert unwrap_type_alias(alias) is annotation


def test_too_many_aliases() -> None:
    """Bound the number of nested aliases that can be resolved."""
    alias_factory: Any = TypeAliasType
    annotation: Any = str

    for _ in range(16):
        annotation = alias_factory('Nested', annotation)

    with pytest.raises(TypeError, match='too many nested type aliases'):
        unwrap_type_alias(annotation)
