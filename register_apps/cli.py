"""
Module that contains the command line app.

Why does this file exist, and why not put this in __main__?
You might be tempted to import things from __main__ later, but that will
cause problems, the code will get executed twice:

    - When you run `python -m register_apps` python will execute
      `__main__.py` as a script. That means there won't be any
      `register_apps.__main__` in `sys.modules`.

    - When you import __main__ it will get executed again (as a module) because
      there's no `register_apps.__main__` in `sys.modules`.

Also see (1) from http://click.pocoo.org/5/setuptools/#setuptools-integration
"""

from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Dict

import click

from register_apps import config
from register_apps import options
from register_apps import utils


@click.group()
def cli():
    """Register versioned container pipelines and commands."""
    pass


def _register_toil(  # pylint: disable=R0917
    bindir,
    optdir,
    pypi_name,
    pypi_version,
    python,
    volumes,
    tmpvar,
    image_url,
    image_user,
    singularity,
    container,
    environment,
    pre_install,
    image_registry=None,
    verbose=True,
):
    """Register versioned toil container pipelines in a bin directory (internal function)."""
    # Normalize volumes to ensure they're in tuple format
    volumes = utils.normalize_volumes(volumes)

    python = shutil.which(python)
    if not python:
        raise click.ClickException("Could not determine the python path.")

    optdir = Path(optdir) / pypi_name / pypi_version
    bindir = Path(bindir)
    optexe = optdir / pypi_name
    binexe = bindir / f"{pypi_name}_{pypi_version}"
    workdir = f"{tmpvar}/{pypi_name}_{pypi_version}_`uuidgen`"

    # Normalize image URL
    image_url = utils.normalize_image_url(
        image_url, container, image_user, pypi_name, pypi_version, image_registry
    )

    # Setup directories
    optdir.mkdir(exist_ok=True, parents=True)
    bindir.mkdir(exist_ok=True, parents=True)

    # Create and setup virtual environment
    env = f"{environment}__{pypi_name}__{pypi_version}"
    click.echo(f"Creating virtual environment '{env}'...")
    utils.create_venv_with_virtualenvwrapper(env, python, environment, verbose=verbose)

    # Install package
    package_spec = utils.build_package_spec(pypi_name, pypi_version, image_user)
    
    click.echo(f"Installing package '{package_spec}'...")
    pre_install_list = list(pre_install) if pre_install else None
    utils.install_package_with_virtualenvwrapper(
        env, package_spec, pre_install=pre_install_list, verbose=verbose
    )

    # Find executable and build command
    toolpath = utils.find_executable_in_virtualenvwrapper(env, pypi_name)
    command_parts = [toolpath, '"$@"']

    if container == "singularity":
        command_parts.extend(
            [
                "--singularity",
                _get_or_create_image(optdir, singularity, image_url),
            ]
        )
    else:  # docker
        command_parts.extend(["--docker", image_url])

    command_parts.extend(
        [
            " ".join(f"--volumes {i} {j}" for i, j in volumes),
            "--workDir",
            workdir,
        ]
    )

    utils.create_executable(optexe, binexe, command_parts)


@click.command()
@options.PYPI_NAME
@options.PYPI_VERSION
@options.IMAGE_USER
@options.IMAGE_URL
@options.GITHUB_USER
@options.BINDIR
@options.OPTDIR
@options.PYTHON2
@options.TMPVAR
@options.VOLUMES
@options.SINGULARITY
@options.CONTAINER
@options.ENVIRONMENT
@click.option(
    "--pre-install",
    multiple=True,
    help=(
        "Package specifications to install before main package "
        "(can be used multiple times)"
    ),
)
def register_toil(  # pylint: disable=R0917
    pypi_name,
    pypi_version,
    bindir,
    optdir,
    python,
    volumes,
    tmpvar,
    image_url,
    image_user,
    github_user,
    singularity,
    container,
    environment,
    pre_install,
):
    """Register versioned toil container pipelines in a bin directory."""
    _register_toil(
        pypi_name=pypi_name,
        pypi_version=pypi_version,
        bindir=bindir,
        optdir=optdir,
        python=python,
        volumes=volumes,
        tmpvar=tmpvar,
        image_url=image_url,
        image_user=image_user,
        github_user=github_user,
        singularity=singularity,
        container=container,
        environment=environment,
        pre_install=pre_install,
        image_registry=None,
    )


