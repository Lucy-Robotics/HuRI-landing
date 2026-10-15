"""These pages' links resolve, and the checker catches broken ones."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("check_links", ROOT / "check_links.py")
assert spec and spec.loader
check_links = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_links)
GH = "https://github.com/Lucy-Robotics"


def test_pages_have_no_broken_links():
    names = ["README.md", "ARCHITECTURE.md", "CONTRIBUTING.md"]
    pages = [ROOT / name for name in names]
    assert [p.name for p in pages] == check_links.PAGES
    assert check_links.main([str(p) for p in pages]) == 0
    # The default is the same set of pages.
    assert check_links.main([]) == 0


def test_broken_paths_and_anchors_are_reported(tmp_path):
    (tmp_path / "other.md").write_text("# Real Heading\n")
    page = tmp_path / "page.md"
    page.write_text(
        "[ok](other.md) [ok](other.md#real-heading) [web](https://example.invalid/x)\n"
        "[gone](missing.md) [bad anchor](other.md#nope)\n"
        "```\n[in code](ignored.md)\n```\n"
    )
    problems = check_links.check_file(page, external=False)
    assert len(problems) == 2
    assert "missing.md" in problems[0] and "#nope" in problems[1]


def test_known_repositories_pass(tmp_path):
    page = tmp_path / "page.md"
    page.write_text(
        "[core](https://github.com/Lucy-Robotics/huri-core)\n"
        "[stt](https://github.com/Lucy-Robotics/huri-modules/tree/main/packages/x)\n"
        "[tpl](https://github.com/Lucy-Robotics/huri-plugin-template#readme)\n"
        "[home](https://github.com/Lucy-Robotics/HuRI-landing)\n"
        "```sh\n"
        "pip install git+https://github.com/Lucy-Robotics/huri-core.git@dev\n"
        "```\n"
    )
    assert check_links.check_file(page, external=False) == []


def test_unknown_repository_is_reported(tmp_path):
    page = tmp_path / "page.md"
    page.write_text(
        "[old](https://github.com/Lucy-Robotics/huri-events)\n"
        "```sh\n"
        "pip install git+https://github.com/Lucy-Robotics/huri-server.git@0.4.0\n"
        "```\n"
    )
    problems = check_links.check_file(page, external=False)
    assert len(problems) == 2
    assert "unknown repository Lucy-Robotics/huri-events" in problems[0]
    assert "unknown repository Lucy-Robotics/huri-server (" in problems[1]


def test_installing_from_the_showcase_is_reported(tmp_path):
    page = tmp_path / "page.md"
    page.write_text(
        "```sh\n"
        'pip install "git+https://github.com/Lucy-Robotics/HuRI-landing.git@0.3.0"\n'
        "```\n"
    )
    (problem,) = check_links.check_file(page, external=False)
    assert "holds no code" in problem


def test_the_old_name_is_reported(tmp_path):
    # Lucy-Robotics/HuRI was renamed to huri-core: GitHub redirects it, but
    # neither a link nor an install string should rely on the redirect.
    page = tmp_path / "page.md"
    page.write_text(
        "[home](https://github.com/Lucy-Robotics/HuRI)\n"
        "see https://github.com/lucy-robotics/huri/blob/main/README.md\n"
        "```sh\n"
        f'pip install "huri-core @ git+{GH}/HuRI.git@0.3.0"\n'
        "```\n"
    )
    problems = check_links.check_file(page, external=False)
    assert len(problems) == 3
    for problem in problems:
        assert "old name, now huri-core; use the huri-core URL" in problem


def test_repository_names_in_running_text(tmp_path):
    page = tmp_path / "page.md"
    page.write_text(
        "<https://github.com/Lucy-Robotics/huri-evnts>\n"
        "https://github.com/Lucy-Robotics/huri-evnts, here\n"
        "https://github.com/lucy-robotics/huri-evnts\n"
        "Repo https://github.com/Lucy-Robotics/huri-core.\n"
        "Lowercase org https://github.com/lucy-robotics/HURI-MODULES; fine\n"
        "<https://github.com/Lucy-Robotics/huri-core>, and\n"
        'pip install "git+https://github.com/Lucy-Robotics/huri-core.git@dev"\n'
    )
    problems = check_links.check_file(page, external=False)
    assert len(problems) == 3
    for problem in problems:
        assert "unknown repository Lucy-Robotics/huri-evnts " in problem


def test_hidden_directories_are_skipped(tmp_path):
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "vendored.md").write_text("[gone](missing.md)\n")
    (tmp_path / "page.md").write_text("# Page\n")
    assert check_links.markdown_files(tmp_path) == [tmp_path / "page.md"]


def test_github_heading_slugs():
    assert check_links.slug("Client SDK") == "client-sdk"
    assert (
        check_links.slug("Module manifest (`huri_module.toml`)")
        == "module-manifest-huri_moduletoml"
    )
    assert (
        check_links.slug("Versions, and how a core change propagates")
        == "versions-and-how-a-core-change-propagates"
    )


def test_duplicate_headings_get_numbered_anchors(tmp_path):
    (tmp_path / "other.md").write_text("# Dup\n\n## Dup\n")
    page = tmp_path / "page.md"
    page.write_text("[a](other.md#dup) [b](other.md#dup-1) [c](other.md#dup-2)\n")
    (problem,) = check_links.check_file(page, external=False)
    assert "#dup-2" in problem


def test_tilde_fences_and_inline_code_are_skipped(tmp_path):
    (tmp_path / "other.md").write_text("# Real\n\n~~~\n# Not a heading\n~~~\n")
    page = tmp_path / "page.md"
    page.write_text(
        "~~~md\n[in code](nofile.md)\n~~~\n"
        "`[inline](nofile.md)` [ok](other.md#real) [bad](other.md#not-a-heading)\n"
    )
    (problem,) = check_links.check_file(page, external=False)
    assert "#not-a-heading" in problem


def _siblings(root):
    modules = root / "huri-modules"
    (modules / "packages" / "huri-module-stt").mkdir(parents=True)
    (modules / "packages" / "huri-events").mkdir(parents=True)
    (modules / "registry.toml").write_text("")
    (modules / "README.md").write_text("# huri-modules\n## Install\n")
    (root / "huri-core").mkdir()
    (root / "huri-core" / "README.md").write_text("# huri-core\n## Client SDK\n")
    return root


def test_deep_links_resolve_against_sibling_checkouts(tmp_path):
    siblings = _siblings(tmp_path / "split")
    page = tmp_path / "page.md"
    page.write_text(
        f"[ok]({GH}/huri-modules/tree/main/packages/huri-module-stt)\n"
        f"[ok]({GH}/huri-modules/blob/main/registry.toml)\n"
        f"[ok]({GH}/huri-core#client-sdk)\n"
        f"[ok]({GH}/huri-modules/blob/main/README.md#install)\n"
        f"[ok]({GH}/huri-core/issues/93)\n"
        f"[ok]({GH}/huri-core#readme)\n"
        f"[typo]({GH}/huri-modules/tree/main/packages/huri-module-sst)\n"
        f"[anchor]({GH}/huri-core#client-sdj)\n"
        "```sh\n"
        f'pip install "huri-events @ git+{GH}/huri-modules.git@<ref>'
        '#subdirectory=packages/huri-events"\n'
        f'pip install "git+{GH}/huri-modules.git@0.1.0'
        '#subdirectory=packages/huri-evnts"\n'
        "```\n"
        f"[unchecked]({GH}/huri-plugin-template/blob/main/README.md)\n"
    )
    # Without the sibling checkouts only repository names are checked.
    assert check_links.check_file(page, external=False) == []
    problems = check_links.check_file(page, external=False, siblings=siblings)
    assert len(problems) == 4
    assert "has no packages/huri-module-sst" in problems[0]
    assert "no heading #client-sdj" in problems[1]
    assert "has no packages/huri-evnts" in problems[2]
    assert "huri-plugin-template is not checked out" in problems[3]
    assert check_links.main(["--siblings", str(siblings), str(page)]) == 1
