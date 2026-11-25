import enum
from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Any, Final, Required, final

from django.core.exceptions import ImproperlyConfigured
from django.db.models.fields.files import FieldFile
from typing_extensions import TypedDict

from imgproxykit.transform import Transform
from imgproxykit.types import SourceEncoding

if TYPE_CHECKING:
    from _typeshed import DataclassInstance

IMGPROXYKIT_SETTINGS: Final = 'IMGPROXYKIT'


@final
@enum.unique
class ClientSettings(enum.StrEnum):
    """Name options in IMGPROXYKIT's client dictionary."""

    base_url = 'base_url'
    key = 'key'
    salt = 'salt'
    signature_size = 'signature_size'
    unsigned_marker = 'unsigned_marker'
    argument_separator = 'argument_separator'
    use_short_options = 'use_short_options'
    only_presets = 'only_presets'
    source_encoding = 'source_encoding'


@final
@enum.unique
class Settings(enum.StrEnum):
    """Name options in Django's IMGPROXYKIT dictionary."""

    client = 'client'
    transforms = 'transforms'
    variants = 'variants'
    source_resolver = 'source_resolver'


class ClientSettingsDict(TypedDict, total=False, closed=True):
    """Describe client constructor options for static type checking."""

    base_url: Required[str]
    """Public imgproxy address, including any deployment path prefix."""
    key: str | None
    """Hex-encoded signing key matching the imgproxy server."""
    salt: str | None
    """Hex-encoded signing salt matching the imgproxy server."""
    signature_size: int
    """Positive signature digest byte count; must match the server."""
    unsigned_marker: str
    """Signature marker used when signing credentials are omitted."""
    argument_separator: str
    """Processing argument separator; must match the server."""
    use_short_options: bool
    """Use short processing option aliases when available."""
    only_presets: bool
    """Serialize only preset options, ignoring other processing options."""
    source_encoding: SourceEncoding
    """Source URL representation using Base64 or percent-encoded plain mode."""


class SettingsDict(TypedDict, total=False, closed=True):
    """Describe the IMGPROXYKIT dictionary for static type checking."""

    client: Required[ClientSettingsDict]
    """Client constructor options; defaults remain in the core Client."""
    transforms: Mapping[str, Transform]
    """Named Python transformations, distinct from imgproxy server presets."""
    variants: Mapping[str, Mapping[str, Transform] | type['DataclassInstance']]
    """Named sets of transformations; objects can be shared with transforms."""
    source_resolver: Callable[[str | FieldFile], str] | str
    """Convert the original source to a URI, including empty file fields."""


assert set(SettingsDict.__annotations__) == set(Settings), (  # noqa: S101
    'Settings enum and its type SettingsDict have different keys'
)
assert set(ClientSettingsDict.__annotations__) == set(ClientSettings), (  # noqa: S101
    'ClientSettings enum and its type ClientSettingsDict have different keys'
)


# Client defaults stay in Client; these defaults belong to the Django adapter.
_DEFAULTS: Final[Mapping[str, Any]] = {  # noqa: WPS407
    Settings.transforms: {},
    Settings.variants: {},
    Settings.source_resolver: (
        'imgproxykit.integrations.django.sources.default_source_resolver'
    ),
}


def get_config() -> SettingsDict:
    """
    Read the client configuration from Django's IMGPROXYKIT setting.

    Access settings only when called. Merge adapter defaults with supplied
    settings without modifying the original dictionary. Client option
    defaults and signing validation remain in the core client.

    Returns:
        A new dictionary containing adapter defaults and configured options.

    Raises:
        ImproperlyConfigured: If ``IMGPROXYKIT`` is missing or ``None``.
    """
    # Keep LazySettings out of module globals: doctest inspection evaluates it.
    from django.conf import settings  # noqa: PLC0415

    config = getattr(settings, IMGPROXYKIT_SETTINGS, None)
    if config is None:
        raise ImproperlyConfigured(
            'Define IMGPROXYKIT in Django settings to configure imgproxykit.',
        )
    return _resolve_defaults(config)  # type: ignore[no-any-return]


def _resolve_defaults(config: Mapping[str, Any]) -> Any:
    """Overlay configured options on the Django adapter defaults."""
    return {**_DEFAULTS, **config}
