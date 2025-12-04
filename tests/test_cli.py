"""register_apps cli tests."""

import os

from click.testing import CliRunner
import pytest

from register_apps import cli
from register_apps import utils as register_utils
from tests import utils


SKIP_SINGULARITY = pytest.mark.skipif(
    not utils.is_executable_available("singularity"),
    reason="singularity is not available.",
)


SKIP_DOCKER = pytest.mark.skipif(
    not utils.is_executable_available("docker"), reason="docker is not installed."
)


def _require_virtualenvwrapper():
    """Require virtualenvwrapper to be available, fail if not."""
    if not register_utils.is_virtualenvwrapper_configured():
        pytest.fail(
            "virtualenvwrapper is not available. "
            "Please install virtualenvwrapper and ensure it's configured."
        )


def _test_register_container(tmpdir, container_cli):
    """Helper function to test container registration."""
    runner = CliRunner()
    optdir = tmpdir.mkdir("opt")
    bindir = tmpdir.mkdir("bin")
    optexe = optdir.join("alpine", "latest", "test_cmd")
    binexe = bindir.join("test_cmd")

    result = runner.invoke(
        container_cli,
        [
            "--image_url",
            "alpine:latest",
            "--image_repository",
            "alpine",
            "--image_version",
            "latest",
            "--volumes",
            "/tmp",
            "/tmp",
            "--optdir",
            optdir.strpath,
            "--bindir",
            bindir.strpath,
            "--tmpvar",
            "$TMPDIR",
            "--command",
            "echo",
            "--target",
            "test_cmd",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, f"Failed: {result.output}"
    assert os.path.exists(optexe.strpath)
    assert os.path.exists(binexe.strpath)


@SKIP_DOCKER
def test_register_docker(tmpdir):
    """Test register_docker command."""
    _test_register_container(tmpdir, cli.register_docker)


@SKIP_SINGULARITY
def test_register_singularity(tmpdir):
    """Test register_singularity command."""
    _test_register_container(tmpdir, cli.register_singularity)


@SKIP_SINGULARITY
def test_register_toil(tmpdir):
    """Test register_toil command."""
    _require_virtualenvwrapper()
    runner = CliRunner()
    optdir = tmpdir.mkdir("opt")
    bindir = tmpdir.mkdir("bin")

    result = runner.invoke(
        cli.register_toil,
        [
            "--pypi_name",
            "toil_container",
            "--pypi_version",
            "v2.0.3",
            "--image_user",
            "leukgen",
            "--volumes",
            "/tmp",
            "/tmp",
            "--optdir",
            optdir.strpath,
            "--bindir",
            bindir.strpath,
            "--tmpvar",
            "$TMP",
            "--python",
            "python3",
        ],
    )

    assert result.exit_code == 0, f"Failed: {result.output}"
    workon_home = os.getenv("WORKON_HOME", os.path.expanduser("~/.virtualenvs"))
    venv_path = os.path.join(workon_home, "production__toil_container__v2.0.3")
    assert os.path.exists(venv_path)


def test_register_python(tmpdir):
    """Test register_python command."""
    _require_virtualenvwrapper()
    runner = CliRunner()
    optdir = tmpdir.mkdir("opt")
    bindir = tmpdir.mkdir("bin")
    optexe = optdir.join("flake8", "4.0.1", "flake8")
    binexe = bindir.join("flake8")

    result = runner.invoke(
        cli.register_python,
        [
            "--pypi_name",
            "flake8",
            "--pypi_version",
            "4.0.1",
            "--optdir",
            optdir.strpath,
            "--bindir",
            bindir.strpath,
            "--python",
            "python3",
            "--command",
            "flake8",
        ],
    )

    assert result.exit_code == 0, f"Failed: {result.output}"
    workon_home = os.getenv("WORKON_HOME", os.path.expanduser("~/.virtualenvs"))
    venv_path = os.path.join(workon_home, "production__flake8__4.0.1")
    assert os.path.exists(venv_path)
    assert os.path.exists(optexe.strpath)
    assert os.path.exists(binexe.strpath)


def test_register_python_github(tmpdir):
    """Test register_python command with GitHub source."""
    _require_virtualenvwrapper()
    runner = CliRunner()
    optdir = tmpdir.mkdir("opt")
    bindir = tmpdir.mkdir("bin")
    optexe = optdir.join("flake8", "4.0.1", "flake8")
    binexe = bindir.join("flake8")

    result = runner.invoke(
        cli.register_python,
        [
            "--pypi_name",
            "flake8",
            "--pypi_version",
            "4.0.1",
            "--optdir",
            optdir.strpath,
            "--bindir",
            bindir.strpath,
            "--github_user",
            "PyCQA",
            "--python",
            "python3",
            "--command",
            "flake8",
        ],
    )

    assert result.exit_code == 0, f"Failed: {result.output}"
    workon_home = os.getenv("WORKON_HOME", os.path.expanduser("~/.virtualenvs"))
    venv_path = os.path.join(workon_home, "production__flake8__4.0.1")
    assert os.path.exists(venv_path)
    assert os.path.exists(optexe.strpath)
    assert os.path.exists(binexe.strpath)