def _register_image(  # pylint: disable=R0913,R0917
    bindir,
    command,
    force,
    image_repository,
    image_type,
    image_url,
    image_user,
    image_version,
    no_home,
    optdir,
    runtime,
    target,
    tmpvar,
    volumes,
    image_registry=None,
):
    """
    Register a container image (Docker or Singularity) as an executable.

    Creates versioned executables that run commands inside container images.
    The function sets up the directory structure, creates wrapper scripts,
    and links executables in the bin directory.

    Args:
        bindir: Directory where executable symlinks will be created.
        command: Command to execute inside the container.
        force: If True, overwrite existing targets.
        image_repository: Docker hub repository name.
        image_type: Type of container ("docker" or "singularity").
        image_url: Full image URL (optional, will be constructed if not provided).
        image_user: Docker hub user/organization name.
        image_version: Version tag of the image.
        no_home: If True, use --no-home option for Singularity.
        optdir: Directory where images and scripts will be stored.
        runtime: Path to container runtime executable.
        target: Name of the target executable to create.
        tmpvar: Environment variable for work directory.
        volumes: List of (source, destination) volume mappings.
        image_registry: Optional container registry (e.g., 'quay.io', ECR URL).

    Raises:
        click.UsageError: If targets already exist and force is False.
    """
    # Normalize volumes to ensure they're in tuple format
    volumes = utils.normalize_volumes(volumes)

    image_version = str(image_version)
    optdir = Path(optdir) / image_repository / image_version
    bindir = Path(bindir)
    optexe = optdir / target
    binexe = bindir / target
    workdir = f"{tmpvar}/${{USER}}_{image_repository}_{image_version}_`uuidgen`"

    # Normalize image URL
    image_url = utils.normalize_image_url(
        image_url, image_type, image_user, image_repository, image_version, image_registry
    )

    # Check if targets exist
    if not force and (optexe.exists() or binexe.exists()):
        raise click.UsageError(f"Targets exist, exiting...\n\t{optexe}\n\t{binexe}")

    # Setup directories
    optdir.mkdir(exist_ok=True, parents=True)
    bindir.mkdir(exist_ok=True, parents=True)

    # Build command based on container type
    if image_type == "singularity":
        image_path = _get_or_create_image(optdir, runtime, image_url)
        command_parts = [
            runtime,
            "exec",
            "--workdir",
            workdir,
            " ".join(f"--bind {i}:{j}" for i, j in volumes),
        ]
        if no_home:
            command_parts.append("--no-home")
        command_parts.extend([image_path, command, '"$@"'])
    else:  # docker
        command_parts = [
            runtime,
            "run",
            "--rm",
            "-u",
            "$(id -u):$(id -g)",
            "--workdir",
            workdir,
            " ".join(f"--volume {i}:{j}" for i, j in volumes),
        ]
        if command:
            command_parts.append("--entrypoint ''")
        command_parts.extend([image_url, command, '"$@"'])

    command_str = " ".join(filter(None, command_parts))
    utils.create_executable(optexe, binexe, [command_str])


@click.command()
@options.TARGET
@options.COMMAND
@options.IMAGE_REPOSITORY
@options.IMAGE_USER
@options.IMAGE_VERSION
@options.IMAGE_URL
@options.BINDIR
@options.OPTDIR
@options.TMPVAR
@options.VOLUMES
@options.SINGULARITY
@options.FORCE
@options.VERSION
@options.NO_HOME
def register_singularity(singularity, *args, **kwargs):
    """Register versioned singularity command in a bin directory."""
    _register_image(image_type="singularity", runtime=singularity, *args, **kwargs)


