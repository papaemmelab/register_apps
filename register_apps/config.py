"""YAML configuration parsing and validation for register_apps."""

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


def load_config(config_path: Path) -> Dict[str, Any]:
    """
    Load and validate YAML configuration file.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        Dictionary containing the parsed configuration.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        yaml.YAMLError: If YAML parsing fails.
        ValueError: If configuration validation fails.
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not config:
        raise ValueError("Configuration file is empty")

    validate_config(config)
    return config


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate configuration schema.

    Args:
        config: Configuration dictionary to validate.

    Raises:
        ValueError: If configuration is invalid.
    """
    # Check required top-level keys
    if "defaults" not in config:
        raise ValueError("Missing 'defaults' section in configuration")
    if "apps" not in config:
        raise ValueError("Missing 'apps' section in configuration")

    if not isinstance(config["apps"], list):
        raise ValueError("'apps' must be a list")

    if not config["apps"]:
        raise ValueError("'apps' list is empty")

    # Validate each app
    for i, app in enumerate(config["apps"]):
        try:
            validate_app(app)
        except ValueError as e:
            raise ValueError(f"Invalid app at index {i}: {e}") from e


def validate_app(app: Dict[str, Any]) -> None:
    """
    Validate individual app configuration.

    Args:
        app: App configuration dictionary.

    Raises:
        ValueError: If app configuration is invalid.
    """
    if not isinstance(app, dict):
        raise ValueError("App must be a dictionary")

    app_type = app.get("type")
    if app_type not in ["container", "toil", "python"]:
        raise ValueError(
            f"Invalid app type: {app_type}. Must be one of: container, toil, python"
        )

    if app_type == "container":
        if "image_repository" not in app and "image_url" not in app:
            raise ValueError(
                "Container app requires either 'image_repository' or 'image_url'"
            )
        if "image_version" not in app and "image_url" not in app:
            raise ValueError(
                "Container app requires either 'image_version' or 'image_url'"
            )
    elif app_type == "toil":
        if "pypi_name" not in app:
            raise ValueError("Toil app requires 'pypi_name'")
        if "pypi_version" not in app:
            raise ValueError("Toil app requires 'pypi_version'")
    elif app_type == "python":
        if "pypi_name" not in app:
            raise ValueError("Python app requires 'pypi_name'")
        if "pypi_version" not in app:
            raise ValueError("Python app requires 'pypi_version'")


def merge_defaults(app: Dict[str, Any], defaults: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge app configuration with defaults.

    Args:
        app: App-specific configuration.
        defaults: Default configuration values.

    Returns:
        Merged configuration dictionary.
    """
    merged = defaults.copy()
    merged.update(app)
    # Ensure verify_after_install and force are properly merged (CLI flags can override)
    # These will be handled at the CLI level, but we ensure defaults are set
    return merged


def get_apps_by_type(
    config: Dict[str, Any], app_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get apps filtered by type.

    Args:
        config: Configuration dictionary.
        app_type: Type to filter by ('container', 'toil', 'python', or None for all).

    Returns:
        List of app configurations.
    """
    apps = config.get("apps", [])
    if app_type is None or app_type == "all":
        return apps
    return [app for app in apps if app.get("type") == app_type]
