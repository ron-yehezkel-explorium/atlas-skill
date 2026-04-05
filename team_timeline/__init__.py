"""team_timeline — team gantt pipeline package.

Programmatic API:
    from team_timeline import run_build, run_preflight

Note: imports are deferred to avoid the __main__ re-import warning
when running via `python3 -m team_timeline`.
"""


def run_build(args):  # type: ignore[no-untyped-def]
    from .__main__ import run_build as _run_build
    return _run_build(args)


def run_preflight(args):  # type: ignore[no-untyped-def]
    from .__main__ import run_preflight as _run_preflight
    return _run_preflight(args)


__all__ = ["run_build", "run_preflight"]
