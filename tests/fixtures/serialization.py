import pytest

from imgproxykit.serialization import OptionSerializer, PathSerializer


@pytest.fixture
def path_serializer() -> PathSerializer:
    """Provide a serializer with the standard argument separator."""
    return PathSerializer(
        argument_separator=':',
        use_short_options=False,
        source_encoding='base64',
        only_presets=False,
    )


@pytest.fixture
def option_serializer() -> OptionSerializer:
    """Provide an option serializer with the standard separator."""
    return OptionSerializer(argument_separator=':')
