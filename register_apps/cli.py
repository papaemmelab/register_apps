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
import os
import shutil
import subprocess

import click

from register_apps import options
from register_apps import utils


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
@options.VERSION
def register_toil(
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
):
    """Register versioned toil container pipelines in a bin directory."""
    virtualenvwrapper = shutil.which("virtualenvwrapper.sh")
    python = shutil.which(python)
    optdir = Path(optdir) / pypi_name / pypi_version
    bindir = Path(bindir)
    optexe = optdir / pypi_name
    binexe = bindir / f"{pypi_name}_{pypi_version}"
    image_url = image_url or f"docker://{image_user}/{pypi_name}:{pypi_version}"

    # check paths
    assert python, "Could not determine the python path."
    assert virtualenvwrapper, "Could not determine the virtualenvwrapper.sh path."

    # make sure dirs exist
    optdir.mkdir(exist_ok=True, parents=True)
    bindir.mkdir(exist_ok=True, parents=True)

    # create virtual environment and install package
    env = f"production__{pypi_name}__{pypi_version}"
    click.echo(f"Creating virtual environment '{env}'...")
    subprocess.check_output(
        [
            "/bin/bash",
            "-c",
            f"source {virtualenvwrapper} && mkvirtualenv -p {python} {env}",
        ]
    )

    if github_user:
        install_cmd = (
            f"source {virtualenvwrapper} && workon {env} && "
            f"pip install git+https://github.com/{github_user}/"
            f"{pypi_name}@{pypi_version}#egg={pypi_name} && which {pypi_name}"
        )
    else:
        install_cmd = (
            f"source {virtualenvwrapper} && workon {env} && "
            f"pip install {pypi_name}=={pypi_version} && which {pypi_name}"
        )

    click.echo(f"Installing package with '{install_cmd}'...")
    toolpath = subprocess.check_output(["/bin/bash", "-c", install_cmd])
    toolpath = toolpath.decode("utf-8").strip().split("\n")[-1]

    # build command
    command = [
        toolpath,
        '"$@"',
        "--singularity",
        _get_or_create_image(optdir, singularity, image_url),
        " ".join(f"--volumes {i} {j}" for i, j in volumes),
        "--workDir",
        tmpvar,
        "\n",
    ]

    # link executables
    click.echo("Creating and linking executable...")
    optexe.write_text(f"#!/bin/bash\n{' '.join(command)}")
    optexe.chmod(mode=0o755)
    utils.force_symlink(optexe, binexe)
    click.secho(
        f"\nExecutables available at:\n" f"\n\t{str(optexe)}" f"\n\t{str(binexe)}\n",
        fg="green",
    )


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
@options.VERSION
def register_singularity(  # pylint: disable=R0913
    bindir,
    command,
    image_repository,
    image_url,
    image_user,
    image_version,
    optdir,
    singularity,
    target,
    tmpvar,
    volumes,
):
    """Register versioned singularity command in a bin directory."""
    optdir = Path(optdir) / image_repository / image_version
    bindir = Path(bindir)
    optexe = optdir / target
    binexe = bindir / target
    image_url = image_url or f"docker://{image_user}/{image_repository}:{image_version}"

    # do not overwrite targets
    if os.path.isfile(optexe) or os.path.isfile(binexe):  # pragma: no cover
        raise click.UsageError(f"Targets exist, exiting...\n\t{optexe}\n\t{binexe}")

    # make sure dirs exist
    optdir.mkdir(exist_ok=True, parents=True)
    bindir.mkdir(exist_ok=True, parents=True)

    # build command
    command = [
        singularity,
        "exec",
        "--workdir",
        f"{tmpvar}/${{USER}}_{image_repository}_{image_version}_`uuidgen`",
        " ".join(f"--bind {i}:{j}" for i, j in volumes),
        _get_or_create_image(optdir, singularity, image_url),
        command,
        '"$@"\n',
    ]

    # link executables
    click.echo("Creating and linking executable...")
    optexe.write_text(f"#!/bin/bash\n{' '.join(command)}")
    optexe.chmod(mode=0o755)
    utils.force_symlink(optexe, binexe)
    click.secho(
        f"\nExecutables available at:\n" f"\n\t{str(optexe)}" f"\n\t{str(binexe)}\n",
        fg="green",
    )


@click.command()
@options.PYPI_NAME
@options.PYPI_VERSION
@options.GITHUB_USER
@options.BINDIR
@options.OPTDIR
@options.PYTHON3
@options.VERSION
def register_python(pypi_name, pypi_version, github_user, bindir, optdir, python):
    """Register versioned python pipelines in a bin directory."""
    virtualenvwrapper = shutil.which("virtualenvwrapper.sh")
    python = shutil.which(python)
    optdir = Path(optdir) / pypi_name / pypi_version
    bindir = Path(bindir)
    optexe = optdir / pypi_name
    binexe = bindir / f"{pypi_name}_{pypi_version}"

    # check paths
    assert python, "Could not determine the python path."
    assert virtualenvwrapper, "Could not determine the virtualenvwrapper.sh path."

    # make sure dirs exist
    optdir.mkdir(exist_ok=True, parents=True)
    bindir.mkdir(exist_ok=True, parents=True)

    # create virtual environment and install package
    env = f"production__{pypi_name}__{pypi_version}"
    click.echo(f"Creating virtual environment '{env}'...")
    subprocess.check_output(
        [
            "/bin/bash",
            "-c",
            f"source {virtualenvwrapper} && mkvirtualenv -p {python} {env}",
        ]
    )

    if github_user:
        install_cmd = (
            f"source {virtualenvwrapper} && workon {env} && "
            f"pip install git+https://github.com/{github_user}/"
            f"{pypi_name}@{pypi_version}#egg={pypi_name} && which {pypi_name}"
        )
    else:
        install_cmd = (
            f"source {virtualenvwrapper} && workon {env} && "
            f"pip install {pypi_name}=={pypi_version} && which {pypi_name}"
        )

    click.echo(f"Installing package with '{install_cmd}'...")
    toolpath = subprocess.check_output(["/bin/bash", "-c", install_cmd])
    toolpath = toolpath.decode("utf-8").strip().split("\n")[-1]

    # build command
    command = [toolpath, '"$@"', "\n"]

    # link executables
    click.echo("Creating and linking executable...")
    optexe.write_text(f"#!/bin/bash\n{' '.join(command)}")
    optexe.chmod(mode=0o755)
    utils.force_symlink(optexe, binexe)
    click.secho(
        f"\nExecutables available at:\n" f"\n\t{str(optexe)}" f"\n\t{str(binexe)}\n",
        fg="green",
    )


def _get_or_create_image(optdir, singularity, image_url):
    # pull image
    singularity_images = list(optdir.glob("*.simg"))

    assert (
        not singularity_images or len(singularity_images) == 1
    ), f"Found multiple images at {optdir}"

    if singularity_images:
        click.echo(f"Image exists at: {singularity_images[0]}")
    else:
        subprocess.check_call(
            ["/bin/bash", "-c", f"umask 22 && {singularity} pull {image_url}"],
            cwd=optdir,
        )

    # fix singularity permissions
    singularity_image = next(optdir.glob("*.simg"))
    singularity_image.chmod(mode=0o755)
    return str(singularity_image)
