"""
Cache utilities.
"""
import threading

from django.core.cache import cache as django_cache
from django.core.cache.backends.base import DEFAULT_TIMEOUT


class TieredCache(object):
    """
    The first tier is a request cache that is tied to the life of a
    given request. The second tier is the Django cache -- e.g. the
    "default" entry in settings.CACHES, typically backed by memcached.

    Some baseline rules:

    1. Treat it as a global namespace, like any other cache. The per-request
       local cache is only going to live for the lifetime of one request, but
       the backing cache is going to be something like Memcached, where key
       collision is possible.

    2. Timeouts are ignored for the purposes of the in-memory request cache,
       but do apply to the Django cache. One consequence of this is that
       sending an explicit timeout of 0 in `set` or `add` will cause that
       item to only be cached across the duration of the request and will not
       cause a write to the remote cache.

    """
    class _RequestCache(threading.local):
        """
        A thread-local for storing the per-request cache.
        """

        def __init__(self):
            super(TieredCache._RequestCache, self).__init__()
            self.data = {}

        def clear(self):
            self.data = {}

    REQUEST_CACHE = _RequestCache()

    @classmethod
    def get_value_or_cache_miss(cls, key):
        """
        Retrieves a cached value from the request cache or the django cache.
        If there is no cache value for the key, returns the CACHE_MISS
        object.

        Note: The CACHE_MISS object avoids the problem where a cache hit that
        is Falsey is misinterpreted as a cache miss.

        Usage:
            value = cache.get_value_or_cache_miss(key)
            if value is CACHE_MISS:
                value = None  # or any appropriate default
                ...

        Args:
            key (string)

        Returns:
            The value associated with key, or the CACHE_MISS object.

        """
        request_cache_value = cls.REQUEST_CACHE.data.get(key, CACHE_MISS)
        if request_cache_value is CACHE_MISS:
            return cls._get_from_django_cache_and_set_request_cache()

        return request_cache_value

    @classmethod
    def set_all_tiers(cls, key, value, django_cache_timeout=DEFAULT_TIMEOUT):
        """
        Caches the value for the provided key in both the request cache and the
        django cache.

        Args:
            key (string)
            value (object)
            django_cache_timeout (int): (Optional) Timeout used to determine
                if and for how long to cache in the django cache. A timeout of
                0 will skip the django cache. If timeout is provided, use that
                timeout for the key; otherwise use the default cache timeout.

        """
        cls.REQUEST_CACHE.data[key] = value
        django_cache.set(key, value, django_cache_timeout)

    def _get_and_set_force_django_cache_miss(self, request):
        """
        Gets value for request query parameter 'force_django_cache_miss'
        and sets it in the request cache.

        Example:
            http://clobert.com/api/v1/resource?force_django_cache_miss=true

        """
        force_django_cache_miss = request.GET.get('force_django_cache_miss', 'false').lower() == 'true'
        self.REQUEST_CACHE.data['force_django_cache_miss'] = force_django_cache_miss

    @classmethod
    def _get_from_django_cache_and_set_request_cache(cls, key):
        """
        Retrieves a value from the django cache and sets it in the request
        cache (if not a CACHE_MISS).

        If the request was set to force cache misses, then this will always
        return CACHE_MISS.

        Args:
            key (string)

        Returns:
            The cached value or CACHE_MISS.

        """
        if cls._force_django_cache_miss():
            return CACHE_MISS

        value = django_cache.get(key, CACHE_MISS)
        if value is not CACHE_MISS:
            cls.REQUEST_CACHE.data[key] = value
        return value

    @classmethod
    def _force_django_cache_miss(cls):
        return cls.REQUEST_CACHE.data['force_django_cache_miss']


class CacheMissError(Exception):
    """
    An error used when the CACHE_MISS object is misused in any context other
    than checking if it is the CACHE_MISS object.
    """
    USAGE_MESSAGE = 'Proper Usage: "if value is CACHE_MISS: value = DEFAULT; ...".'

    def __init__(self, message=USAGE_MESSAGE):
        super(CacheMissError, self).__init__(message)


class _CacheMiss(object):
    """
    Private class representing cache misses.  This is not meant to be used
    outside of the singleton declaration of CACHE_MISS.

    Meant to be a noisy object if used for any other purpose other than:
        if value is CACHE_MISS:
    """
    def __repr__(self):
        return 'CACHE_MISS'

    def __nonzero__(self):
        raise CacheMissError()

    def __bool__(self):
        raise CacheMissError()

    def __index__(self):
        raise CacheMissError()

    def __getattr__(self, name):
        raise CacheMissError()

    def __setattr__(self, name, val):
        raise CacheMissError()

    def __getitem__(self, key):
        raise CacheMissError()

    def __setitem__(self, key, val):
        raise CacheMissError()

    def __iter__(self):
        raise CacheMissError()

    def __contains__(self, value):
        raise CacheMissError()


# Singleton CacheMiss to be used everywhere.
CACHE_MISS = _CacheMiss()
