"""
Resilient service lookup for the web app.

Why this exists: a gunicorn worker constructs the Google Sheets services
at startup. If that construction fails - e.g. the Sheets API returns 429
because both workers burst through the 60-reads/minute quota at the same
moment - the worker used to end up with NO data callbacks registered at
all: Dash cannot add callbacks after startup, so the worker served empty
pages forever while still accepting logins (the login callback
re-initialized the services, but too late for the callbacks that were
never registered).

The fix has two parts, both here:

- ServiceRegistry owns initialization and retries it (throttled) until it
  succeeds, so a poisoned start heals on later use instead of being
  final.
- LazyService is a stable stand-in handed to callback registration at
  startup. Every attribute access resolves the registry's CURRENT
  service, so callbacks registered once start working as soon as
  initialization succeeds. Its truthiness mirrors availability, so the
  layouts' existing `if not data_service:` guards keep rendering their
  graceful empty states while services are down - and return real data
  once they're up.
"""

import threading
import time


class ServiceUnavailableError(RuntimeError):
    """Raised when a service is accessed before initialization succeeds."""


class ServiceRegistry:
    """Holds the (sheets, auth, data) service triple and builds it lazily.

    `factory` is a zero-argument callable returning the triple, or raising
    when initialization fails.
    """

    def __init__(self, factory, retry_interval=30):
        self._factory = factory
        self.retry_interval = retry_interval
        self._lock = threading.Lock()
        self._services = None
        self._last_attempt = 0.0

    @property
    def ready(self):
        return self._services is not None

    def _get(self, index):
        if self._services is None:
            return None
        return self._services[index]

    @property
    def sheets_service(self):
        return self._get(0)

    @property
    def auth_service(self):
        return self._get(1)

    @property
    def data_service(self):
        return self._get(2)

    def ensure(self, force=False):
        """Build the services if they aren't built yet.

        Returns True when services are available. A failed attempt is
        throttled (unless forced) so a burst of callback hits cannot turn
        into a burst of Sheets calls - the very thing that caused the
        429s this class exists to survive.
        """
        if self.ready:
            return True
        with self._lock:
            if self.ready:
                return True
            now = time.time()
            if not force and (now - self._last_attempt) < self.retry_interval:
                return False
            self._last_attempt = now
            try:
                self._services = self._factory()
            except Exception as e:
                print(f"Service initialization failed (will retry): {e}")
                return False
            print("Services initialized successfully")
            return True


class LazyService:
    """Stand-in for a service that may not exist yet.

    Handed to callback registration at startup; resolves the real service
    from the registry on every attribute access. `kind` is one of the
    registry's property names ('sheets_service', 'auth_service',
    'data_service').
    """

    def __init__(self, registry, kind):
        object.__setattr__(self, '_registry', registry)
        object.__setattr__(self, '_kind', kind)

    def _target(self):
        registry = object.__getattribute__(self, '_registry')
        kind = object.__getattribute__(self, '_kind')
        target = getattr(registry, kind)
        if target is None:
            # Nudge a (throttled) recovery attempt, then look again.
            registry.ensure()
            target = getattr(registry, kind)
        return target

    def __getattr__(self, name):
        if name.startswith('__') and name.endswith('__'):
            raise AttributeError(name)
        target = self._target()
        if target is None:
            raise ServiceUnavailableError(
                f"{object.__getattribute__(self, '_kind')} is not initialized yet")
        return getattr(target, name)

    def __bool__(self):
        # Layouts guard with `if not data_service:` - truthiness must mean
        # "a real service is available", not "the proxy exists".
        return self._target() is not None

    def __repr__(self):
        target = self._target()
        return repr(target) if target is not None else '<LazyService: unavailable>'
