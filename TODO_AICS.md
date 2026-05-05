# vconverge — open issues to resolve for AICS L3 readiness

This file tracks vconverge gaps that remain after the
`pyproject.toml` migration (commit `eab9e86`, May 2026). The
migration was the minimum needed to make `pip install -e .` work
under modern setuptools (>=70). Three latent issues remain — none
broke the install, but each will surface in different scenarios.

When vconverge eventually graduates to AICS Level 3 (third parties
can verify reproductions at the bit level via SHA-256 hashes), all
three need to be fixed and a tagged release with an attached wheel
needs to exist. The plan that frames the L3 work for the GJ 1132
XUV benchmark is in
`~/.claude/plans/in-this-session-we-re-binary-teacup.md` (the
"Fix 2" section there describes the staged approach — pyproject
first, wheel + tagged release second).

---

## Issue 1 — Console-script entry point points at a missing symbol

**Location**: `pyproject.toml` declares
`[project.scripts]` → `vconverge = "vconverge.vconverge:main"`,
mirroring what the old `setup.py` had.

**Problem**: `vconverge/vconverge.py` does **not** define a
`main()` function. The current top-level code reads
`sys.argv[1]` and runs the convergence loop at import time:

```python
# vconverge/vconverge.py — present-day shape
...
cdic, conved = vconverge(sys.argv[1])
```

So `pip install -e .` succeeds and drops a `vconverge` command on
PATH, but invoking it crashes with:

```
AttributeError: module 'vconverge.vconverge' has no attribute 'main'
```

**When this matters**: only when someone runs `vconverge <input>`
from the shell. Scripts that `import vconverge.vconverge` and call
the function directly are unaffected. The GJ 1132 XUV pipeline
currently invokes vconverge via Python imports, so this is dormant
for the benchmark workflow.

**Fix**: wrap the side-effecting bottom of `vconverge.py` in a
`main()` function and replace the bottom block with
`if __name__ == "__main__": main()`. Roughly:

```python
def main():
    sInputFile = sys.argv[1]
    cdic, conved = vconverge(sInputFile)
    # ...whatever side effects belong at the bottom

if __name__ == "__main__":
    main()
```

After that, the entry-point string in `pyproject.toml` resolves
correctly.

---

## Issue 2 — `vconverge/__init__.py` is missing

**Problem**: There is no `vconverge/__init__.py`, so `import
vconverge` succeeds (Python treats the directory as a namespace
package) but `vconverge.__version__` isn't exposed. The
`setuptools_scm` config writes
`vconverge/vconverge_version.py` correctly on every install — that
file does exist after `pip install -e .` — but nothing imports
`__version__` from it into the `vconverge` namespace.

**When this matters**: any caller that does
`vconverge.__version__` for diagnostics, logging, or
reproducibility metadata gets `AttributeError`. Vaibify's
environment-snapshot capture (Tier 3 of the AICS L3 envelope) would
benefit from a working `__version__` here.

**Fix**: create `vconverge/__init__.py` with:

```python
"""vconverge — VPLANET parameter sweep and convergence helper."""

from vconverge.vconverge_version import __version__

__all__ = ["__version__"]
```

Commit it. Make sure `vconverge_version.py` stays gitignored (it's
auto-generated).

---

## Issue 3 — Undeclared runtime dependency on `bigplanet`

**Problem**: `vconverge/vconverge.py` does
`import bigplanet as bp` (or similar) at module top, but
`pyproject.toml`'s `[project].dependencies` lists only
`numpy`, `matplotlib`, `astropy`. `bigplanet` is missing.

**When this matters**: a fresh `pip install vconverge` into a
clean environment (no bigplanet) succeeds at install time, then
crashes with `ModuleNotFoundError: No module named 'bigplanet'` at
the first `import vconverge.vconverge`. In the GJ 1132 XUV
container this is invisible because the entrypoint installs
bigplanet alongside vconverge.

**Fix**: add `bigplanet` to `[project].dependencies` in
`pyproject.toml`. (If bigplanet is also private/unreleased, this
shifts the AICS L3 problem one repo deeper; pin to a git URL or
vendor the wheel under that path too.)

---

## When you're ready to ship vconverge for AICS L3

The full sequence — for context when you return:

1. **Fix the three issues above** (each independent).
2. **Tag a release** in vconverge — `v0.1.0` or similar. Any
   stable identifier works; PyPI publication is not required.
3. **Build a wheel** from that tag:
   `python -m build` produces a deterministic
   `vconverge-0.1.0-py3-none-any.whl` under `dist/`.
4. **Pin the wheel by hash** in the GJ 1132 XUV project's
   `requirements.in` so `uv pip compile --generate-hashes`
   records its SHA-256. Two delivery options:
   - **Vendored**: commit the wheel under
     `GJ1132_XUV/wheels/` and reference it as
     `vconverge @ file:./wheels/vconverge-0.1.0-py3-none-any.whl`.
     Bytes live in `MANIFEST.sha256`. Simplest.
   - **GitHub Release asset**: attach the wheel to the tag's
     Release, reference by URL. Cleaner if other projects ever
     depend on vconverge directly.
5. **Update the GJ 1132 XUV `vaibify.yml`** to reference the
   pinned vconverge instead of cloning from `main` (the entrypoint
   would need a small extension to support wheel-pinned repos
   alongside its current git-clone-and-pip-install flow). This
   is the deepest part of the work and may be deferred until other
   currently-cloned dependencies face the same question.

Until then, vconverge can stay at `installMethod: pip_editable`
and clone from `main` — the workflow runs, just not at L3 strict
bit-level reproducibility.