@click.command()
@options.TARGET
@options.COMMAND
@options.IMAGE_REPOSITORY
@options.IMAGE_USER
@options.IMAGE_VERSION
@options.IMAGE_URL
@options.BINDIR
@options.OPTDIR
@options.TMPVAR
@options.VOLUMES
@options.DOCKER
@options.FORCE
@options.VERSION
def register_docker(docker, *args, **kwargs):
    """Register versioned docker command in a bin directory."""
    _register_image(image_type="docker", runtime=docker, no_home=False, *args, **kwargs)


def _register_python(  # pylint: disable=R0917
    pypi_name,
    pypi_version,
    github_user,
    command,
    bindir,
    optdir,
    python,
    environment,
    pre_install,
    verbose=True,
):
    """Register versioned python pipelines in a bin directory (internal function)."""
    python = shutil.which(python)
    if not python:
        raise click.ClickException("Could not determine the python path.")

    optdir = Path(optdir) / pypi_name / pypi_version
    bindir = Path(bindir)
    optexe = optdir / pypi_name
    binexe = bindir / (command or f"{pypi_name}_{pypi_version}")

    # Setup directories
    optdir.mkdir(exist_ok=True, parents=True)
    bindir.mkdir(exist_ok=True, parents=True)

    # Create and setup virtual environment
    env = f"{environment}__{pypi_name}__{pypi_version}"
    
    click.echo(f"Creating virtual environment '{env}'...")
    utils.create_venv_with_virtualenvwrapper(env, python, environment, verbose=verbose)

    # Install package
    package_spec = utils.build_package_spec(pypi_name, pypi_version, github_user)
    
    click.echo(f"Installing package '{package_spec}'...")
    pre_install_list = list(pre_install) if pre_install else None
    utils.install_package_with_virtualenvwrapper(
        env, package_spec, pre_install=pre_install_list, verbose=verbose
    )

    # Find executable and create script
    command_name = command or pypi_name
    toolpath = utils.find_executable_in_virtualenvwrapper(env, command_name)
    cmd = [toolpath, '"$@"']

    utils.create_executable(optexe, binexe, cmd)


@click.command()
@options.PYPI_NAME
@options.PYPI_VERSION
@options.GITHUB_USER
@options.COMMAND
@options.BINDIR
@options.OPTDIR
@options.PYTHON3
@options.VERSION
@options.ENVIRONMENT
@click.option(
    "--pre-install",
    multiple=True,
    help=(
        "Package specifications to install before main package "
        "(can be used multiple times)"
    ),
)
def register_python(  # pylint: disable=R0917
    pypi_name,
    pypi_version,
    github_user,
    command,
    bindir,
    optdir,
    python,
    environment,
    pre_install,
):
    """Register versioned python pipelines in a bin directory."""
    _register_python(
        pypi_name=pypi_name,
        pypi_version=pypi_version,
        github_user=github_user,
        command=command,
        bindir=bindir,
        optdir=optdir,
        python=python,
        environment=environment,
        pre_install=pre_install,
        verbose=True,
    )


def _get_or_create_image(optdir, singularity, image_url):
    """Pull image if it's not locally available and store it."""
    # Look for existing images
    singularity_images = list(optdir.glob("*.sif")) + list(optdir.glob("*.simg"))

    if singularity_images:
        if len(singularity_images) > 1:
            click.echo(
                f"Found multiple images at {optdir}. Using {singularity_images[0]}."
            )
        click.echo(f"Image exists at: {singularity_images[0]}")
    else:
        # Pull image if not found
        subprocess.check_call(
            ["/bin/bash", "-c", f"umask 22 && {singularity} pull {image_url}"],
            cwd=optdir,
        )
        singularity_images = list(optdir.glob("*.sif")) + list(optdir.glob("*.simg"))
        if not singularity_images:
            raise FileNotFoundError(f"Image not found after pull: {optdir}")

    singularity_image = singularity_images[0]
    singularity_image.chmod(mode=0o755)
    return str(singularity_image)


