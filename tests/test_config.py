"""Tests for YAML configuration feature."""

from pathlib import Path

import pytest
import yaml

from register_apps import config


def test_load_config_valid(tmpdir):
    """Test loading a valid configuration file."""
    config_file = Path(tmpdir) / "apps.yaml"
    config_data = {
        "defaults": {
            "bindir": "/tmp/bin",
            "optdir": "/tmp/opt",
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

    loaded = config.load_config(config_file)
    assert loaded == config_data


def test_load_config_missing_file():
    """Test loading a non-existent configuration file."""
    with pytest.raises(FileNotFoundError):
        config.load_config(Path("/nonexistent/path/apps.yaml"))


def test_load_config_empty(tmpdir):
    """Test loading an empty configuration file."""
    config_file = Path(tmpdir) / "apps.yaml"
    config_file.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="Configuration file is empty"):
        config.load_config(config_file)


def test_validate_config_missing_defaults(tmpdir):
    """Test validation with missing defaults."""
    config_data = {"apps": []}
    with pytest.raises(ValueError, match="Missing 'defaults' section"):
        config.validate_config(config_data)


def test_validate_config_missing_apps(tmpdir):
    """Test validation with missing apps."""
    config_data = {"defaults": {}}
    with pytest.raises(ValueError, match="Missing 'apps' section"):
        config.validate_config(config_data)


def test_validate_config_empty_apps(tmpdir):
    """Test validation with empty apps list."""
    config_data = {"defaults": {}, "apps": []}
    with pytest.raises(ValueError, match="'apps' list is empty"):
        config.validate_config(config_data)


def test_validate_app_invalid_type():
    """Test validation with invalid app type."""
    app = {"type": "invalid"}
    with pytest.raises(ValueError, match="Invalid app type"):
        config.validate_app(app)


def test_validate_app_container_missing_fields():
    """Test validation of container app with missing required fields."""
    app = {"type": "container"}
    with pytest.raises(ValueError, match="requires either 'image_repository' or 'image_url'"):
        config.validate_app(app)


def test_validate_app_toil_missing_fields():
    """Test validation of toil app with missing required fields."""
    app = {"type": "toil"}
    with pytest.raises(ValueError, match="requires 'pypi_name'"):
        config.validate_app(app)


def test_validate_app_python_missing_fields():
    """Test validation of python app with missing required fields."""
    app = {"type": "python"}
    with pytest.raises(ValueError, match="requires 'pypi_name'"):
        config.validate_app(app)


def test_merge_defaults():
    """Test merging app config with defaults."""
    defaults = {"bindir": "/tmp/bin", "optdir": "/tmp/opt", "force": True}
    app = {"type": "container", "target": "test", "force": False}

    merged = config.merge_defaults(app, defaults)
    assert merged["bindir"] == "/tmp/bin"
    assert merged["optdir"] == "/tmp/opt"
    assert merged["force"] is False  # App value overrides default
    assert merged["type"] == "container"
    assert merged["target"] == "test"


def test_get_apps_by_type():
    """Test filtering apps by type."""
    cfg = {
        "defaults": {},
        "apps": [
            {"type": "container", "target": "tool1"},
            {"type": "toil", "pypi_name": "tool2"},
            {"type": "python", "pypi_name": "tool3"},
            {"type": "container", "target": "tool4"},
        ],
    }

    containers = config.get_apps_by_type(cfg, "container")
    assert len(containers) == 2
    assert all(app["type"] == "container" for app in containers)

    toil = config.get_apps_by_type(cfg, "toil")
    assert len(toil) == 1
    assert toil[0]["pypi_name"] == "tool2"

    all_apps = config.get_apps_by_type(cfg, None)
    assert len(all_apps) == 4

