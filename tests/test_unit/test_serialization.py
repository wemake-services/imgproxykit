from typing import Final

import pytest

from imgproxykit import Transform
from imgproxykit.options import Format, Preset, Quality, Resize
from imgproxykit.serialization import (
    OptionSerializer,
    PathSerializer,
    PresetsSerializer,
    SourceSerializer,
)
from imgproxykit.types import Argument

_SOURCE: Final = 'https://example.com/photo.jpg'


@pytest.mark.parametrize(
    ('source', 'expected'),
    [
        # An HTTPS source is encoded without Base64 padding.
        (_SOURCE, '/aHR0cHM6Ly9leGFtcGxlLmNvbS9waG90by5qcGc'),
        # Unicode and query parameters are preserved.
        (
            's3://bucket/café.jpg?version=1',
            '/czM6Ly9idWNrZXQvY2Fmw6kuanBnP3ZlcnNpb249MQ',
        ),
    ],
)
def test_source_path(
    path_serializer: PathSerializer,
    *,
    source: str,
    expected: str,
) -> None:
    """Ensure that sources are encoded unchanged without Base64 padding."""
    assert path_serializer(source, transform=None) == expected


def test_unknown_source_encoding() -> None:
    """Ensure that unknown source encodings fail with a descriptive error."""
    with pytest.raises(ValueError, match="Unknown source encoding 'unknown'"):
        SourceSerializer(source_encoding='unknown')  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]  # ty: ignore[invalid-argument-type]  # pyrefly: ignore[bad-argument-type]


@pytest.mark.parametrize(
    ('transform', 'expected'),
    [
        # Processing options retain their order.
        (
            Transform(
                Quality(85),
                Resize(width=300, height=200, mode='fill'),
                Format('webp'),
            ),
            '/quality:85/resize:fill:300:200/format:webp/',
        ),
        # Names within a preset retain their order.
        (
            Transform(Preset('thumbnail', 'watermarked')),
            '/preset:thumbnail:watermarked/',
        ),
        # Presets retain their positions around overrides.
        (
            Transform(
                Preset('thumbnail'),
                Quality(85),
                Preset('watermarked'),
            ),
            '/preset:thumbnail/quality:85/preset:watermarked/',
        ),
        # Repeated formats retain their positions around presets.
        (
            Transform(
                Format('webp'),
                Preset('thumbnail'),
                Format('avif'),
            ),
            '/format:webp/preset:thumbnail/format:avif/',
        ),
        # An empty transform adds no processing segments.
        (Transform(), '/'),
    ],
)
def test_transform_path(
    path_serializer: PathSerializer,
    *,
    transform: Transform,
    expected: str,
) -> None:
    """Ensure that transform options retain their order before the source."""
    assert path_serializer(_SOURCE, transform=transform) == (
        f'{expected}aHR0cHM6Ly9leGFtcGxlLmNvbS9waG90by5qcGc'
    )


@pytest.mark.parametrize(
    ('arguments', 'expected'),
    [
        # No arguments produce only the option name.
        ((), 'resize'),
        # All trailing None values are omitted.
        ((None, None), 'resize'),
        # Trailing None values after an explicit value are omitted.
        (('fill', None, None), 'resize:fill'),
        # Leading None values retain their positions.
        ((None, 300, None), 'resize::300'),
        # Internal None values retain their positions.
        ((300, None, 200), 'resize:300::200'),
        # Consecutive internal None values retain their positions.
        (('fill', None, None, True), 'resize:fill:::1'),
        # Booleans are serialized as integers.
        ((True, False), 'resize:1:0'),
        # Floats preserve their string representation, including zero.
        ((0.0, 1.5), 'resize:0.0:1.5'),  # noqa: WPS358
        # An explicit empty string is preserved.
        (('', None), 'resize:'),
        # False is preserved before trailing None values.
        ((False, None), 'resize:0'),
        # Integer zero is preserved before trailing None values.
        ((0, None), 'resize:0'),
        # Unicode arguments are preserved.
        (('café',), 'resize:café'),
    ],
)
def test_serialize_segment(
    *,
    arguments: tuple[Argument, ...],
    expected: str,
) -> None:
    """Ensure that arguments retain their positions and explicit values."""
    serializer = OptionSerializer(argument_separator=':')
    assert serializer('resize', arguments) == expected


def test_custom_argument_separator() -> None:
    """Ensure that custom separators preserve omitted argument positions."""
    serializer = PathSerializer(
        argument_separator=',',
        use_short_options=False,
        source_encoding='base64',
        only_presets=False,
    )
    transform = Transform(Resize(width=300), format='webp')
    assert serializer(_SOURCE, transform=transform) == (
        '/resize,,300/format,webp/aHR0cHM6Ly9leGFtcGxlLmNvbS9waG90by5qcGc'
    )


def test_short_names_with_custom_separator() -> None:
    """Combine short aliases, omitted arguments and a custom separator."""
    serializer = PathSerializer(
        argument_separator=',',
        use_short_options=True,
        source_encoding='base64',
        only_presets=False,
    )
    transform = Transform(Resize(width=300), format='webp', raw=False)

    assert serializer(_SOURCE, transform=transform) == (
        '/rs,,300/f,webp/raw,0/aHR0cHM6Ly9leGFtcGxlLmNvbS9waG90by5qcGc'
    )


def test_plain_source_path() -> None:
    """Place the escaped source after options and the plain marker."""
    serializer = PathSerializer(
        argument_separator=',',
        use_short_options=True,
        source_encoding='plain',
        only_presets=False,
    )
    assert serializer(
        'http://example.com/images/curiosity.jpg?size=300',
        transform=Transform(width=300, format='webp'),
    ) == (
        '/w,300/f,webp/plain/'
        'http%3A%2F%2Fexample.com%2Fimages%2Fcuriosity.jpg%3Fsize%3D300'
    )


@pytest.mark.parametrize(
    ('transform', 'expected'),
    [
        (
            Transform(Preset('thumbnail', 'small'), Preset('watermarked')),
            (
                '/thumbnail;small;watermarked/plain/'
                'https%3A%2F%2Fexample.com%2Fphoto.jpg'
            ),
        ),
        (
            Transform(
                Format('avif'),
                Preset('thumbnail'),
                Format('webp'),
            ),
            '/thumbnail/plain/https%3A%2F%2Fexample.com%2Fphoto.jpg@webp',
        ),
    ],
)
def test_only_presets_path(*, transform: Transform, expected: str) -> None:
    """Ensure that presets keep their order and the last format is a suffix."""
    serializer = PathSerializer(
        argument_separator=';',
        use_short_options=False,
        source_encoding='plain',
        only_presets=True,
    )
    assert serializer(_SOURCE, transform=transform) == expected


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
