# dash_prometheus refuses to load after dash, so it is imported first here too.
import dash_prometheus

import dash
from prometheus_client import generate_latest


def test_callback_calls_are_counted_and_exposed_on_metrics():
    app = dash.Dash(__name__)
    app.layout = dash.html.Div([dash.html.Button(id="in"), dash.html.Div(id="out")])

    @dash.callback(dash.Output("out", "children"), dash.Input("in", "n_clicks"))
    def echo(n_clicks):
        return n_clicks

    dash_prometheus.add_middleware(app)
    echo(3)

    assert dash_prometheus.counter.labels(__file__, "echo")._value.get() == 1
    body = app.server.test_client().get("/metrics").get_data(as_text=True)
    assert 'dash_callback_calls_total{callback="echo"' in body
    assert "dash_callback_duration_bucket" in generate_latest(dash_prometheus.registry).decode()


def test_async_callback_stays_async_and_is_counted():
    import asyncio
    import inspect

    @dash.callback(dash.Output("async-out", "children"), dash.Input("async-in", "n_clicks"))
    async def async_echo(n_clicks):
        return n_clicks

    assert inspect.iscoroutinefunction(async_echo)
    assert asyncio.run(async_echo(5)) == 5
    assert dash_prometheus.counter.labels(__file__, "async_echo")._value.get() == 1
