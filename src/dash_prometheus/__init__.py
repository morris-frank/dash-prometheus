"""Prometheus metrics for Plotly Dash callbacks. Import before ``dash``."""

import os
import shutil
import sys
import uuid

if "dash" in sys.modules:
    raise RuntimeError("dash_prometheus must be imported before dash")


def _reset_multiproc_dir() -> str:
    """Point prometheus_client at an empty multiprocess directory, creating one under /tmp if unset."""
    path = os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", f"/tmp/dash_prometheus_{uuid.uuid4()}")
    if os.path.exists(path):
        shutil.rmtree(path)
    os.mkdir(path)
    return path


# Must run before prometheus_client is imported: it reads the variable at import time.
prometheus_dir = _reset_multiproc_dir()

from prometheus_client import CollectorRegistry, multiprocess

registry = CollectorRegistry()
multiprocess.MultiProcessCollector(registry, path=prometheus_dir)

from .metrics import counter, histogram
from .middleware import add_middleware

__all__ = ["add_middleware", "counter", "histogram", "prometheus_dir", "registry"]
