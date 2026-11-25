from collections.abc import Callable

import pytest

from imgproxykit.options import Resize
from imgproxykit.serialization import OptionSerializer
from imgproxykit.types import ResizeType


@pytest.mark.parametrize(
    ('option', 'expected'),
    [
        (Resize(), 'resize'),
        (
            Resize(
                width=300,
                height=200,
                mode='fill',
                enlarge=False,
                extend=True,
            ),
            'resize:fill:300:200:0:1',
        ),
        (Resize(height=200), 'resize:::200'),
        (Resize(extend=False), 'resize:::::0'),
    ],
)
def test_resize(
    option_serializer: OptionSerializer,
    *,
    option: Resize,
    expected: str,
) -> None:
    """Ensure that resize arguments follow protocol order and retain gaps."""
    assert option_serializer(option.name, option.arguments) == expected


@pytest.mark.parametrize(
    ('factory', 'mode'),
    [
        (Resize.fit, 'fit'),
        (Resize.fill, 'fill'),
        (Resize.fill_down, 'fill-down'),
        (Resize.force, 'force'),
        (Resize.auto, 'auto'),
    ],
)
@pytest.mark.parametrize(
    ('settings', 'suffix'),
    [
        ({}, ''),
        (
            {'width': 0, 'height': 200, 'enlarge': False, 'extend': True},
            ':0:200:0:1',
        ),
        ({'enlarge': True, 'extend': False}, ':::1:0'),
    ],
)
def test_resize_factories(
    option_serializer: OptionSerializer,
    *,
    factory: Callable[..., Resize],
    mode: ResizeType,
    settings: dict[str, int | bool],
    suffix: str,
) -> None:
    """Serialize each resize mode with omitted dimensions and explicit flags."""
    option = factory(**settings)

    assert (
        option_serializer(option.name, option.arguments)
        == f'resize:{mode}{suffix}'
    )
