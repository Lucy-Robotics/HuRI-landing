# Contributing to HuRI

HuRI is four repositories; pick the line that matches what you want to change,
and open the issue or pull request there.

| You want to… | Repository | How |
|---|---|---|
| Add a module (a new capability) | your own, created from [huri-plugin-template](https://github.com/Lucy-Robotics/huri-plugin-template) | nobody's permission needed: publish it, tag it `huri-module` to be found by `huri hub`; for the verified mark, open a pull request to [huri-modules](https://github.com/Lucy-Robotics/huri-modules) adding it to `registry.toml` and pinning it as a submodule under `modules/<name>` ([ACCEPTANCE.md](https://github.com/Lucy-Robotics/huri-modules/blob/main/ACCEPTANCE.md)) |
| Add an event type | an events package of your own, in your own topic namespace (`acme.*`) | see the template's `events/`; `huri.*` is reserved for [huri-events](https://github.com/Lucy-Robotics/huri-modules/tree/main/packages/huri-events) |
| Fix or improve a curated module, or `huri-events` | [huri-modules](https://github.com/Lucy-Robotics/huri-modules) ([issues](https://github.com/Lucy-Robotics/huri-modules/issues)) | pull request on `dev` to that package under `packages/`, with tests (`huri_core.testing`); bump the package's version |
| Change install or deployment, or the reference client | [huri-modules](https://github.com/Lucy-Robotics/huri-modules) | pull request on `dev`; CI builds the images and runs a session against them |
| Change the framework (bus, server, SDK, loader, `huri hub`) | [huri-core](https://github.com/Lucy-Robotics/huri-core) ([issues](https://github.com/Lucy-Robotics/huri-core/issues)) | pull request on `dev`; mind the public surface and semver ([RELEASING.md](https://github.com/Lucy-Robotics/huri-core/blob/main/RELEASING.md)) |
| Improve the module starter | [huri-plugin-template](https://github.com/Lucy-Robotics/huri-plugin-template) | pull request on `main` |
| Improve these pages | [HuRI](https://github.com/Lucy-Robotics/HuRI) | pull request on `main`; CI runs `python check_links.py` and `pytest` |

Not sure where something belongs? Open an issue on
[huri-core](https://github.com/Lucy-Robotics/huri-core/issues) and it will be
moved.

`huri-core` and `huri-modules` run `make check` (black, isort, flake8, mypy,
pytest) in CI; run it locally first.

## Versioning, in short

- `huri-core` and `huri-modules` each follow semver, with tags `X.Y.Z` (no
  `v`) on `main` and work on `dev`. While `0.x`, a minor bump may break the
  public surface; a patch must not.
- A change to `huri-core`'s public surface is a minor bump; `huri-modules`
  sees it first in its non-blocking canary CI (against `huri-core` `dev`), then
  adopts it by bumping `HURI_CORE_REF` in a pull request.
- In `huri-modules`, each package has its own version in its `pyproject.toml`:
  bump it when the package changes. A wire-format change to `huri-events` is a
  minor bump while `0.x`.
- Working on `huri-core` and `huri-modules` together: set
  `HURI_CORE_PATH=/path/to/huri-core` and `huri-modules` installs that checkout
  (editable) instead of `HURI_CORE_REF`.

Details: [huri-core's RELEASING.md](https://github.com/Lucy-Robotics/huri-core/blob/main/RELEASING.md),
[huri-modules' RELEASING.md](https://github.com/Lucy-Robotics/huri-modules/blob/main/RELEASING.md),
and [ARCHITECTURE.md](ARCHITECTURE.md#versions-and-how-a-core-change-propagates).
