"""register_apps cli options."""
import os
import click
from register_apps import __version__


_DEFAULT_OPTDIR = "/work/isabl/local"
_DEFAULT_BINDIR = "/work/isabl/bin"

def get_default_volumes():
    volumes = []
    for vol in os.getenv("REGISTER_APPS_VOLUMES", "").split(","):
        if ":" in vol:
            volumes.append(vol.split(":"))
        else:
            volumes.append((vol, vol))
    return volumes or [("/data1", "/data1")]

VERSION = click.version_option(version=__version__)

PYPI_NAME = click.option(
    "--pypi_name", show_default=True, required=True, help="package name in PyPi"
)
PYPI_VERSION = click.option(
    "--pypi_version", show_default=True, required=True, help="package version in PyPi"
)
IMAGE_REPOSITORY = click.option(
    "--image_repository", required=True, help="docker hub repository name"
)
IMAGE_VERSION = click.option(
    "--image_version", required=True, help="docker hub image version"
)
IMAGE_USER = click.option(
    "--image_user",
    default="papaemmelab",
    help="docker hub {user}/{organization} name",
    show_default=True,
)
IMAGE_URL = click.option(
    "--image_url",
    default=None,
    help="image URL [default=docker://{image_user}/{image_repository}:{image_version}]",
)
GITHUB_USER = click.option(
    "--github_user", default=None, help="(optional) github user of package"
)
VOLUMES = click.option(
    "--volumes",
    type=click.Tuple([click.Path(exists=True, resolve_path=True, dir_okay=True), str]),
    multiple=True,
    default=get_default_volumes(),
    show_default=False,
    help=f"volumes tuples to be passed to the container command. Use $REGISTER_APPS_VOLUMES. [default={get_default_volumes()}]",
)
TMPVAR = click.option(
    "--tmpvar",
    show_default=True,
    help="environment variable used for workdir: --workDir ${tmpvar}",
    default="${TMP_DIR}",
)
BINDIR = click.option(
    "--bindir",
    show_default=True,
    type=click.Path(resolve_path=True, dir_okay=True),
    help="path were executables will be linked to. Use $REGISTER_APPS_BIN",
    default=os.getenv("REGISTER_APPS_BIN", _DEFAULT_BINDIR),
)
OPTDIR = click.option(
    "--optdir",
    show_default=True,
    type=click.Path(resolve_path=True, dir_okay=True),
    help="path were images will be versioned and cached. Use $REGISTER_APPS_OPT",
    default=os.getenv("REGISTER_APPS_OPT", _DEFAULT_OPTDIR),
)
PYTHON2 = click.option(
    "--python",
    show_default=True,
    help="which python to be used for the virtual environment",
    default="python2",
)
PYTHON3 = click.option(
    "--python",
    show_default=True,
    help="which python to be used for the virtual environment",
    default="python3",
)
VIRTUALENVWRAPPER = click.option(
    "--virtualenvwrapper",
    show_default=True,
    help="path to virtualenvwrapper.sh",
    default="virtualenvwrapper.sh",
)
DOCKER = click.option(
    "--docker",
    show_default=True,
    help="path to docker runtime",
    default="docker",
)
SINGULARITY = click.option(
    "--singularity",
    show_default=True,
    help="path to singularity runtime",
    default="singularity",
)
TARGET = click.option(
    "--target",
    show_default=True,
    required=True,
    help="name of the target script that will be created",
)
COMMAND = click.option(
    "--command",
    show_default=True,
    required=True,
    help="command that will be added at the end of the singularity exec instruction "
    "(e.g. bwa_mem.pl)",
)
FORCE = click.option(
    "--force",
    is_flag=True,
    required=False,
    help="Overwrite target executable and scripts (and images) if they already exist",
)
CONTAINER = click.option(
    "--container",
    show_default=True,
    default="singularity",
    type=click.Choice(["docker", "singularity"]),
    help="container runtime to be used (docker or singularity)",
)