@click.command()
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True),
    required=True,
    help="Path to YAML configuration file",
)
@click.option(
    "--filter",
    type=click.Choice(["container", "toil", "python", "all"]),
    default="all",
    help="Filter apps by type",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be installed without actually installing",
)
@click.option(
    "--continue-on-error",
    is_flag=True,
    help="Continue installing other apps if one fails",
)
@click.option(
    "--verify-after-install",
    "--verify",
    is_flag=True,
    help="Verify each app after installation by running its verify command",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing targets (overrides defaults.force)",
)
@click.option(
    "--verbose/--no-verbose",
    default=True,
    help="Show live output from commands (default: True)",
)
def install(
    config_path,
    filter,
    dry_run,
    continue_on_error,
    verify_after_install,
    force,
    verbose,
):
    """Install apps from YAML configuration file."""
    if isinstance(config_path, bytes):
        config_path = Path(config_path.decode("utf-8"))
    else:
        config_path = Path(config_path)
    click.secho(f"Loading configuration from {config_path}...", fg="yellow")
    cfg = config.load_config(config_path)

    defaults = cfg.get("defaults", {})
    apps = config.get_apps_by_type(cfg, filter if filter != "all" else None)

    click.secho(f"Found {len(apps)} apps to install", fg="cyan")

    def _get_app_name(app):
        """Get display name for an app."""
        return app.get("name") or app.get("target") or app.get("pypi_name", "unknown")

    if dry_run:
        click.echo("\n[DRY RUN] Would install the following apps:")
        for i, app in enumerate(apps, 1):
            click.echo(f"  {i}. {_get_app_name(app)} ({app.get('type')})")
        return

    failed = []
    for i, app in enumerate(apps, 1):
        app_name = _get_app_name(app)
        click.secho(f"\n[{i}/{len(apps)}] Installing {app_name}...", fg="yellow")

        try:
            merged = config.merge_defaults(app, defaults)
            # Override force if CLI flag is set
            if force:
                merged["force"] = True
            # Override verify_after_install if CLI flag is set
            if verify_after_install:
                merged["verify_after_install"] = True

            install_app(merged, verbose=verbose)
            click.secho(f"✓ {app_name} installed successfully", fg="cyan")

            # Verify after install if requested
            should_verify = merged.get(
                "verify_after_install", defaults.get("verify_after_install", False)
            )
            if should_verify:
                bindir = Path(merged.get("bindir", defaults.get("bindir")))

                app_type = merged.get("type")
                target = None

                if app_type == "container":
                    # Container executables use the target name
                    target = merged.get("target")
                elif app_type == "toil":
                    # Toil executables are named pypi_name_pypi_version
                    pypi_name = merged.get("pypi_name")
                    pypi_version = merged.get("pypi_version")
                    if pypi_name and pypi_version:
                        target = f"{pypi_name}_{pypi_version}"
                elif app_type == "python":
                    # Python executables use command or pypi_name_pypi_version
                    pypi_name = merged.get("pypi_name")
                    pypi_version = merged.get("pypi_version")
                    command = merged.get("command")
                    if command:
                        target = command
                    elif pypi_name and pypi_version:
                        target = f"{pypi_name}_{pypi_version}"

                if not target:
                    click.secho(
                        f"⚠ Skipping verification for {app_name}: could not determine executable name",
                        fg="yellow",
                    )
                else:
                    executable_path = bindir / target
                    verify_cmd = merged.get("verify", defaults.get("verify", "--version"))
                    click.echo(f"Verifying {app_name} ({executable_path})...")
                    success, output, error = utils.verify_executable(
                        executable_path, verify_cmd
                    )
                    if success:
                        if output:
                            click.secho(
                                f"✓ Verification passed: {output[:100]}", fg="cyan"
                            )
                        else:
                            click.secho("✓ Verification passed", fg="cyan")
                    else:
                        click.secho(
                            f"✗ Verification failed: {error or 'Unknown error'}",
                            fg="red",
                        )
                        if not continue_on_error:
                            raise click.ClickException(
                                f"Verification failed for {app_name}"
                            )
        except Exception as e:  # pylint: disable=broad-except
            click.secho(f"✗ Failed to install {app_name}: {e}", fg="red")
            if not continue_on_error:
                raise
            failed.append((app_name, str(e)))

    if failed:
        click.echo(f"\n{len(failed)} apps failed to install:")
        for name, error in failed:
            click.echo(f"  - {name}: {error}")
        sys.exit(1)


