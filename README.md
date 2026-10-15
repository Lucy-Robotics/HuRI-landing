# HuRI

**HuRI** is a realtime, modular conversational pipeline for robots and
avatars: speech in, an answer out as text, a voice and gestures. A server (Ray
Serve) runs a pipeline of **modules** — voice activity detection,
speech-to-text, emotion, retrieval-augmented answers, text-to-speech, gesture
generation — wired by **topics**; clients connect over a websocket and pick the
modules of their session.

Everything is a plugin: any pip-installable package can add a module or an
event type, without touching the framework.

This repository, `HuRI-landing`, holds no code: it is the front page of the
HuRI projects. The framework's repository was called `Lucy-Robotics/HuRI`
before the split; it is now
[huri-core](https://github.com/Lucy-Robotics/huri-core), and GitHub redirects
the old URL there.

## The pipeline

Each arrow is a topic (`huri.*`, defined by `huri-events`); each box is a
module, enabled by the server's operator and chosen per session by the client.

```
client (microphone)
   │ huri.audio.in
   ▼
  VAD
   │ huri.voice
   ├─────────────────────────┐
   ▼                         ▼
  STT                       EMO
   │ huri.transcript         │ huri.emotion
   ▼                         ▼
  TAG                       EAG
   │ huri.partial_question   │ huri.partial_question
   └────────────┬────────────┘
                ▼
               QAG
                │ huri.question
                ▼
               RAG ── huri.token ─────► client (text)
                │ huri.token
                ▼
               TTS ── huri.audio.out ─► client (voice)
                │ huri.audio.out
                ▼
               MOV ── huri.motion ────► client (gestures)
```

A client subscribes to the topics it wants back — the answer's tokens as they
stream, the synthesized voice, the gestures, or a transcript, an emotion — and
the server checks, per session, that every one of them is produced.

## Start here

| You want to… | Go to | You need |
|---|---|---|
| **Try it** — a working pipeline, fast | [huri-modules](https://github.com/Lucy-Robotics/huri-modules) — `install.sh` on this machine | that repository only |
| **Deploy** — run a chosen set of modules somewhere | [huri-modules](https://github.com/Lucy-Robotics/huri-modules) — `install.sh` (bare metal), [deploy/](https://github.com/Lucy-Robotics/huri-modules/tree/main/deploy) (Docker) or [helm/](https://github.com/Lucy-Robotics/huri-modules/tree/main/helm) (Kubernetes) | that repository only |
| **Build a module** — write or change one module, alone | [huri-plugin-template](https://github.com/Lucy-Robotics/huri-plugin-template) ("Use this template") | `huri-core` + `huri-events`; no GPU, no running pipeline |
| **Write a client** — a website, a robot, a CLI | the [huri-core client SDK](https://github.com/Lucy-Robotics/huri-core#client-sdk) and [huri-cli](https://github.com/Lucy-Robotics/huri-modules/tree/main/examples/cli), the reference client | `huri-core[client]` + [huri-events](https://github.com/Lucy-Robotics/huri-modules/tree/main/packages/huri-events) |
| **Understand the framework** — bus, server, plugins, checks | [huri-core](https://github.com/Lucy-Robotics/huri-core), and [ARCHITECTURE.md](ARCHITECTURE.md) here | nothing |

## The pieces

| Repository | What it is |
|---|---|
| [huri-core](https://github.com/Lucy-Robotics/huri-core) | the framework: module and event base classes, bus, server, plugin loader, compatibility checks, client SDK, `huri hub`, `huri_core.testing`; no concrete module or event, and fully testable without any |
| [huri-modules](https://github.com/Lucy-Robotics/huri-modules) | the curated set, released and tested together: the registry of verified modules, install and deploy (`install.sh`, Docker, Helm), and the packages below |
| ↳ [huri-events](https://github.com/Lucy-Robotics/huri-modules/tree/main/packages/huri-events) | the curated event vocabulary, one class per `huri.*` topic |
| ↳ [huri-module-vad](https://github.com/Lucy-Robotics/huri-modules/tree/main/packages/huri-module-vad) | voice activity detection (WebRTC) |
| ↳ [huri-module-stt](https://github.com/Lucy-Robotics/huri-modules/tree/main/packages/huri-module-stt) | speech to text (faster-whisper) |
| ↳ [huri-module-tag](https://github.com/Lucy-Robotics/huri-modules/tree/main/packages/huri-module-tag) | transcript stitching |
| ↳ [huri-module-emo](https://github.com/Lucy-Robotics/huri-modules/tree/main/packages/huri-module-emo) | speech emotion, and its aggregator |
| ↳ [huri-module-rag](https://github.com/Lucy-Robotics/huri-modules/tree/main/packages/huri-module-rag) | answers from long-term memory (Qdrant + an LLM), and the question aggregator |
| ↳ [huri-tts](https://github.com/Lucy-Robotics/huri-modules/tree/main/packages/huri-tts), [huri-module-tts-piper](https://github.com/Lucy-Robotics/huri-modules/tree/main/packages/huri-module-tts-piper), [huri-module-tts-cosyvoice](https://github.com/Lucy-Robotics/huri-modules/tree/main/packages/huri-module-tts-cosyvoice) | text to speech: shared streaming logic, the default Piper engine, CosyVoice3 voice cloning |
| ↳ [huri-module-mov](https://github.com/Lucy-Robotics/huri-modules/tree/main/packages/huri-module-mov) | co-speech gestures (EMAGE) |
| ↳ [huri-cli](https://github.com/Lucy-Robotics/huri-modules/tree/main/examples/cli) | the reference command-line client |
| [huri-plugin-template](https://github.com/Lucy-Robotics/huri-plugin-template) | starter for a new module (a GitHub template repository) |
| [HuRI-landing](https://github.com/Lucy-Robotics/HuRI-landing) | this page: what HuRI is, how the pieces fit, where to contribute |

Each piece installs straight from git, at a tag or a branch (`<ref>`):

```sh
pip install "huri-core[server] @ git+https://github.com/Lucy-Robotics/huri-core.git@<ref>"   # or [client], [dev]
pip install "huri-events @ git+https://github.com/Lucy-Robotics/huri-modules.git@<ref>#subdirectory=packages/huri-events"
pip install "git+https://github.com/Lucy-Robotics/huri-modules.git@<ref>#subdirectory=packages/huri-module-stt"
pip install "git+https://github.com/Lucy-Robotics/huri-modules.git@<ref>#subdirectory=examples/cli"
```

## Versions

`huri-core` and `huri-modules` are versioned separately: semver, tags `X.Y.Z`
(no `v`), work on `dev`, releases on `main`. A `huri-modules` release is a
tested set — every curated package together with the one `huri-core` ref they
were built and tested against, written in its `HURI_CORE_REF` file.

| huri-modules | huri-core |
|---|---|
| 0.1.x | 0.4.x |

How each repository releases: [huri-core's RELEASING.md](https://github.com/Lucy-Robotics/huri-core/blob/main/RELEASING.md)
and [huri-modules' RELEASING.md](https://github.com/Lucy-Robotics/huri-modules/blob/main/RELEASING.md).
How a core change reaches the modules: [ARCHITECTURE.md](ARCHITECTURE.md#versions-and-how-a-core-change-propagates).

Read next: [ARCHITECTURE.md](ARCHITECTURE.md) — how the pieces fit — and
[CONTRIBUTING.md](CONTRIBUTING.md) — where to open what.
