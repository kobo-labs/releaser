import pathlib
from unittest.mock import patch

import freezegun
import pytest

from .helper import (
    COMMIT_URL,
    CZ_JSON,
    RESOURCES_DIR,
    ExpectedChangelog,
    Origin,
    git_graph,
    parse_github_output,
    run_releaser,
)


@pytest.fixture()
@freezegun.freeze_time("2024-08-01")
@patch("src.releaser.core.repository.GitRepository.get_url", return_value=COMMIT_URL)
def test_release_v010(mock_url, tmp_path) -> Origin:
    # GIVEN: Remote origin with feature commit in main branch
    origin = Origin(tmp_path)
    commit = origin.commit(".cz.json", CZ_JSON, "feat(scope1): add a new feature")

    # GIVEN: Local clone of origin
    repo_path = origin.clone().working_tree_dir

    # WHEN: Releaser is run on local clone
    run_releaser(tmp_path, repo_path)

    # THEN: Origin has release branch
    assert_repo_path = origin.clone(["v0"]).working_tree_dir

    # THEN: Git graph has expected structure
    git_graph_result = git_graph(assert_repo_path)
    assert (
        git_graph_result == (RESOURCES_DIR / "test_scenario_log_v010.txt").read_text()
    )

    # THEN: Committed file exists in release branch and has expected content
    committed_file = pathlib.Path(assert_repo_path) / ".cz.json"
    assert committed_file.exists()
    assert committed_file.read_text() == CZ_JSON

    # THEN: Changelog exists and has expected content
    actual_changelog = pathlib.Path(assert_repo_path) / "CHANGELOG.md"
    expected_changelog = ExpectedChangelog().add("commit_sha_1", str(commit))
    assert actual_changelog.read_text() == expected_changelog.render(
        "changelog_v010.md.j2"
    )

    # THEN: Github output exists and has expected content
    github_output_content = parse_github_output(tmp_path / "github_output.txt")
    assert github_output_content.get("ready") == "true"
    assert github_output_content.get("tag") == "v0.1.0"
    assert github_output_content.get("changelog", "").endswith(".md")

    return origin, expected_changelog


@pytest.fixture()
@freezegun.freeze_time("2024-08-02")
@patch("src.releaser.core.repository.GitRepository.get_url", return_value=COMMIT_URL)
def test_release_v011(mock_url, test_release_v010, tmp_path) -> Origin:
    # GIVEN: Origin with v0.1.0 released
    origin = test_release_v010[0]

    # GIVEN: Remote origin with fix commit in main branch
    commit = origin.commit("README.md", "v0.1.1", "fix: resolve a bug")

    # GIVEN: Local clone of origin
    repo_path = origin.clone().working_tree_dir

    # WHEN: Releaser is run on local clone
    run_releaser(tmp_path, repo_path)

    # THEN: Origin has release branch
    assert_repo_path = origin.clone(["v0"]).working_tree_dir

    # THEN: Git graph has expected structure
    git_graph_result = git_graph(assert_repo_path)
    assert (
        git_graph_result == (RESOURCES_DIR / "test_scenario_log_v011.txt").read_text()
    )

    # THEN: Committed file exists in release branch and has expected content
    committed_file = pathlib.Path(assert_repo_path) / "README.md"
    assert committed_file.exists()
    assert committed_file.read_text() == "v0.1.1"

    # THEN: Changelog exists and has expected content
    actual_changelog = pathlib.Path(assert_repo_path) / "CHANGELOG.md"
    expected_changelog = test_release_v010[1].add("commit_sha_2", str(commit))
    assert actual_changelog.read_text() == expected_changelog.render(
        "changelog_v011.md.j2"
    )

    # THEN: Github output exists and has expected content
    github_output_content = parse_github_output(tmp_path / "github_output.txt")
    assert github_output_content.get("ready") == "true"
    assert github_output_content.get("tag") == "v0.1.1"
    assert github_output_content.get("changelog", "").endswith(".md")

    return origin, expected_changelog


@freezegun.freeze_time("2024-08-03")
@patch("src.releaser.core.repository.GitRepository.get_url", return_value=COMMIT_URL)
def test_release_v100(mock_url, test_release_v011, tmp_path) -> None:
    # GIVEN: Origin with v0.1.1 released
    origin = test_release_v011[0]

    # GIVEN: Origin with breaking commit in main branch
    commit = origin.commit("README.md", "breaking change", "feat!: breaking change")

    # GIVEN: Local clone of origin
    repo_path = origin.clone().working_tree_dir

    # WHEN: Releaser is run on local clone
    run_releaser(tmp_path, repo_path)

    # THEN: Origin has release branch
    assert_repo_path = origin.clone(["v1"]).working_tree_dir

    # THEN: Git graph has expected structure
    git_graph_result = git_graph(assert_repo_path)
    assert (
        git_graph_result == (RESOURCES_DIR / "test_scenario_log_v100.txt").read_text()
    )

    # THEN: Committed file exists in release branch
    committed_file = pathlib.Path(assert_repo_path) / "README.md"
    assert committed_file.exists()
    assert committed_file.read_text() == "breaking change"

    # THEN: Changelog exists and has expected content
    actual_changelog = pathlib.Path(assert_repo_path) / "CHANGELOG.md"
    expected_changelog = test_release_v011[1].add("commit_sha_3", str(commit))
    assert actual_changelog.read_text() == expected_changelog.render(
        "changelog_v100.md.j2"
    )

    # THEN: Github output exists and has expected content
    github_output_content = parse_github_output(tmp_path / "github_output.txt")
    assert github_output_content.get("ready") == "true"
    assert github_output_content.get("tag") == "v1.0.0"
    assert github_output_content.get("changelog", "").endswith(".md")
