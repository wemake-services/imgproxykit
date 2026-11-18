# Parts of the code are adapted from
# https://github.com/wemake-services/django-modern-rest/blob/4aec07961229cddbdfa1b67d415e552def144bc8/dmr/internal/types.py
# under MIT license.

# Original license:
# https://github.com/wemake-services/django-modern-rest/blob/4aec07961229cddbdfa1b67d415e552def144bc8/LICENSE

# The MIT License (MIT)
# Copyright (c) 2025 wemake-services
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
# OR OTHER DEALINGS IN THE SOFTWARE.

from typing import Any, Final, TypeAliasType, get_args, get_origin

import typing_extensions

# `typing` and `typing_extensions` define distinct alias classes.
_TYPE_ALIAS_TYPES: Final = (TypeAliasType, typing_extensions.TypeAliasType)

# Bound alias chains to avoid hanging on mutually recursive aliases.
_MAX_ALIAS_DEPTH: Final = 15


def unwrap_type_alias(
    annotation: typing_extensions.TypeForm[Any],
) -> typing_extensions.TypeForm[Any]:
    """
    Replaces a type alias with the type it points to.

    Type aliases created with the ``type X = Y`` syntax
    or with ``TypeAliasType`` directly are lazy objects that hide
    the real type behind them, so things like ``Annotated``
    metadata are not visible without unwrapping.

    Aliases of aliases and subscripted generic aliases
    are unwrapped as well. Anything that is not a type alias
    is returned unchanged.

    Raises:
        TypeError: when there are too many nested aliases,
            which also happens for mutually recursive ones.

    """
    # Type checkers do not know about `__value__` of type aliases:
    current: Any = annotation
    for _ in range(_MAX_ALIAS_DEPTH):
        origin = get_origin(current)
        if isinstance(current, _TYPE_ALIAS_TYPES):
            current = current.__value__
        elif isinstance(origin, _TYPE_ALIAS_TYPES):
            # Generic aliases keep their args outside of `__value__`,
            # we apply them back to get the real type:
            current = origin.__value__[get_args(current)]
        else:
            unwrapped: typing_extensions.TypeForm[Any] = current
            return unwrapped
    raise TypeError(
        f'Cannot unwrap {current!r}, too many nested type aliases',
    )
