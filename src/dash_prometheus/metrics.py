"""The callback metrics, and the ``dash.callback`` patch that records them."""

import inspect
import time
from functools import wraps

import dash
from prometheus_client import Counter, Histogram

from . import registry

# Metric names and labels are public API: dashboards and alerts query them.
_LABELS = ["file", "callback"]

counter = Counter("dash_callback_calls", "Number of calls to Dash callback", _LABELS, registry=registry)
histogram = Histogram(
    "dash_callback_duration",
    "Duration of Dash callback",
    _LABELS,
    buckets=(0.001, 0.01, 0.1, 1, 5, 10, 30, 60, 120, 300),
    registry=registry,
)

_unpatched_dash_dot_callback = dash.callback


def _measured(func):
    """Wrap ``func`` so each completed call is counted and timed; a call that raises is not."""
    labels = (inspect.getfile(func), func.__name__)

    def record(start):
        # Labelled lazily so a callback shows up in /metrics only once it has run.
        counter.labels(*labels).inc()
        histogram.labels(*labels).observe(time.perf_counter() - start)

    # Dash dispatches on inspect.iscoroutinefunction, so an async callback needs an async wrapper.
    if inspect.iscoroutinefunction(func):

        @wraps(func)
        async def wrapped(*args, **kwargs):
            start = time.perf_counter()
            result = await func(*args, **kwargs)
            record(start)
            return result

    else:

        @wraps(func)
        def wrapped(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            record(start)
            return result

    return wrapped


def dash_callback_overwrite(*args, **kwargs):
    """Drop-in for ``dash.callback`` that registers the measured function instead."""
    register = _unpatched_dash_dot_callback(*args, **kwargs)
    return lambda func: register(_measured(func))


dash.callback = dash_callback_overwrite
