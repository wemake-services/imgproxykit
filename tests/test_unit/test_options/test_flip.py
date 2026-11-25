import pytest

from imgproxykit.options import Flip
from imgproxykit.serialization import OptionSerializer


@pytest.mark.parametrize(
    ('option', 'expected'),
    [
        (Flip(), 'flip'),
        (Flip(horizontal=True, vertical=False), 'flip:1:0'),
        (Flip(vertical=False), 'flip::0'),
    ],
)
def test_flip(
    option_serializer: OptionSerializer,
    *,
    option: Flip,
    expected: str,
) -> None:
    """Ensure that flip axes retain positions and explicit false values."""
    assert option_serializer(option.name, option.arguments) == expected
