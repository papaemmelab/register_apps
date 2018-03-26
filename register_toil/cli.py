"""
Module that contains the command line app.

Why does this file exist, and why not put this in __main__?
You might be tempted to import things from __main__ later, but that will
cause problems, the code will get executed twice:

    - When you run `python -m register_toil` python will execute
      `__main__.py` as a script. That means there won't be any
      `register_toil.__main__` in `sys.modules`.

    - When you import __main__ it will get executed again (as a module) because
      there's no `register_toil.__main__` in `sys.modules`.

Also see (1) from http://click.pocoo.org/5/setuptools/#setuptools-integration
"""

from pathlib import Path
import subprocess
import os

import click

from register_toil import __version__
from register_toil import utils


BIN = os.getenv("TOIL_REGISTER_BIN", "/ifs/work/leukgen/local/bin")
OPT = os.getenv("TOIL_REGISTER_OPT", "/ifs/work/leukgen/local/opt")


@click.command()
@click.option(
    "--pypi_name",
    required=True,
    help="Package name in PyPi.")
@click.option(
    "--pypi_version",
    required=True,
    help="Package version in PyPi.")
@click.option(
    "--image_url",
    default=None,
    help="Docker image URL. default=leukgen/{pypi_name}:{pypi_version}")
@click.option(
    "--bindir",
    type=click.Path(resolve_path=True, dir_okay=True),
    help="Path were executables will be linked to.",
    default=BIN)
@click.option(
    "--optdir",
    type=click.Path(resolve_path=True, dir_okay=True),
    help="Path were images will be versioned and cached.",
    default=OPT)
@click.option(
    "--python",
    help="Which python to be used for the virtual environment.",
    default="python2")
@click.option(
    "--tmpvar",
    help="Environment variable used for workdir: --workDir ${tmpvar}.",
    default="$TMP_DIR")
@click.option(
    "--volumes",
    type=(click.Path(exists=True, resolve_path=True, dir_okay=True), str),
    multiple=True,
    required=True,
    help="List of volumes tuples to be passed to the toil application.")
@click.version_option(version=__version__)
def main(
        pypi_name, pypi_version, bindir, optdir,
        python, volumes, tmpvar, image_url):
    """Echo message and exit."""
    virtualenvwrapper = utils.which("virtualenvwrapper.sh")
    python = utils.which(python)
    optdir = Path(optdir) / pypi_name / pypi_version
    bindir = Path(bindir)
    optexe = optdir / pypi_name
    binexe = bindir / pypi_name
    binexe_versioned = bindir / f"{pypi_name}_{pypi_version}"

    # make sure dirs exist
    optdir.mkdir(exist_ok=True, parents=True)
    bindir.mkdir(exist_ok=True, parents=True)

    # create virtual environment and install package
    env = f"prod__{pypi_name}__{pypi_version}"
    click.echo(f"Creating virtual environment '{env}'...")
    subprocess.check_output([
        "/bin/bash", "-c",
        f"source {virtualenvwrapper} && mkvirtualenv -p {python} {env}"
        ])

    install_cmd = (
        f"source {virtualenvwrapper} && workon {env} && "
        f"pip install {pypi_name}=={pypi_version} && which {pypi_name}"
        )

    click.echo(f"Installing package with '{install_cmd}'...")
    toolpath = subprocess.check_output(["/bin/bash", "-c", install_cmd])
    toolpath = toolpath.decode("utf-8").strip().split("\n")[-1]

    # pull image
    if not image_url:
        image_url = f"docker://leukgen/{pypi_name}:{pypi_version}"

    singularity = utils.which("singularity")
    click.echo("Pulling image...")
    subprocess.check_call([
        "/bin/bash", "-c", f"umask 22 && {singularity} pull {image_url}"
        ], cwd=optdir)

    command = [
        toolpath,
        "--singularity", str(next(optdir.glob("*.simg"))),
        " ".join(f"--volumes {i} {j}" for i, j in volumes),
        "--workDir", tmpvar, "$@\n"
        ]

    # link executables
    click.echo("Creating and linking executable...")
    optexe.write_text(f"#!/bin/bash\n{' '.join(command)}")
    optexe.chmod(mode=0o755)
    utils.force_symlink(optexe, binexe)
    utils.force_symlink(optexe, binexe_versioned)
    click.secho(
        f"\nExecutables available at:\n"
        f"\n\t{str(optexe)}"
        f"\n\t{str(binexe)}"
        f"\n\t{str(binexe_versioned)}\n",
        fg="green")
