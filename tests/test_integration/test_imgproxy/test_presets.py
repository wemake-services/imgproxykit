import pytest
import zapros

from imgproxykit import Client, Transform
from imgproxykit.options import Preset
from imgproxykit.types import SourceEncoding
from tests.fixtures.credentials import Credentials
from tests.fixtures.imgproxy import override_imgproxy_env
from tests.test_integration.test_imgproxy.assertions import (
    Size,
    assert_image,
)


# Different preset sizes make their ordering observable.
@override_imgproxy_env(
    IMGPROXY_PRESETS='thumbnail=resize:fill:160:120,small=resize:fill:80:60',
)
@pytest.mark.parametrize(
    ('presets', 'size'),
    [
        (('thumbnail',), (160, 120)),
        (('thumbnail', 'small'), (80, 60)),
        (('small', 'thumbnail'), (160, 120)),
    ],
)
def test_presets(
    imgproxy_client: Client,
    http_client: zapros.Client,
    *,
    presets: tuple[str, ...],
    size: Size,
) -> None:
    """Ensure that server presets follow supplied order."""
    url = imgproxy_client.url(
        'local:///solid-red-640x480.png',
        transform=Transform(Preset(*presets)),
    )

    response = http_client.get(url)

    assert_image(response, size=size)


@override_imgproxy_env(IMGPROXY_ONLY_PRESETS='true')
@pytest.mark.parametrize('encoding', ['plain', 'base64'])
@pytest.mark.parametrize(
    ('separator', 'presets', 'size'),
    [
        pytest.param(
            ':',
            ('thumbnail',),
            (160, 120),
            marks=override_imgproxy_env(
                IMGPROXY_PRESETS='thumbnail=resize:fill:160:120/format:jpg',
            ),
        ),
        # Use the same separator in client URLs and server preset definitions.
        pytest.param(
            ';',
            ('thumbnail', 'small'),
            (80, 60),
            marks=override_imgproxy_env(
                IMGPROXY_ARGUMENTS_SEPARATOR=';',
                IMGPROXY_PRESETS=(
                    'thumbnail=resize;fill;160;120/format;jpg,'
                    'small=resize;fill;80;60/format;jpg'
                ),
            ),
        ),
    ],
)
def test_only_presets(  # noqa: WPS211
    imgproxy_url: str,
    credentials: Credentials,
    http_client: zapros.Client,
    *,
    encoding: SourceEncoding,
    separator: str,
    presets: tuple[str, ...],
    size: Size,
) -> None:
    """Accept signed presets-only URLs and override the preset output format."""
    client = Client(
        imgproxy_url,
        **credentials,
        only_presets=True,
        source_encoding=encoding,
        argument_separator=separator,
    )
    response = http_client.get(
        client.url(
            'local:///solid-red-640x480.png',
            transform=Transform(Preset(*presets), format='webp'),
        )
    )
    assert_image(response, size=size, format='WEBP')
