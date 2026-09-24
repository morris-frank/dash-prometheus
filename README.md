<img src="brand/icon/icon-dash-prometheus-on-obsidian-512.png" align="left" width="128" hspace="16" alt="dash-prometheus icon">

<h3>dash-prometheus</h3>

<p>
  <sub>PROMETHEUS FOR PLOTLY DASH</sub>
  <br>
  <strong>How often each Dash callback runs, and how long it takes.</strong>
  <br>
  <br>
  <a href="https://pypi.org/project/dash-prometheus/"><img src="https://img.shields.io/pypi/v/dash-prometheus?style=flat-square&amp;color=D78A7A&amp;logo=pypi&amp;logoColor=white&amp;labelColor=2D2825" alt="PyPI version"></a>
  <img src="https://img.shields.io/badge/Dash-%E2%89%A5%202.9.3-D78A7A?style=flat-square&amp;labelColor=2D2825" alt="Dash 2.9.3 or newer">
  <img src="https://img.shields.io/badge/python-%E2%89%A5%203.10-7E9688?style=flat-square&amp;labelColor=2D2825" alt="Python 3.10 or newer">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-7E9688?style=flat-square&amp;labelColor=2D2825" alt="MIT license"></a>
</p>

<br clear="left">

`dash-prometheus` wraps every `dash.callback` in a counter and a duration histogram and
serves them on a Prometheus endpoint mounted on the app's own server. No sidecar, no
second port: one import and one call.

```bash
pip install dash-prometheus
```

```python
import dash_prometheus  # must come before `import dash`
import dash

app = dash.Dash(__name__)
dash_prometheus.add_middleware(app)  # serves /metrics
```

`add_middleware(app, slug="stats")` serves `/stats` instead.

## Metrics

| Type | Name | Description | Labels |
| --- | --- | --- | --- |
| Counter | `dash_callback_calls` | Number of calls to a Dash callback | `file`, `callback` |
| Histogram | `dash_callback_duration` | Duration of a Dash callback, in seconds | `file`, `callback` |

`file` is the source file that defines the callback and `callback` is its function name.
Histogram buckets are 1 ms, 10 ms, 100 ms, 1 s, 5 s, 10 s, 30 s, 1 min, 2 min and 5 min.

## Multiple workers

Metrics use `prometheus_client`'s multiprocess mode, so every gunicorn worker reports into
one set of numbers. Set `PROMETHEUS_MULTIPROC_DIR` to choose the directory; without it, the
package creates a fresh one under `/tmp`. Either way the directory is **emptied on import**,
so point it at a path used for nothing else.

## Known limits

- Import order matters: `dash_prometheus` patches `dash.callback` at import time and raises
  if `dash` is already loaded, rather than silently missing callbacks.
- Only callbacks registered through `dash.callback` are measured; `app.callback` and
  clientside callbacks are not.
- A callback that raises is not counted: the counter and histogram record completed calls.
- `prometheus-client` is pinned to `0.18.0`.

## Development

```bash
mise run setup     # cold start: toolchain, frozen deps, git hooks, verify
mise run check     # lint + format + tests: the definition of done
```

See [AGENTS.md](AGENTS.md) for the working agreement.

### Releasing

Publishing runs from CI, not from a laptop: bump `version` in `pyproject.toml`, merge, then
push a tag `v<version>`. [`.github/workflows/release.yml`](.github/workflows/release.yml)
re-runs the full check, refuses a tag that disagrees with `pyproject.toml`, and publishes to
PyPI with [trusted publishing](https://docs.pypi.org/trusted-publishers/), so no API token
is stored anywhere.

## Licence

MIT
