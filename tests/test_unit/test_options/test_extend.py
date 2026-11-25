import pytest

from imgproxykit.options import Extend, Gravity
from imgproxykit.serialization import OptionSerializer


@pytest.mark.parametrize(
    ('option', 'expected'),
    [
        (Extend(value=False), 'extend:0'),
        (
            Extend(value=True, gravity=Gravity.focus(x=0.25, y=0.75)),
            'extend:1:fp:0.25:0.75',
        ),
        (
            Extend(value=True, gravity=Gravity.center(offset_y=0)),
            'extend:1:ce::0',
        ),
    ],
)
def test_extend(
    option_serializer: OptionSerializer,
    *,
    option: Extend,
    expected: str,
) -> None:
    """Ensure that extension retains its flag, anchor, and offset positions."""
    assert option_serializer(option.name, option.arguments) == expected
