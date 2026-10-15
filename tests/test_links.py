"""These pages' links resolve, and the checker catches broken ones."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("check_links", ROOT / "check_links.py")
assert spec and spec.loader
check_links = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_links)


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
        "[home](https://github.com/Lucy-Robotics/HuRI)\n"
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
        "pip install git+https://github.com/Lucy-Robotics/huri.git\n"
        "```\n"
    )
    problems = check_links.check_file(page, external=False)
    assert len(problems) == 2
    assert "unknown repository Lucy-Robotics/huri-events" in problems[0]
    assert "unknown repository Lucy-Robotics/huri (" in problems[1]


def test_installing_from_the_showcase_is_reported(tmp_path):
    page = tmp_path / "page.md"
    page.write_text(
        "```sh\n"
        'pip install "git+https://github.com/Lucy-Robotics/HuRI.git@0.3.0"\n'
        "```\n"
    )
    (problem,) = check_links.check_file(page, external=False)
    assert "holds no code" in problem


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
