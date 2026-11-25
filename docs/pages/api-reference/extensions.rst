Extension points
================

Customize URL generation by subclassing these components and assigning them
to :attr:`imgproxykit.Client.path_serializer_cls`,
:attr:`imgproxykit.Client.url_signer_cls`, or
:attr:`imgproxykit.Client.variants_resolver_cls`.

Path serializer
---------------

.. autoclass:: imgproxykit.serialization.PathSerializer
   :members:
   :special-members: __call__

Transform serializer
--------------------

Customize transformation serialization by assigning a subclass to
:attr:`imgproxykit.serialization.PathSerializer.transform_serializer_cls`.

.. autoclass:: imgproxykit.serialization.TransformSerializer
   :members:
   :special-members: __call__

Presets serializer
------------------

Presets-only mode uses
:attr:`imgproxykit.serialization.PathSerializer.presets_serializer_cls`.
Both transformation strategies return ``SerializedTransform``.

.. autoclass:: imgproxykit.serialization.PresetsSerializer
   :members:
   :special-members: __call__

.. autoclass:: imgproxykit.serialization.SerializedTransform
   :members:

Option serializer
-----------------

Customize option segments by subclassing this component and assigning it to
:attr:`imgproxykit.serialization.TransformSerializer.option_serializer_cls`.

.. autoclass:: imgproxykit.serialization.OptionSerializer
   :members:
   :special-members: __call__

Source serializer
-----------------

Customize source encoding by subclassing this component and assigning it to
:attr:`imgproxykit.serialization.PathSerializer.source_serializer_cls`.

.. autoclass:: imgproxykit.serialization.SourceSerializer
   :members:
   :special-members: __call__

URL signer
----------

.. autoclass:: imgproxykit.signing.UrlSigner
   :members:
   :special-members: __call__

Dataclass variants resolver
---------------------------

.. autoclass:: imgproxykit.variants.DataclassVariantsResolver
   :members:
   :special-members: __call__
