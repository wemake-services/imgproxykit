from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import ClassVar

from imgproxykit.internal.encoding import encode_base64, encode_plain
from imgproxykit.options import Format, Option, Preset
from imgproxykit.transform import Transform
from imgproxykit.types import Argument, FormatType, SourceEncoding


@dataclass(frozen=True, slots=True)
class _SourceCodec:
    """Source encoder, path prefix, and output format separator."""

    encoder: Callable[[str], str]
    prefix: str
    format_separator: str


@dataclass(frozen=True, slots=True)
class SerializedTransform:
    """Ordered option segments and an optional source format suffix."""

    segments: tuple[str, ...]
    format_type: FormatType | None = None


class SourceSerializer:
    """Encode a source URI into a source path, including its marker."""

    __slots__ = ('_codec',)

    # Source representations defined by imgproxy:
    # https://docs.imgproxy.net/usage/processing#source-url
    _codecs: ClassVar[Mapping[SourceEncoding, _SourceCodec]] = {
        'base64': _SourceCodec(
            encoder=encode_base64,
            prefix='',
            format_separator='.',
        ),
        'plain': _SourceCodec(
            encoder=encode_plain,
            prefix='plain/',
            format_separator='@',
        ),
    }

    def __init__(self, *, source_encoding: SourceEncoding) -> None:
        """Select the codec for the configured source encoding."""
        self._codec = self._resolve_codec(source_encoding)

    def __call__(
        self,
        source: str,
        *,
        format_type: FormatType | None = None,
    ) -> str:
        """
        Encode the source URL and append an optional output format.

        Args:
            source: Complete source URI understood by the imgproxy server.
            format_type: Output format suffix. Omit to add no suffix.
        """
        codec = self._codec
        encoded = codec.encoder(source)
        source_path = f'{codec.prefix}{encoded}'

        if format_type is None:
            return source_path

        return f'{source_path}{codec.format_separator}{format_type}'

    @classmethod
    def _resolve_codec(cls, source_encoding: SourceEncoding) -> _SourceCodec:
        """Resolve the source codec or reject an unknown encoding."""
        codec = cls._codecs.get(source_encoding)
        if codec is None:
            raise ValueError(
                f'Unknown source encoding {source_encoding!r}. '
                f'Supported encodings: {list(cls._codecs)!r}.',
            )
        return codec


class OptionSerializer:
    """Serialize an option name and arguments into a processing segment."""

    __slots__ = ('_argument_separator',)

    def __init__(self, *, argument_separator: str) -> None:
        """Configure the separator between the name and positional arguments."""
        self._argument_separator = argument_separator

    def __call__(
        self,
        name: str,
        arguments: tuple[Argument, ...],
    ) -> str:
        """
        Serialize an option name and positional arguments into a path segment.

        Internal ``None`` values become empty positions; trailing ``None``
        values are omitted. Explicit zeroes and empty strings retain their
        positions. Booleans are serialized as ``1`` and ``0``.
        """
        end = len(arguments)
        while end and arguments[end - 1] is None:
            end -= 1

        return self._argument_separator.join(
            (
                name,
                *(
                    self._serialize_argument(argument)
                    for argument in arguments[:end]
                ),
            ),
        )

    @classmethod
    def _serialize_argument(cls, value: Argument) -> str:
        """Serialize None as empty, booleans as integers, and others as text."""
        if value is None:
            return ''
        return str(int(value) if isinstance(value, bool) else value)


class TransformSerializer:
    """Serialize transformation options in order, preserving repetitions."""

    __slots__ = ('_option_serializer', '_use_short_options')

    option_serializer_cls: ClassVar[type[OptionSerializer]] = OptionSerializer

    def __init__(
        self,
        *,
        argument_separator: str,
        use_short_options: bool,
    ) -> None:
        """Configure argument separation and processing option aliases."""
        self._option_serializer = self.option_serializer_cls(
            argument_separator=argument_separator,
        )
        self._use_short_options = use_short_options

    def __call__(self, transform: Transform) -> SerializedTransform:
        """Build option segments; empty transforms add none."""
        segments = tuple(
            self._option_serializer(
                (option.short_name or option.name)
                if self._use_short_options
                else option.name,
                option.arguments,
            )
            for option in transform.options
        )
        return SerializedTransform(segments=segments)


