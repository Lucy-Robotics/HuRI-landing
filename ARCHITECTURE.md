# HuRI architecture

How the pieces fit, as built. The design and its rationale are in the refactor
epic ([huri-core#93](https://github.com/Lucy-Robotics/huri-core/issues/93)).

## Where each piece lives

| Repository | Holds | Depends on |
|---|---|---|
| [huri-core](https://github.com/Lucy-Robotics/huri-core) | the abstract framework: base classes, bus, server, plugin loader, checks, client SDK, `huri hub`, `huri_core.testing` | nothing of HuRI's |
| [huri-modules](https://github.com/Lucy-Robotics/huri-modules) | `packages/huri-events`, the curated `packages/huri-module-*` (+ `huri-tts`), `registry.toml`, `modules/<name>` submodules for verified third-party modules, install and deploy, the reference client in `examples/cli` | `huri-core`, at the ref in its `HURI_CORE_REF` file |
| [huri-plugin-template](https://github.com/Lucy-Robotics/huri-plugin-template) | a starter module package, with its tests and CI | `huri-core` + `huri-events` |
| [HuRI](https://github.com/Lucy-Robotics/HuRI) | these pages | nothing |

`huri-core` is complete and fully tested without any module or curated event:
its tests define their own toy events and modules. The curated vocabulary,
`huri-events`, lives in `huri-modules`, next to the modules that use it, and
changes with them.

## Layers

```
use cases       huri-cli, a website backend, a robot ...   ── client SDK ──┐
                                                                            │ websocket
huri-core       Module / EventData base classes, bus, server,             ◄┘
                plugin loader, compatibility checks, client SDK, testing
                  ▲ entry points ("huri.modules", "huri.events")
event packages  huri-events (huri.*), third-party (acme.*)
module packages huri-module-stt, huri-module-rag, ... , third-party modules
```

Dependencies point one way, with no cycle:

```
use case    ──► huri-core[client] + huri-events (or another event package)
module      ──► huri-core[server] + huri-events (or another event package)
huri-events ──► huri-core
```

`huri-core` knows no concrete module or event: it moves bytes and JSON and calls
`from_wire` / `to_wire`. Its extras keep clients light: `huri-core[client]` is
websockets + YAML loading, `huri-core[server]` is Ray Serve + FastAPI and the
pins that keep them working.

## Modules and events are plugins

A package registers what it provides in its `pyproject.toml`:

```toml
[project.entry-points."huri.modules"]
stt = "huri_stt.module:STT"

[project.entry-points."huri.events"]
"huri.transcript" = "huri_events.speech:Transcript"
```

Installing it is all it takes. The server loads modules
(`huri_core/core/plugins.py`) only if its operator enables them:
`HURI_MODULES` is a **default-deny** allow-list — unset enables nothing — and
it may also name an unpackaged module by import path
(`my_pkg.servo:Servo`, "tier 0"), which a client can then use with
`module: my_pkg.servo:Servo`. A client can never make the server import code
the server did not list.

**Topics are namespaced**, `<namespace>.<name>`. `huri.` belongs to
`huri-events`; every other package registers its topics under one namespace of
its own, which no other package may use. A replacement for a curated event
(`acme.motion`) lives next to it instead of overriding it, and a module's
topics are part of what it is: a module consuming `acme.motion` is a different
module, wired instead of the old one.

## Checks before anything runs

- **At startup** (`build_app`, before deploying): every enabled module's topics
  are registered by an installed event package, with the event classes the
  module declares (`input_event` / `output_event`); and, for a module shipping a
  `huri_module.toml` manifest, the manifest agrees with the class and the
  installed `huri-core` and event packages are within its declared ranges.
- **Per session**: every module input is produced by another module or by the
  client, and every topic the client subscribes to is emitted.

Failures say which module, which topic, and which package is probably missing.

**Actuation.** A module that can drive physical hardware declares it
(`requires.actuation` in its manifest, or `actuation = True` on its class); the
server will not start with it unless the operator also lists it in
`HURI_ACTUATION_MODULES`. Enabling a module is not consenting to it moving a
robot, and neither is a verified mark.

## A session

The client sends a handshake — `user_id`, `modules`, the topics it will `send`
and those it will `subscribe` to — and gets `session_init`, or `session_error`
with the reason. Events then travel as JSON frames or binary frames
`[u16 topic length][topic][payload]`. On the server, the event bus runs each
module on its input topic and publishes what it emits; a `Sender` per
subscribed topic forwards to the client. The SDK delivers each topic's events
to its handlers in order.

Heavy models run as Ray Serve deployments (`ModuleWithHandle`); module code
imports their libraries lazily, so the head node can import every module to
build the app whatever its hardware.

## Building and trusting modules

| Tier | What | Review |
|---|---|---|
| 0 | an import path listed in `HURI_MODULES` | none |
| 1 | a pip-installable package with entry points | none |
| 2 | discoverable (GitHub topic `huri-module`), found by `huri hub search` / `list` | none; `huri hub install` refuses it unless asked explicitly |
| 3 | listed in the `huri-modules` [registry](https://github.com/Lucy-Robotics/huri-modules/blob/main/registry.toml) — "verified" | a pull request, CI-checked ([ACCEPTANCE.md](https://github.com/Lucy-Robotics/huri-modules/blob/main/ACCEPTANCE.md)) |

A tier-3 entry's `source` says where its reviewed code is:

- a curated, first-party module lives in `huri-modules` itself:
  `source = { path = "packages/huri-module-stt" }`, installed as
  `git+https://github.com/Lucy-Robotics/huri-modules.git@<ref>#subdirectory=packages/huri-module-stt`;
- a verified third-party module stays in its author's repository, and
  `huri-modules` pins the reviewed tag as a git submodule:
  `source = { git = "https://github.com/acme/huri-module-servo", tag = "0.1.0", submodule = "modules/servo" }`
  (optionally `subdirectory = "<dir>"`), installed as `git+<git>@<tag>`. The
  submodule under `modules/<name>` must be checked out at that tag, so what CI
  tests is what users install.

`huri hub` (in `huri-core`) reads that registry from `huri-modules` at the ref
in `HURI_MODULES_REF` (default `main`, the latest release) and installs curated
modules from the same repository and ref. `--registry PATH|URL`, `HURI_REGISTRY`
or a local `huri-modules` checkout point it elsewhere.

A module is tested alone with `huri_core.testing` (`ModuleHarness`, and
`LocalHandle` standing in for a deployment); `huri-modules` runs the whole
curated pipeline together (`tests/integration`).

## Installing

Each module package declares its dependencies, and exact pins per hardware
variant in `requirements-{cpu,nvidia,amd}.txt`. The `huri-modules` installer
merges them for the planned modules and stops on conflicting pins before
installing anything heavy; its Docker images install every curated package and
fail to build if modules and events do not fit together. Both install
`huri-core` from the ref in `HURI_CORE_REF` — or, for a developer working on
both repositories, from a local checkout named by `HURI_CORE_PATH`.

## Versions, and how a core change propagates

- **huri-core**: semver, tags `X.Y.Z` (no `v`), `dev` → `main`, the version in
  `huri_core/__init__.py`. While `0.x`, a minor bump may break the public
  surface (base classes, client SDK and config schema, wire protocol, entry
  point groups and manifest); a patch must not.
- **huri-modules**: its own semver and tags, same branches. A release is a
  tested set: every package (each with its own version in its
  `pyproject.toml`) and the one `huri-core` ref in `HURI_CORE_REF`. Packages
  pin `huri-core` to one minor range (`>=0.4,<0.5` from
  `huri-core` 0.4.0 on); a wire-format change in
  `huri-events` is a minor bump while `0.x`.
- **huri-plugin-template**: `main` only; its CI installs `huri-core` and
  `huri-events` from `HURI_CORE_REF` and `HURI_MODULES_REF`.

| huri-modules | huri-core |
|---|---|
| 0.1.x | 0.4.x |

A change to the core reaches the modules in four steps, none of them silent:

1. `huri-core` merges it on `dev`, and tags a release on `main`.
2. `huri-modules` CI runs every package against the pinned `HURI_CORE_REF`
   (blocking) and against `huri-core` `dev` (a non-blocking canary): a breaking
   core change shows up there before it is released.
3. A `huri-modules` pull request bumps `HURI_CORE_REF` to the new tag (and the
   packages' `huri-core` range on a minor bump), with whatever fixes the
   modules need.
4. `huri-modules` releases: a new tested set, and a new row in the table above.

Details: [huri-core's RELEASING.md](https://github.com/Lucy-Robotics/huri-core/blob/main/RELEASING.md),
[huri-modules' RELEASING.md](https://github.com/Lucy-Robotics/huri-modules/blob/main/RELEASING.md).
