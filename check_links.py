#!/usr/bin/env python3
"""Check the links of these pages (run by CI).

    python check_links.py [--external] [FILE_OR_DIR ...]

Relative links must point to an existing file or directory, and a `#anchor`
into a Markdown file to one of its headings (GitHub's slugs). A URL into the
Lucy-Robotics organization, anywhere in a page (code blocks included, so the
install strings are checked too), must name one of the HuRI repositories, and
never installs from `HuRI`, which holds no code. External links are only
fetched with --external: CI should not depend on the network.
"""

import argparse
import re
import sys
import urllib.request
from pathlib import Path
from typing import Iterable, List, Optional

HERE = Path(__file__).resolve().parent
PAGES = ["README.md", "ARCHITECTURE.md", "CONTRIBUTING.md"]
ORG = "Lucy-Robotics"
# Spelled as on GitHub. HuRI is this showcase: the old monorepo of that name
# became huri-core, so a link to HuRI's code is a link to the wrong place.
REPOS = {"huri-core", "huri-modules", "huri-plugin-template", "HuRI"}

_LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)")
_FENCE = re.compile(r"(?ms)^```.*?^```")
_ORG_URL = re.compile(
    rf"(git\+)?https?://github\.com/{ORG}/"
    r"([A-Za-z0-9_.-]+?)(?:\.git)?(?=[/@#)\s\"'`]|$)"
)


def slug(heading: str) -> str:
    # GitHub: lowercase, drop punctuation but keep "-" and "_", spaces -> "-".
    text = re.sub(r"[`*]", "", heading.strip().lower())
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def anchors(path: Path) -> set:
    text = _FENCE.sub("", path.read_text())
    return {slug(m.group(1)) for m in re.finditer(r"(?m)^#+\s+(.*)$", text)}


def links(path: Path) -> Iterable[str]:
    return _LINK.findall(_FENCE.sub("", path.read_text()))


def check_org_urls(path: Path) -> List[str]:
    """Every Lucy-Robotics URL in the page names a known repository."""
    problems = []
    for match in _ORG_URL.finditer(path.read_text()):
        pip, repo = match.group(1), match.group(2)
        if repo not in REPOS:
            problems.append(
                f"{path}: {match.group(0)} -> unknown repository {ORG}/{repo} "
                f"(known: {', '.join(sorted(REPOS))})"
            )
        elif pip and repo == "HuRI":
            problems.append(
                f"{path}: {match.group(0)} -> {ORG}/HuRI holds no code; "
                "install from huri-core or huri-modules"
            )
    return problems


def check_file(path: Path, external: bool) -> List[str]:
    problems = check_org_urls(path)
    for target in links(path):
        if target.startswith(("http://", "https://")):
            if external:
                try:
                    request = urllib.request.Request(target, method="HEAD")
                    urllib.request.urlopen(request, timeout=10)
                except Exception as e:  # noqa: BLE001 - report any failure
                    problems.append(f"{path}: {target} -> {e}")
            continue
        if target.startswith("mailto:"):
            continue
        file_part, _, anchor = target.partition("#")
        resolved = (path.parent / file_part).resolve() if file_part else path
        if not resolved.exists():
            problems.append(f"{path}: {target} -> {resolved} does not exist")
        elif anchor and resolved.suffix == ".md" and anchor not in anchors(resolved):
            problems.append(f"{path}: {target} -> no heading #{anchor}")
    return problems


def markdown_files(path: Path) -> List[Path]:
    if not path.is_dir():
        return [path]
    # Skip hidden directories (.git, .venv) and anything vendored in them.
    return sorted(
        p
        for p in path.rglob("*.md")
        if not any(part.startswith(".") for part in p.relative_to(path).parts)
    )


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "paths", nargs="*", type=Path, default=[HERE / page for page in PAGES]
    )
    parser.add_argument("--external", action="store_true")
    args = parser.parse_args(argv)

    files = [f for path in args.paths for f in markdown_files(path)]
    problems = [p for f in files for p in check_file(f, args.external)]
    for problem in problems:
        print(f"- {problem}")
    print(
        f"{len(files)} file(s), "
        + ("links OK" if not problems else f"{len(problems)} broken")
    )
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
