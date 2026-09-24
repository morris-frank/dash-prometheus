# Working agreement

For humans and agents alike. `CLAUDE.md` is a symlink to this file.

`dash-prometheus` makes a Plotly Dash app export Prometheus metrics for its callbacks. It
is a published PyPI package imported into other people's servers, so it must stay small,
import-order-safe and free of anything machine-specific.

## Golden rules

1. **Import order is the contract.** `dash_prometheus` patches `dash.callback` and sets
   `PROMETHEUS_MULTIPROC_DIR` at import time, so it must load before `dash`. The guard in
   `__init__.py` raises rather than silently missing callbacks; keep it.
2. **Metric names and labels are public API.** `dash_callback_calls` and
   `dash_callback_duration`, labelled `file` and `callback`, are what dashboards and alerts
   query. Renaming one is a breaking release, and the README's metric table changes with it.
3. **Multiprocess-safe by default.** Every metric registers on the package's
   `CollectorRegistry`, which reads the multiprocess directory, so gunicorn workers report
   one set of numbers.
4. **No machine-specific paths, hosts or accounts in code.** Anything configurable is an
   argument or an environment variable with a default that works anywhere.

## Layout

```
src/dash_prometheus/
  __init__.py     import guard, multiprocess dir, shared registry
  metrics.py      the counter and histogram, and the dash.callback patch
  middleware.py   add_middleware(): mounts the /metrics WSGI app
tests/            pytest; imports dash_prometheus before dash
brand/icon/       the README icon
```

## Workflow

```bash
mise run setup     # cold start: toolchain, frozen deps, git hooks, verify
mise run check     # lint + format-check + tests — the local gate
mise run test      # tests only; also the pre-push hook
mise run build     # sdist + wheel into dist/
mise run audit     # osv-scanner against uv.lock
mise run secrets   # gitleaks over the working tree
```

CI reaches the same gates through the prek hooks and adds `build`, `secrets` and `audit`.
Dependencies via `uv add`; never hand-edit `uv.lock`. Tool versions live in `mise.toml`
and nowhere else.

## Releasing

Packaging is `pyproject.toml` alone. Bump `version` there, merge, then push a tag
`v<version>` on that commit. [`.github/workflows/release.yml`](.github/workflows/release.yml)
re-runs the gate, refuses a tag that disagrees with `pyproject.toml`, and publishes to PyPI
through trusted publishing (environment `pypi`). No token is stored in the repository.

## Definition of done

- `mise run check` is green.
- New behaviour has a direct test.
- The README's metric table matches what `metrics.py` registers.
