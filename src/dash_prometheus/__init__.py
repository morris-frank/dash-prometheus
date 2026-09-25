"""Prometheus metrics for Plotly Dash callbacks. Import before ``dash``."""

import os
import sys
import tempfile

if "dash" in sys.modules:
    raise RuntimeError("dash_prometheus must be imported before dash")


def _multiproc_dir() -> str:
    """Point prometheus_client at a multiprocess directory, creating a fresh one if unset.

    A directory the caller set is never emptied here: gunicorn workers each import this
    package, and one worker wiping it would erase the others' metrics.
    """
    path = os.environ.get("PROMETHEUS_MULTIPROC_DIR")
    if path is None:
        path = os.environ["PROMETHEUS_MULTIPROC_DIR"] = tempfile.mkdtemp(prefix="dash_prometheus_")
    else:
        os.makedirs(path, exist_ok=True)
    return path


# Must run before prometheus_client is imported: it reads the variable at import time.
prometheus_dir = _multiproc_dir()

from prometheus_client import CollectorRegistry, multiprocess

registry = CollectorRegistry()
multiprocess.MultiProcessCollector(registry, path=prometheus_dir)

from .metrics import counter, histogram
from .middleware import add_middleware

__all__ = ["add_middleware", "counter", "histogram", "prometheus_dir", "registry"]
