from dataclasses import dataclass, make_dataclass
from re import escape
from typing import Annotated, Any, Final

import pytest

from imgproxykit import Transform
from imgproxykit.variants import DataclassVariantsResolver

_SMALL: Final = Transform(width=100)
type _Thumbnail = Annotated[str, _SMALL]
type _Small = _Thumbnail
type _Variant[ResultT] = Annotated[ResultT, _SMALL]
type _Invalid = Annotated[int, _SMALL]
type _Missing = Annotated[str, 'description']
type _Ambiguous = Annotated[str, _SMALL, _SMALL]


@dataclass
class _Images:
    """Declare variants through lazy aliases and forward references."""

    small: _Thumbnail
    chained: _Small
    generic: _Variant[str]
    forward: '_Thumbnail'


def test_type_alias_variants() -> None:
    """Resolve transformations from ordinary, chained, and generic aliases."""
    assert DataclassVariantsResolver(model=_Images)() == {
        'small': _SMALL,
        'chained': _SMALL,
        'generic': _SMALL,
        'forward': _SMALL,
    }


@pytest.mark.parametrize(
    ('annotation', 'message'),
    [
        (
            _Invalid,
            'must be annotated with `Annotated[str, Transform(...)]`',
        ),
        (
            _Variant[int],
            'must be annotated with `Annotated[str, Transform(...)]`',
        ),
        (_Missing, 'got 0'),
        (_Ambiguous, 'got 2'),
    ],
)
def test_invalid_alias(*, annotation: Any, message: str) -> None:
    """Keep field validation after revealing the underlying annotation."""
    model = make_dataclass('InvalidVariants', [('small', annotation)])

    with pytest.raises(TypeError, match=escape(message)) as exc_info:
        DataclassVariantsResolver(model=model)()  # ty: ignore[invalid-argument-type]

    assert "Field 'small'" in str(exc_info.value)
    assert 'InvalidVariants' in str(exc_info.value)
