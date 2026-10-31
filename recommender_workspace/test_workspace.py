"""Behaviour checks for the private/public data boundary."""

import importlib.util
from pathlib import Path
import subprocess

import pytest

from consumption_certainty.record import load_certainty_map
from finding_cache.store import write_finding
from recommender_workspace.paths import PACKAGE_ROOT, private_path
from recommender_workspace.setup import init_workspace


def test_blank_workspace_has_no_consumption_and_rerun_preserves_answers(tmp_path):
    workspace = tmp_path / "private"
    assert len(init_workspace(workspace)) == 3
    record = workspace / "taste/grilling-record.md"
    assert load_certainty_map(record) == {}
    record.write_text(record.read_text() + "\nAn explicitly private answer.\n")
    (workspace / "sources.md").write_text("Private source additions\n")

    assert init_workspace(workspace) == []
    assert record.read_text().endswith("An explicitly private answer.\n")
    assert (workspace / "sources.md").read_text() == "Private source additions\n"


def test_workspace_inside_package_is_rejected_before_any_write():
    with pytest.raises(ValueError, match="outside"):
        init_workspace(PACKAGE_ROOT / "personal")
    assert not (PACKAGE_ROOT / "personal").exists()


def test_symlink_into_package_is_rejected(tmp_path):
    linked = tmp_path / "linked"
    linked.symlink_to(PACKAGE_ROOT, target_is_directory=True)
    with pytest.raises(ValueError, match="outside"):
        private_path(linked / "taste/record.md")


def test_existing_workspace_cannot_route_new_records_into_package(tmp_path):
    (tmp_path / "taste").symlink_to(PACKAGE_ROOT / "templates", target_is_directory=True)
    with pytest.raises(ValueError, match="outside"):
        init_workspace(tmp_path)
    assert not (tmp_path / "sources.md").exists()


@pytest.mark.parametrize("via_link", [False, True])
def test_finding_writer_rejects_public_directory(tmp_path, via_link):
    destination = PACKAGE_ROOT / "findings"
    if via_link:
        (tmp_path / "linked").symlink_to(PACKAGE_ROOT, target_is_directory=True)
        destination = tmp_path / "linked/findings"
    record = dict(finding_id="example", kind="living_list", payload={},
                  source_refs=[], fetched_at="2026-01-01T00:00:00+00:00",
                  max_age_seconds=1, status="active")
    with pytest.raises(ValueError, match="outside"):
        write_finding(destination, record)
    assert not (PACKAGE_ROOT / "findings").exists()


def test_checker_rejects_ignored_personal_files_and_links(tmp_path):
    spec = importlib.util.spec_from_file_location("public_check", PACKAGE_ROOT / "scripts/check_public.py")
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    (tmp_path / "PUBLIC_FILES.txt").write_text("PUBLIC_FILES.txt\nSKILL.md\n")
    (tmp_path / "SKILL.md").write_text("Generic instructions\n")
    assert checker.check_tree(tmp_path) == []

    (tmp_path / "private-record.md").write_text("Personal answer\n")
    assert any("outside publication allowlist" in p for p in checker.check_tree(tmp_path))
    (tmp_path / "private-record.md").unlink()
    (tmp_path / "leak").symlink_to(tmp_path / "SKILL.md")
    assert any("symlink" in p for p in checker.check_tree(tmp_path))


def test_checker_flags_private_content_without_echoing_it(tmp_path):
    spec = importlib.util.spec_from_file_location("public_check", PACKAGE_ROOT / "scripts/check_public.py")
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    (tmp_path / "PUBLIC_FILES.txt").write_text("PUBLIC_FILES.txt\nSKILL.md\n")
    secret_path = "/" + "Users" + "/example-person/private/record.md"
    (tmp_path / "SKILL.md").write_text(secret_path)
    problems = checker.check_tree(tmp_path)
    assert problems == ["possible private content: SKILL.md"]
    assert all(secret_path not in message for message in problems)


def test_checker_inspects_staged_and_historical_content(tmp_path):
    spec = importlib.util.spec_from_file_location("public_check", PACKAGE_ROOT / "scripts/check_public.py")
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)

    def git(*args):
        return subprocess.run(
            ["git", "-C", str(tmp_path), "-c", "user.name=Example Maintainer",
             "-c", "user.email=example@example.test", *args],
            check=True, capture_output=True,
        )

    git("init", "-b", "main")
    (tmp_path / "PUBLIC_FILES.txt").write_text("PUBLIC_FILES.txt\nSKILL.md\n")
    (tmp_path / "SKILL.md").write_text("Generic instructions\n")
    git("add", "PUBLIC_FILES.txt", "SKILL.md")
    git("-c", "core.hooksPath=/dev/null", "commit", "-m", "Generic test fixture")
    assert checker.check_git(tmp_path) == []

    (tmp_path / "SKILL.md").write_text("/" + "Users" + "/example-person/private/record.md")
    git("add", "SKILL.md")
    (tmp_path / "SKILL.md").write_text("Generic working copy\n")
    assert any("private content in tracked" in p for p in checker.check_git(tmp_path))

    git("-c", "core.hooksPath=/dev/null", "commit", "-m", "Synthetic boundary test")
    git("add", "SKILL.md")
    git("-c", "core.hooksPath=/dev/null", "commit", "-m", "Restore generic content")
    assert any("private content in committed" in p for p in checker.check_git(tmp_path))
