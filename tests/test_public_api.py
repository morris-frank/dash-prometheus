# Pins the public behaviour the refactor must preserve. Imported before dash, as in test_metrics.
import os

import dash_prometheus

import dash
import pytest
from prometheus_client import Counter, Histogram, generate_latest


def _app():
    app = dash.Dash(__name__)
    app.layout = dash.html.Div()
    app.server.add_url_rule("/hello", "hello", lambda: "hi")
    return app


def test_exported_names():
    for name in ("registry", "counter", "histogram", "add_middleware", "prometheus_dir"):
        assert hasattr(dash_prometheus, name)
    assert isinstance(dash_prometheus.counter, Counter)
    assert isinstance(dash_prometheus.histogram, Histogram)


def test_multiprocess_dir_is_set_and_exists():
    assert os.environ["PROMETHEUS_MULTIPROC_DIR"] == dash_prometheus.prometheus_dir
    assert os.path.isdir(dash_prometheus.prometheus_dir)


def test_importing_after_dash_is_refused(monkeypatch):
    import importlib
    import sys

    monkeypatch.delitem(sys.modules, "dash_prometheus")
    with pytest.raises(RuntimeError, match="must be imported before dash"):
        importlib.import_module("dash_prometheus")


def test_metric_names_labels_and_buckets():
    assert dash_prometheus.counter._name == "dash_callback_calls"
    assert dash_prometheus.histogram._name == "dash_callback_duration"
    assert dash_prometheus.counter._labelnames == ("file", "callback")
    assert dash_prometheus.histogram._labelnames == ("file", "callback")
    assert dash_prometheus.histogram._upper_bounds == [0.001, 0.01, 0.1, 1, 5, 10, 30, 60, 120, 300, float("inf")]


def test_dash_callback_is_patched_and_keeps_the_function():
    @dash.callback(dash.Output("pin-out", "children"), dash.Input("pin-in", "n_clicks"))
    def pinned_identity(n):
        """doc"""
        return n * 2

    assert pinned_identity.__name__ == "pinned_identity"
    assert pinned_identity.__doc__ == "doc"
    assert pinned_identity(4) == 8
    labels = dash_prometheus.histogram.labels(__file__, "pinned_identity")
    assert dash_prometheus.counter.labels(__file__, "pinned_identity")._value.get() == 1
    assert labels._sum.get() >= 0
    body = generate_latest(dash_prometheus.registry).decode()
    assert 'dash_callback_duration_count{callback="pinned_identity"' in body


def test_raising_callback_is_not_counted():
    @dash.callback(dash.Output("raise-out", "children"), dash.Input("raise-in", "n_clicks"))
    def pinned_raises(n):
        raise ValueError(n)

    with pytest.raises(ValueError):
        pinned_raises(1)
    assert dash_prometheus.counter.labels(__file__, "pinned_raises")._value.get() == 0


def test_middleware_serves_metrics_and_passes_other_requests_through():
    app = _app()
    dash_prometheus.add_middleware(app)
    client = app.server.test_client()

    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.content_type.startswith("text/plain")
    assert client.get("/hello").get_data(as_text=True) == "hi"


def test_middleware_custom_slug():
    app = _app()
    dash_prometheus.add_middleware(app, slug="stats")
    client = app.server.test_client()

    assert "dash_callback_calls" in client.get("/stats").get_data(as_text=True)
    # Dash's catch-all route answers /metrics with its index page, not the exposition.
    assert "dash_callback_calls" not in client.get("/metrics").get_data(as_text=True)


def test_middleware_records_nothing_per_request():
    app = _app()
    dash_prometheus.add_middleware(app)
    client = app.server.test_client()

    before = generate_latest(dash_prometheus.registry)
    client.get("/hello")
    client.get("/metrics")
    assert generate_latest(dash_prometheus.registry) == before
