"""Tests for install command."""

from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from register_apps import cli


@pytest.fixture
def sample_config(tmpdir):
    """Create a sample YAML configuration file."""
    config_file = Path(tmpdir) / "apps.yaml"
    config_data = {
        "defaults": {
            "bindir": str(Path(tmpdir) / "bin"),
            "optdir": str(Path(tmpdir) / "opt"),
            "force": True,
        },
        "apps": [
            {
                "type": "container",
                "target": "test_tool",
                "image_repository": "test_repo",
                "image_version": "v1.0.0",
            }
        ],
    }
    config_file.write_text(yaml.dump(config_data), encoding="utf-8")
    return config_file


def test_install_dry_run(sample_config):
    """Test install command with dry-run flag."""
    runner = CliRunner()
    result = runner.invoke(
        cli.install,
        ["--config", str(sample_config), "--dry-run"],
    )

    assert result.exit_code == 0
    assert "DRY RUN" in result.output
    assert "test_tool" in result.output


def test_install_missing_config():
    """Test install command with missing config file."""
    runner = CliRunner()
    result = runner.invoke(
        cli.install,
        ["--config", "/nonexistent/path/apps.yaml"],
    )

    assert result.exit_code != 0


def test_install_invalid_config(tmpdir):
    """Test install command with invalid config."""
    config_file = Path(tmpdir) / "apps.yaml"
    config_file.write_text("invalid: yaml: content: [", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli.install,
        ["--config", str(config_file)],
    )

    assert result.exit_code != 0


@pytest.mark.parametrize(
    "filter_type,expected_tools,excluded_tools",
    [
        ("container", ["tool1"], ["tool2", "tool3"]),
        ("toil", ["tool2"], ["tool1", "tool3"]),
        ("python", ["tool3"], ["tool1", "tool2"]),
        ("all", ["tool1", "tool2", "tool3"], []),
    ],
)
def test_install_filter(tmpdir, filter_type, expected_tools, excluded_tools):
    """Test install command with different filters."""
    config_file = Path(tmpdir) / "apps.yaml"
    config_data = {
        "defaults": {
            "bindir": str(Path(tmpdir) / "bin"),
            "optdir": str(Path(tmpdir) / "opt"),
        },
        "apps": [
            {
                "type": "container",
                "target": "tool1",
                "image_repository": "repo",
                "image_version": "v1",
            },
            {"type": "toil", "pypi_name": "tool2", "pypi_version": "v1"},
            {"type": "python", "pypi_name": "tool3", "pypi_version": "v1"},
        ],
    }
    config_file.write_text(yaml.dump(config_data), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli.install,
        ["--config", str(config_file), "--filter", filter_type, "--dry-run"],
    )

    assert result.exit_code == 0
    for tool in expected_tools:
        assert tool in result.output
    for tool in excluded_tools:
        assert tool not in result.output


def test_install_multiple_apps(tmpdir):
    """Test install command with multiple apps."""
    config_file = Path(tmpdir) / "apps.yaml"
    config_data = {
        "defaults": {
            "bindir": str(Path(tmpdir) / "bin"),
            "optdir": str(Path(tmpdir) / "opt"),
        },
        "apps": [
            {
                "type": "container",
                "target": "tool1",
                "image_repository": "repo1",
                "image_version": "v1",
            },
            {
                "type": "container",
                "target": "tool2",
                "image_repository": "repo2",
                "image_version": "v2",
            },
        ],
    }
    config_file.write_text(yaml.dump(config_data), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli.install,
        ["--config", str(config_file), "--dry-run"],
    )

    assert result.exit_code == 0
    assert "Found 2 apps to install" in result.output


def test_install_empty_config(tmpdir):
    """Test install command with empty apps list."""
    config_file = Path(tmpdir) / "apps.yaml"
    config_data = {
        "defaults": {
            "bindir": str(Path(tmpdir) / "bin"),
            "optdir": str(Path(tmpdir) / "opt"),
        },
        "apps": [],
    }
    config_file.write_text(yaml.dump(config_data), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli.install,
        ["--config", str(config_file)],
    )

    assert result.exit_code != 0
