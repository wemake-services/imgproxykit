from typing import Final

import pytest

from imgproxykit import Transform
from imgproxykit.options import Preset, Quality
from imgproxykit.serialization import (
    PathSerializer,
    PresetsSerializer,
    SourceSerializer,
)

_SOURCE: Final = 'https://example.com/photo.jpg'


def test_unknown_source_encoding() -> None:
    """Ensure that unknown source encodings fail with a descriptive error."""
    with pytest.raises(ValueError, match="Unknown source encoding 'unknown'"):
        SourceSerializer(source_encoding='unknown')  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]  # ty: ignore[invalid-argument-type]  # pyrefly: ignore[bad-argument-type]


@pytest.mark.parametrize(
    'transform',
    [
        None,
        Transform(),
        Transform(Preset('thumbnail', '')),
    ],
)
def test_only_presets_requires_names(*, transform: Transform | None) -> None:
    """Ensure that presets-only mode requires nonempty preset names."""
    serializer = PathSerializer(
        argument_separator=':',
        use_short_options=False,
        source_encoding='base64',
        only_presets=True,
    )

    with pytest.raises(ValueError, match='Presets-only mode requires'):
        serializer(_SOURCE, transform=transform)


def test_only_presets_rejects_other_options() -> None:
    """Ensure that presets-only mode rejects ordinary processing options."""
    serializer = PresetsSerializer(argument_separator=':')

    with pytest.raises(TypeError, match="Option 'quality' is not allowed"):
        serializer(Transform(Preset('thumbnail'), Quality(85)))
