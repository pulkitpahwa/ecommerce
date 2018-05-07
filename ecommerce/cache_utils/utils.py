"""
Cache utilities.
"""
import threading

from django.core.cache import cache as django_cache
from django.core.cache.backends.base import DEFAULT_TIMEOUT


class _RequestCache(threading.local):
    """
    A thread-local for storing the per-request cache.
    """

    def __init__(self):
        super(_RequestCache, self).__init__()
        self.data = {}

    def clear(self):
        self.data = {}


class TieredCache(object):
    """
    A two tiered caching object with a request cache backed by a django cache.
    """
    REQUEST_CACHE = _RequestCache()

    @classmethod
    def get_value_or_cache_miss(cls, key):
        """
        Retrieves a cached value from the request cache or the django cache.
        If there is no cache value for the key, returns the CACHE_MISS
        object.

        See README for more details.

        Args:
            key (string)

        Returns:
            The value associated with key, or the CACHE_MISS object.

        """
        request_cache_value = cls.REQUEST_CACHE.data.get(key, CACHE_MISS)
        if request_cache_value is CACHE_MISS:
            return cls._get_from_django_cache_and_set_request_cache(key)

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
        return cls.REQUEST_CACHE.data.get('force_django_cache_miss', False)


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