@click.command()
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True),
    required=True,
    help="Path to YAML configuration file",
)
@click.option(
    "--bindir",
    type=click.Path(exists=True, dir_okay=True),
    help="Override bindir from config (optional)",
)
@click.option(
    "--filter",
    type=click.Choice(["container", "toil", "python", "all"]),
    default="all",
    help="Filter apps by type",
)
@click.option(
    "--timeout",
    type=int,
    default=60,
    help="Timeout per tool in seconds",
)
@click.option(
    "--continue-on-error",
    is_flag=True,
    help="Continue verifying other apps if one fails",
)
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
def verify(
    config_path,
    bindir,
    filter,
    timeout,
    continue_on_error,
    format,
):
    """Verify installed apps by running their verify commands."""
    if isinstance(config_path, bytes):
        config_path = Path(config_path.decode("utf-8"))
    else:
        config_path = Path(config_path)

    click.secho(f"Loading configuration from {config_path}...", fg="yellow")
    cfg = config.load_config(config_path)

    defaults = cfg.get("defaults", {})
    apps = config.get_apps_by_type(cfg, filter if filter != "all" else None)

    # Use provided bindir or get from defaults
    bindir_path = Path(bindir) if bindir else Path(defaults.get("bindir"))
    if not bindir_path.exists():
        raise click.ClickException(f"Bindir does not exist: {bindir_path}")

    click.echo(f"Verifying {len(apps)} apps from {bindir_path}...")

    def _get_app_name(app):
        """Get display name for an app."""
        return app.get("name") or app.get("target") or app.get("pypi_name", "unknown")

    results = []
    for app in apps:
        app_name = _get_app_name(app)
        merged = config.merge_defaults(app, defaults)

        app_type = merged.get("type")
        target = None

        if app_type == "container":
            target = merged.get("target")
        elif app_type == "toil":
            pypi_name = merged.get("pypi_name")
            pypi_version = merged.get("pypi_version")
            if pypi_name and pypi_version:
                target = f"{pypi_name}_{pypi_version}"
        elif app_type == "python":
            pypi_name = merged.get("pypi_name")
            pypi_version = merged.get("pypi_version")
            command = merged.get("command")
            if command:
                target = command
            elif pypi_name and pypi_version:
                target = f"{pypi_name}_{pypi_version}"

        if not target:
            click.secho(
                f"  ⚠ Skipping {app_name}: could not determine executable name",
                fg="yellow",
            )
            continue

        executable_path = bindir_path / target
        verify_cmd = merged.get("verify", defaults.get("verify", "--version"))

        success, output, error = utils.verify_executable(
            executable_path, verify_cmd, timeout
        )
        results.append({
            "name": app_name,
            "target": target,
            "type": merged.get("type"),
            "success": success,
            "output": output,
            "error": error,
        })

        if success:
            if output:
                click.secho(f"  ✓ {app_name} ({verify_cmd}): {output[:80]}", fg="green")
            else:
                click.secho(f"  ✓ {app_name} ({verify_cmd}): passed", fg="green")
        else:
            click.secho(f"  ✗ {app_name} ({verify_cmd}): {error or 'Unknown error'}", fg="red")
            if not continue_on_error:
                raise click.ClickException(f"Verification failed for {app_name}")

    # Summary
    passed = sum(1 for r in results if r["success"])
    failed = len(results) - passed

    if format == "json":
        import json
        click.echo(json.dumps(results, indent=2))
    else:
        click.echo(f"\nSummary: {passed} passed, {failed} failed out of {len(results)} apps")

    if failed > 0:
        sys.exit(1)


