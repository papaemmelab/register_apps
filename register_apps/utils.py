"""register_apps utils."""

import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path
from typing import List, Tuple, Union, Optional, Dict, Any

import click


def force_link(src, dst):
    """Force a link between src and dst."""
    if os.path.exists(dst):
        os.unlink(dst)
    os.link(src, dst)


def force_symlink(src, dst):
    """Force a symlink between src and dst."""
    if os.path.exists(dst):
        os.unlink(dst)
    os.symlink(src, dst)


def tar_dir(output_path, source_dir):
    """Compress a `source_dir` in `output_path`."""
    with tarfile.open(output_path, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))


def is_executable_available(executable):
    """Check if an executable is available in PATH."""
    return shutil.which(executable) is not None


def get_virtualenvwrapper_script():
    """
    Get the path to virtualenvwrapper.sh script.

    Returns:
        str: Path to virtualenvwrapper.sh script.

    Raises:
        RuntimeError: If virtualenvwrapper is not found.
    """
    # Try common locations
    possible_paths = [
        os.getenv("VIRTUALENVWRAPPER_SCRIPT"),
        "/usr/local/bin/virtualenvwrapper.sh",
        "/usr/bin/virtualenvwrapper.sh",
        os.path.expanduser("~/.local/bin/virtualenvwrapper.sh"),
    ]

    # Also try to find via which
    if is_executable_available("virtualenvwrapper.sh"):
        result = subprocess.run(
            ["which", "virtualenvwrapper.sh"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode == 0:
            possible_paths.insert(0, result.stdout.decode("utf-8").strip())

    for path in possible_paths:
        if path and os.path.exists(path):
            return path

    raise RuntimeError(
        "virtualenvwrapper is not available. "
        "Please install virtualenvwrapper and ensure VIRTUALENVWRAPPER_SCRIPT is set."
    )


def _get_virtualenvwrapper_env():
    """Get environment variables for virtualenvwrapper commands."""
    venv_env = os.environ.copy()
    venv_env.setdefault("WORKON_HOME", os.path.expanduser("~/.virtualenvs"))
    venv_env["VIRTUALENVWRAPPER_PYTHON"] = sys.executable
    return venv_env


def _build_virtualenvwrapper_cmd(script_path, command):
    """Build a bash command to run with virtualenvwrapper sourced."""
    venv_env = _get_virtualenvwrapper_env()
    return (
        f"export VIRTUALENVWRAPPER_PYTHON={sys.executable} && "
        f"export WORKON_HOME={venv_env['WORKON_HOME']} && "
        f"source {script_path} && {command}"
    )


def _run_command_with_live_output(cmd, env=None, verbose=True):
    """
    Run a command and show live output.
    
    Args:
        cmd: Command to run (list of strings).
        env: Environment variables dict (optional).
        verbose: If True, print output in real-time (default: True).
    
    Raises:
        subprocess.CalledProcessError: If command fails.
    """
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        universal_newlines=True,
        bufsize=1,  # Line buffered
    )
    
    output_lines = []
    for line in iter(process.stdout.readline, ''):
        if line:
            line = line.rstrip()
            output_lines.append(line)
            if verbose:
                click.echo(line)
    
    process.stdout.close()
    returncode = process.wait()
    
    if returncode != 0:
        output = '\n'.join(output_lines)
        raise subprocess.CalledProcessError(returncode, cmd, output=output)


def is_virtualenvwrapper_configured():
    """
    Check if virtualenvwrapper is configured and available.

    Returns:
        bool: True if virtualenvwrapper is available, False otherwise.
    """
    try:
        script_path = get_virtualenvwrapper_script()
        # Check if mkvirtualenv is available (it's a shell function)
        result = subprocess.run(
            ["/bin/bash", "-c", f"source {script_path} && type mkvirtualenv"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=5,
        )
        return result.returncode == 0
    except (RuntimeError, subprocess.TimeoutExpired, FileNotFoundError):
        return False


def create_venv_with_virtualenvwrapper(
    env_name, python_interpreter, environment="production", verbose=True
):
    """
    Create virtual environment using virtualenvwrapper.

    Args:
        env_name: Name of the virtual environment.
        python_interpreter: Python interpreter to use (e.g., 'python3', 'python2.7').
        environment: Environment name (default: 'production').
        verbose: If True, show live output (default: True).

    Raises:
        RuntimeError: If virtualenvwrapper is not available.
        subprocess.CalledProcessError: If mkvirtualenv command fails.
    """
    virtualenvwrapper_script = get_virtualenvwrapper_script()
    cmd = _build_virtualenvwrapper_cmd(
        virtualenvwrapper_script, f"mkvirtualenv -p {python_interpreter} {env_name}"
    )

    _run_command_with_live_output(
        ["/bin/bash", "-c", cmd],
        env=_get_virtualenvwrapper_env(),
        verbose=verbose,
    )


def install_package_with_virtualenvwrapper(env_name, package_spec, pre_install=None, verbose=True):
    """
    Install package in virtualenvwrapper environment.

    Args:
        env_name: Name of the virtual environment.
        package_spec: Package specification (e.g., 'package==1.0.0' or
                     'git+https://github.com/user/repo@tag#egg=package').
        pre_install: Optional list of package specs to install before main package.
        verbose: If True, show live output (default: True).

    Raises:
        RuntimeError: If virtualenvwrapper is not available.
        subprocess.CalledProcessError: If pip install command fails.
    """
    virtualenvwrapper_script = get_virtualenvwrapper_script()
    venv_env = _get_virtualenvwrapper_env()

    # Install pre-install packages if specified
    if pre_install:
        for pre_pkg in pre_install:
            cmd = _build_virtualenvwrapper_cmd(
                virtualenvwrapper_script, f"workon {env_name} && pip3 install {pre_pkg}"
            )
            _run_command_with_live_output(
                ["/bin/bash", "-c", cmd],
                env=venv_env,
                verbose=verbose,
            )

    # Install main package
    cmd = _build_virtualenvwrapper_cmd(
        virtualenvwrapper_script, f"workon {env_name} && pip install {package_spec}"
    )
    _run_command_with_live_output(
        ["/bin/bash", "-c", cmd],
        env=venv_env,
        verbose=verbose,
    )


def find_executable_in_virtualenvwrapper(env_name, command_name):
    """
    Find executable in virtualenvwrapper environment.

    Args:
        env_name: Name of the virtual environment.
        command_name: Name of the command/executable to find.

    Returns:
        str: Path to the executable.

    Raises:
        RuntimeError: If virtualenvwrapper is not available.
        FileNotFoundError: If executable is not found.
    """
    virtualenvwrapper_script = get_virtualenvwrapper_script()
    cmd = _build_virtualenvwrapper_cmd(
        virtualenvwrapper_script, f"workon {env_name} && which {command_name}"
    )

    try:
        toolpath = subprocess.check_output(
            ["/bin/bash", "-c", cmd],
            env=_get_virtualenvwrapper_env(),
            stderr=subprocess.STDOUT,
        )
        toolpath_str = toolpath.decode("utf-8").strip()
        if not toolpath_str:
            raise FileNotFoundError(
                f"Executable '{command_name}' not found in virtualenv '{env_name}'. "
                f"'which {command_name}' returned empty output."
            )
        return toolpath_str
    except subprocess.CalledProcessError as e:
        error_msg = e.stdout.decode("utf-8", errors="ignore") if e.stdout else str(e)
        raise FileNotFoundError(
            f"Executable '{command_name}' not found in virtualenv '{env_name}'. "
            f"Error: {error_msg}"
        ) from e


def normalize_volumes(volumes: Union[List[str], List[Tuple[str, str]], None]) -> List[Tuple[str, str]]:
    """
    Normalize volumes from YAML config to list of tuples.

    Handles volumes in different formats:
    - List of strings like ["/data1:/data1", "/data2:/data2"]
    - List of tuples like [("/data1", "/data1"), ("/data2", "/data2")]
    - None or empty list -> returns empty list

    Args:
        volumes: Volumes from config (can be strings or tuples).

    Returns:
        List of (source, destination) tuples.
    """
    if not volumes:
        return []

    normalized = []
    for vol in volumes:
        if isinstance(vol, str):
            # Handle string format like "/data1:/data1" or "/data1"
            if ":" in vol:
                parts = vol.split(":", 1)  # Split only on first colon
                normalized.append((parts[0], parts[1]))
            else:
                # If no colon, map to itself
                normalized.append((vol, vol))
        elif isinstance(vol, (list, tuple)) and len(vol) == 2:
            # Already a tuple/list with 2 elements
            normalized.append((vol[0], vol[1]))
        else:
            raise ValueError(f"Invalid volume format: {vol}. Expected string 'src:dest' or tuple (src, dest)")

    return normalized


def normalize_image_url(
    image_url: Optional[str],
    image_type: str,
    image_user: str,
    image_repository: str,
    image_version: str,
    image_registry: Optional[str] = None,
) -> str:
    """
    Normalize image URL based on container type.

    Args:
        image_url: Existing image URL or None.
        image_type: Container type ('docker' or 'singularity').
        image_user: Docker hub user/organization.
        image_repository: Docker repository name.
        image_version: Image version tag.
        image_registry: Optional container registry (e.g., 'quay.io', '123456789.dkr.ecr.us-east-1.amazonaws.com').

    Returns:
        str: Normalized image URL.
    """
    if not image_url:
        # Construct image URL with optional registry
        if image_registry:
            image_url = f"{image_registry}/{image_user}/{image_repository}:{image_version}"
        else:
            image_url = f"{image_user}/{image_repository}:{image_version}"

    if image_type == "singularity" and not image_url.startswith("docker://"):
        image_url = f"docker://{image_url}"
    elif image_type == "docker" and image_url.startswith("docker://"):
        image_url = image_url.replace("docker://", "")

    return image_url


def build_package_spec(pypi_name: str, pypi_version: str, github_user: Optional[str]) -> str:
    """
    Build package specification string.

    Args:
        pypi_name: Package name.
        pypi_version: Package version.
        github_user: GitHub user (optional).

    Returns:
        str: Package specification.
    """
    if github_user:
        return (
            f"git+https://github.com/{github_user}/"
            f"{pypi_name}@{pypi_version}#egg={pypi_name}"
        )
    return f"{pypi_name}=={pypi_version}"


def create_executable(optexe: Path, binexe: Path, command_parts: List[str]) -> None:
    """
    Create executable script and symlink.

    Args:
        optexe: Path to the executable script.
        binexe: Path to the symlink.
        command_parts: List of command parts to join.

    Raises:
        click.ClickException: If file operations fail.
    """
    click.echo("Creating and linking executable...")
    try:
        script_content = f"#!/bin/bash\n{' '.join(str(part) for part in command_parts)}"
        optexe.write_text(script_content)
        optexe.chmod(mode=0o755)
        force_symlink(optexe, binexe)
        click.secho(
            f"\nExecutables available at:\n" f"\n\t{str(optexe)}\n\t{str(binexe)}\n",
            fg="green",
        )
    except OSError as e:
        raise click.ClickException(f"Failed to create executable: {e}") from e


def verify_executable(
    executable_path: Path, verify_cmd: str = "--version", timeout: int = 60
) -> Tuple[bool, str, Optional[str]]:
    """
    Verify an executable by running a verification command.

    Args:
        executable_path: Path to the executable to verify.
        verify_cmd: Command to run for verification (default: "--version").
        timeout: Timeout in seconds for the verification command.

    Returns:
        Tuple of (success: bool, output: str, error: Optional[str]).
        If successful, error will be None. If failed, output may be empty and error contains the error message.
    """
    if not executable_path.exists():
        return False, "", f"Executable not found: {executable_path}"

    try:
        result = subprocess.run(
            [str(executable_path), verify_cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            universal_newlines=True,  # Compatible with Python 3.6+
        )
        output = result.stdout.strip() if result.stdout else ""
        if result.returncode == 0:
            return True, output, None
        else:
            return False, output, f"Command failed with exit code {result.returncode}"
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after {timeout} seconds"
    except Exception as e:
        return False, "", f"Error running verification: {str(e)}"


def extract_container_images(config: Dict[str, Any], filter_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Extract container image information from YAML config.

    Args:
        config: Configuration dictionary loaded from YAML.
        filter_type: Filter by app type ('container', 'toil', or None for both).

    Returns:
        List of dictionaries with container image information.
    """
    from register_apps import config as config_module

    defaults = config.get("defaults", {})
    apps = config_module.get_apps_by_type(config, filter_type if filter_type else None)

    containers = []
    for app in apps:
        app_type = app.get("type")
        if app_type not in ["container", "toil"]:
            continue

        merged = config_module.merge_defaults(app, defaults)

        # Get app name
        app_name = merged.get("name") or merged.get("target") or merged.get("pypi_name", "unknown")

        # Extract image information
        image_url = merged.get("image_url")
        image_registry = merged.get("image_registry", defaults.get("image_registry"))
        image_user = merged.get("image_user", defaults.get("image_user", "papaemmelab"))
        image_repository = merged.get("image_repository") or merged.get("pypi_name")
        image_version = merged.get("image_version") or merged.get("pypi_version")
        container_runtime = merged.get("container_runtime", defaults.get("container_runtime", "singularity"))

        # Construct image URL if not provided
        if not image_url and image_repository and image_version:
            if image_registry:
                image_url = f"{image_registry}/{image_user}/{image_repository}:{image_version}"
            else:
                image_url = f"{image_user}/{image_repository}:{image_version}"

        # Normalize for singularity (add docker:// prefix if needed)
        if container_runtime == "singularity" and image_url and not image_url.startswith("docker://"):
            image_url = f"docker://{image_url}"

        # Extract registry from image_url if not explicitly set
        if image_url and not image_registry:
            # Try to extract registry from image_url
            url_parts = image_url.replace("docker://", "").split("/")
            if len(url_parts) > 2 and "." in url_parts[0]:
                image_registry = url_parts[0]
            elif len(url_parts) > 2:
                # Might be ECR or other registry
                image_registry = url_parts[0]

        containers.append({
            "name": app_name,
            "type": app_type,
            "image_url": image_url,
            "image_registry": image_registry,
            "image_user": image_user,
            "image_repository": image_repository,
            "image_version": image_version,
            "runtime": container_runtime,
        })

    return containers


def format_container_list(containers: List[Dict[str, Any]], format_type: str = "table") -> str:
    """
    Format container list for output.

    Args:
        containers: List of container dictionaries from extract_container_images.
        format_type: Output format ('table', 'json', 'yaml', 'pull-commands', 'migration').

    Returns:
        Formatted string output.
    """
    if format_type == "json":
        import json
        return json.dumps(containers, indent=2)

    elif format_type == "yaml":
        import yaml
        return yaml.dump(containers, default_flow_style=False)

    elif format_type == "pull-commands":
        lines = []
        for container in containers:
            image_url = container.get("image_url", "")
            # Remove docker:// prefix for pull commands
            if image_url.startswith("docker://"):
                image_url = image_url.replace("docker://", "")
            if image_url:
                lines.append(f"docker pull {image_url}")
        return "\n".join(lines)

    elif format_type == "migration":
        import json
        migration_data = []
        for container in containers:
            source = container.get("image_url", "")
            if source.startswith("docker://"):
                source = source.replace("docker://", "")
            migration_data.append({
                "name": container.get("name"),
                "source": source,
                "target": source,  # User can modify this
            })
        return json.dumps(migration_data, indent=2)

    else:  # table format
        lines = []
        # Header
        lines.append(f"{'Name':<20} {'Image URL':<50} {'Version':<15} {'Registry':<20} {'Runtime':<12}")
        lines.append("-" * 120)

        for container in containers:
            name = container.get("name", "")[:18]
            image_url = container.get("image_url", "")
            if image_url.startswith("docker://"):
                image_url = image_url.replace("docker://", "")
            image_url = image_url[:48] if len(image_url) > 48 else image_url
            version = str(container.get("image_version", ""))[:13]
            registry = (container.get("image_registry") or "")[:18]
            runtime = container.get("runtime", "")[:10]

            lines.append(f"{name:<20} {image_url:<50} {version:<15} {registry:<20} {runtime:<12}")

        return "\n".join(lines)