class PresetsSerializer:
    """Serialize server presets and an output format in presets-only mode."""

    __slots__ = ('_argument_separator',)

    def __init__(self, *, argument_separator: str) -> None:
        """Configure the separator between preset names."""
        self._argument_separator = argument_separator

    def __call__(self, transform: Transform) -> SerializedTransform:
        """Collect ordered preset names and an optional source format suffix."""
        names, output_format = self._collect_presets(transform.options)
        if not names or not all(names):
            raise ValueError(
                'Presets-only mode requires at least one preset. '
                'All preset names must be nonempty strings.',
            )

        return SerializedTransform(
            segments=(self._argument_separator.join(names),),
            format_type=output_format,
        )

    @classmethod
    def _collect_presets(
        cls,
        options: tuple[Option, ...],
    ) -> tuple[list[str], FormatType | None]:
        """Collect ordered preset names and the last format."""
        names: list[str] = []
        output_format = None
        for option in options:
            if isinstance(option, Preset):
                names.extend(option.names)
            elif isinstance(option, Format):
                output_format = option.value
            else:
                supported = [Preset.name, Format.name]
                raise TypeError(
                    f'Option {option.name!r} is not allowed '
                    'in presets-only mode. '
                    f'Supported options: {supported!r}.',
                )

        return names, output_format


class PathSerializer:
    """
    Serialize processing options and a source into an unsigned imgproxy path.

    Subclass and override :meth:`__call__` to customize path construction.
    Set the subclass on :attr:`imgproxykit.Client.path_serializer_cls`.
    """

    __slots__ = (
        '_source_serializer',
        '_transform_serializer',
    )

    transform_serializer_cls: ClassVar[type[TransformSerializer]] = (
        TransformSerializer
    )
    presets_serializer_cls: ClassVar[type[PresetsSerializer]] = (
        PresetsSerializer
    )
    source_serializer_cls: ClassVar[type[SourceSerializer]] = SourceSerializer

    def __init__(
        self,
        *,
        argument_separator: str,
        use_short_options: bool,
        source_encoding: SourceEncoding,
        only_presets: bool,
    ) -> None:
        """
        Configure processing options and select the source URL serializer.

        Args:
            argument_separator: Separator between processing option names
                and their arguments. Must match the server's
                `IMGPROXY_ARGUMENTS_SEPARATOR
                <https://docs.imgproxy.net/latest/configuration/options#miscellaneous>`__.
            source_encoding: Source URL representation: ``'base64'`` without
                padding or ``'plain'`` with full UTF-8 percent-encoding.
                See `imgproxy source URLs
                <https://docs.imgproxy.net/usage/processing#source-url>`_.
            use_short_options: Use short aliases when available,
                otherwise full names. See `imgproxy processing options
                <https://docs.imgproxy.net/usage/processing#processing-options>`_.
            only_presets: Match server presets-only mode. Require presets,
                optionally combined with output format options. See
                `imgproxy presets-only mode
                <https://docs.imgproxy.net/usage/presets#only-presets>`_.
        """
        self._transform_serializer = (
            self.presets_serializer_cls(argument_separator=argument_separator)
            if only_presets
            else self.transform_serializer_cls(
                argument_separator=argument_separator,
                use_short_options=use_short_options,
            )
        )
        self._source_serializer = self.source_serializer_cls(
            source_encoding=source_encoding,
        )

    def __call__(
        self,
        source: str,
        *,
        transform: Transform | None,
    ) -> str:
        """
        Build path using processing options and preset references.

        Serialize options before the encoded source. In presets-only mode,
        the last format becomes a source suffix; otherwise it stays an option.
        Omitted processing parameters are left to the server.

        Args:
            source: Complete source URI understood by the imgproxy server.
                Encoded according to ``source_encoding``.
            transform: Reusable processing options and optional output format.
        """
        if transform is None:
            # Give transform serializers a concrete instance, even when omitted.
            transform = Transform()

        serialized_transform = self._transform_serializer(transform)
        source_path = self._source_serializer(
            source,
            format_type=serialized_transform.format_type,
        )
        return '/'.join(('', *serialized_transform.segments, source_path))
