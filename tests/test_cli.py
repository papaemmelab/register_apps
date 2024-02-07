"""register_apps cli tests."""
# pylint: disable=E1135
import subprocess

from click.testing import CliRunner
import pytest

from register_apps import cli
from tests import utils


SKIP_SINGULARITY = pytest.mark.skipif(
    not utils.is_executable_available("singularity"), reason="singularity is not available."
)

SKIP_DOCKER = pytest.mark.skipif(
    not utils.is_executable_available("docker"), reason="docker is not available."
)

def test_register_container(tmpdir, container_runtime):
    runner = CliRunner()
    optdir = tmpdir.mkdir("opt")
    bindir = tmpdir.mkdir("bin")
    optexe = optdir.join("docker-pcapcore", "v0.1.1", "bwa_mem.pl")
    binexe = bindir.join("bwa_mem.pl")
    container_cli = cli.register_docker if container_runtime == "docker" else cli.register_singularity 

    result = runner.invoke(
        container_cli,
        [
            "--image_repository",
            "docker-pcapcore",
            "--image_version",
            "v0.1.1",
            "--image_user",
            "leukgen",
            "--volumes",
            "/tmp",
            "/carlos",
            "--optdir",
            optdir.strpath,
            "--bindir",
            bindir.strpath,
            "--tmpvar",
            "$TMP",
            "--command",
            "bwa_mem.pl",
            "--target",
            "bwa_mem.pl",
        ],
    )

    if result.exit_code:
        print(vars(result))

    for i in optexe.strpath, binexe.strpath:
        assert b"4.2.1" in subprocess.check_output(
            args=[i, "--version"],
            env={"TMP": "/tmp", "USER": "root"},
            stderr=subprocess.STDOUT,
        )

    assert "--volume /tmp:/carlos" if container_runtime == "docker" else "--bind /tmp:/carlos" in optexe.read()
    assert "--workdir $TMP" in optexe.read()
    assert not runner.invoke(container_cli, ["--help"]).exit_code


@SKIP_DOCKER
def test_register_docker(tmpdir):
    """Sample test for register_docker command."""
    test_register_container(tmpdir, container_runtime="docker")


@SKIP_SINGULARITY
def test_register_singularity(tmpdir):
    """Sample test for register_singularity command."""
    test_register_container(tmpdir, container_runtime="singularity")


@SKIP_SINGULARITY
def test_register_toil(tmpdir):
    """Sample test for register_toil command."""
    runner = CliRunner()
    optdir = tmpdir.mkdir("opt")
    bindir = tmpdir.mkdir("bin")
    optexe = optdir.join("toil_disambiguate", "v0.1.2", "toil_disambiguate")
    binexe = bindir.join("toil_disambiguate_v0.1.2")
    result = runner.invoke(
        cli.register_toil,
        [
            "--pypi_name",
            "toil_disambiguate",
            "--pypi_version",
            "v0.1.2",
            "--image_user",
            "leukgen",
            "--volumes",
            "/tmp",
            "/carlos",
            "--optdir",
            optdir.strpath,
            "--bindir",
            bindir.strpath,
            "--tmpvar",
            "$TMP",
        ],
    )

    if result.exit_code:
        print(vars(result))

    for i in optexe.strpath, binexe.strpath:
        assert b"0.1.2" in subprocess.check_output(
            args=[i, "--version"], env={"TMP": "/tmp"}, stderr=subprocess.STDOUT
        )

    assert "--volumes /tmp /carlos" in optexe.read()
    assert "--workDir $TMP" in optexe.read()
    assert not runner.invoke(cli.register_toil, ["--help"]).exit_code


def test_register_python(tmpdir):
    """Sample test for register_python command."""
    runner = CliRunner()
    optdir = tmpdir.mkdir("opt")
    bindir = tmpdir.mkdir("bin")
    optexe = optdir.join("toil_snapigv", "v0.1.1", "toil_snapigv")
    binexe = bindir.join("toil_snapigv_v0.1.1")
    result = runner.invoke(
        cli.register_python,
        [
            "--pypi_name",
            "toil_snapigv",
            "--pypi_version",
            "v0.1.1",
            "--optdir",
            optdir.strpath,
            "--bindir",
            bindir.strpath,
            "--python",
            "python2",
        ],
    )

    if result.exit_code:
        print(vars(result))

    for i in optexe.strpath, binexe.strpath:
        assert b"0.1.1" in subprocess.check_output(
            args=[i, "--version"], stderr=subprocess.STDOUT
        )
    assert not runner.invoke(cli.register_python, ["--help"]).exit_code


def test_register_python_github(tmpdir):
    """Sample test for register_python command."""
    runner = CliRunner()
    optdir = tmpdir.mkdir("opt")
    bindir = tmpdir.mkdir("bin")
    optexe = optdir.join("toil_snapigv", "v0.1.1", "toil_snapigv")
    binexe = bindir.join("toil_snapigv_v0.1.1")
    result = runner.invoke(
        cli.register_python,
        [
            "--pypi_name",
            "toil_snapigv",
            "--pypi_version",
            "v0.1.1",
            "--optdir",
            optdir.strpath,
            "--bindir",
            bindir.strpath,
            "--github_user",
            "papaemmelab",
            "--python",
            "python2",
        ],
    )

    if result.exit_code:
        print(vars(result))

    for i in optexe.strpath, binexe.strpath:
        assert b"0.1.1" in subprocess.check_output(
            args=[i, "--version"], stderr=subprocess.STDOUT
        )
    assert not runner.invoke(cli.register_python, ["--help"]).exit_code

