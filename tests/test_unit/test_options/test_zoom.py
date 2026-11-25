import pytest

from imgproxykit.options import Zoom
from imgproxykit.serialization import OptionSerializer


@pytest.mark.parametrize(
    ('option', 'expected'),
    [
        (Zoom(factor_x=1.5), 'zoom:1.5'),
        (Zoom(factor_x=1.5, factor_y=2.5), 'zoom:1.5:2.5'),
    ],
)
def test_zoom(
    option_serializer: OptionSerializer,
    *,
    option: Zoom,
    expected: str,
) -> None:
    """Ensure that zoom supports uniform and independent axis factors."""
    assert option_serializer(option.name, option.arguments) == expected
