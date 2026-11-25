from imgproxykit.options import ResizingType
from imgproxykit.serialization import OptionSerializer


def test_resizing_type(
    option_serializer: OptionSerializer,
) -> None:
    """Ensure that resizing strategies use the resizing type segment."""
    option = ResizingType(value='fit')

    assert (
        option_serializer(option.name, option.arguments) == 'resizing_type:fit'
    )
