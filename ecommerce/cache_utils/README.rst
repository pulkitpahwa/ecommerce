Cache Utils
===========

TieredCache
-----------

    Usage::

        from ecommerce.cache_utils.utils import CACHE_MISS, TieredCache

        TieredCache.get_value_or_cache_miss(key)
        if value is CACHE_MISS:
            value = None  # or any appropriate default
            ...

            TieredCache.set_all_tiers(key, value, django_cache_timeout)

CACHE_MISS
----------

    An object to be used to represent a CACHE_MISS.  See TieredCache.

    The CACHE_MISS object avoids the problem where a cache hit that
    is Falsey is misinterpreted as a cache miss.