@click.command()
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True),
    required=True,
    help="Path to YAML configuration file",
)
@click.option(
    "--filter",
    type=click.Choice(["container", "toil", "all"]),
    default="container",
    help="Filter apps by type (default: container)",
)
@click.option(
    "--format",
    type=click.Choice(["table", "json", "yaml", "pull-commands", "migration"]),
    default="table",
    help="Output format",
)
@click.option(
    "--output",
    type=click.Path(),
    help="Write output to file (optional)",
)
def list_containers(
    config_path,
    filter,
    format,
    output,
):
    """List all container images from YAML configuration."""
    if isinstance(config_path, bytes):
        config_path = Path(config_path.decode("utf-8"))
    else:
        config_path = Path(config_path)

    click.secho(f"Loading configuration from {config_path}...", fg="yellow", err=True)
    cfg = config.load_config(config_path)

    # Extract container images
    filter_type = filter if filter != "all" else None
    containers = utils.extract_container_images(cfg, filter_type)

    if not containers:
        click.echo("No containers found.")
        return

    # Format output
    output_text = utils.format_container_list(containers, format)

    # Write to file or stdout
    if output:
        output_path = Path(output)
        output_path.write_text(output_text)
        click.echo(f"Output written to {output_path}")
    else:
        click.echo(output_text)


def install_app(app_config: Dict[str, Any], verbose: bool = True) -> None:  # type: ignore
    """
    Install a single app based on configuration.

    Args:
        app_config: App configuration dictionary with defaults merged.
        verbose: If True, show live output (default: True).

    Raises:
        ValueError: If app type is unknown.
    """
    app_type = app_config["type"]

    if app_type == "container":
        install_container_app(app_config, verbose=verbose)
    elif app_type == "toil":
        install_toil_app(app_config, verbose=verbose)
    elif app_type == "python":
        install_python_app(app_config, verbose=verbose)
    else:
        raise ValueError(f"Unknown app type: {app_type}")


def install_container_app(app_config: Dict[str, Any], verbose: bool = False) -> None:  # type: ignore
    """Install a container app."""
    runtime_type = app_config.get("container_runtime", "singularity")
    runtime_path = app_config.get(f"{runtime_type}_path", runtime_type)

    _register_image(
        bindir=app_config["bindir"],
        optdir=app_config["optdir"],
        target=app_config.get("target"),
        command=app_config.get("command", ""),
        image_repository=app_config.get("image_repository"),
        image_version=app_config.get("image_version"),
        image_url=app_config.get("image_url"),
        image_user=app_config.get("image_user"),
        force=app_config.get("force", False),
        tmpvar=app_config.get("tmpvar", "$TMP_DIR"),
        volumes=app_config.get("volumes", []),
        runtime=runtime_path,
        image_type=runtime_type,
        no_home=app_config.get("no_home", False),
        image_registry=app_config.get("image_registry"),
    )


def install_toil_app(app_config: Dict[str, Any], verbose: bool = True) -> None:  # type: ignore
    """Install a toil app."""
    _register_toil(
        bindir=app_config["bindir"],
        optdir=app_config["optdir"],
        pypi_name=app_config["pypi_name"],
        pypi_version=app_config["pypi_version"],
        python=app_config.get("python", "python3"),
        volumes=app_config.get("volumes", []),
        tmpvar=app_config.get("tmpvar", "$TMP_DIR"),
        image_url=app_config.get("image_url"),
        image_user=app_config.get("image_user"),
        singularity=app_config.get("singularity_path", "singularity"),
        container=app_config.get("container", "singularity"),
        environment=app_config.get("environment", "development"),
        pre_install=app_config.get("pre_install"),
        image_registry=app_config.get("image_registry"),
        verbose=verbose,
    )


def install_python_app(app_config: Dict[str, Any], verbose: bool = True) -> None:  # type: ignore
    """Install a python app."""
    _register_python(
        pypi_name=app_config["pypi_name"],
        pypi_version=app_config["pypi_version"],
        github_user=app_config.get("github_user"),
        command=app_config.get("command"),
        bindir=app_config["bindir"],
        optdir=app_config["optdir"],
        python=app_config.get("python", "python3"),
        environment=app_config.get("environment", "development"),
        pre_install=app_config.get("pre_install"),
        verbose=verbose,
    )


# Register commands to the CLI group (must be after function definitions)
cli.add_command(install, name="install")
cli.add_command(verify, name="verify")
cli.add_command(list_containers, name="list-containers")
