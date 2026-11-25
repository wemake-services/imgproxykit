from imgproxykit import Client, Transform
from imgproxykit.options import Preset

client = Client('http://localhost:8082', only_presets=True)  # (1)!
source_url = 'https://picsum.photos/id/237/1600/1200'

thumbnail = Transform(
    Preset('thumbnail', 'small'),  # (2)!
    format='webp',  # (3)!
)

thumbnail_url = client.url(source=source_url, transform=thumbnail)
print(thumbnail_url)
