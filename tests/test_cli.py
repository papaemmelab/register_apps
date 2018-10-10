"""register_toil cli tests."""

# pylint: disable=E1135

import subprocess

from click.testing import CliRunner

from register_toil import cli


def test_main(tmpdir):
    """Sample test for main command."""
    runner = CliRunner()
    optdir = tmpdir.mkdir("opt")
    bindir = tmpdir.mkdir("bin")
    optexe = optdir.join("toil_disambiguate", "v0.1.2", "toil_disambiguate")
    binexe = bindir.join("toil_disambiguate")
    binexe_versioned = bindir.join("toil_disambiguate_v0.1.2")

    params = [
        "--pypi_name",
        "toil_disambiguate",
        "--pypi_version",
        "v0.1.2",
        "--volumes",
        "/tmp",
        "/carlos",
        "--optdir",
        optdir.strpath,
        "--bindir",
        bindir.strpath,
        "--tmpvar",
        "$TMP",
    ]

    result = runner.invoke(cli.main, params)

    if result.exit_code:
        print(vars(result))

    for i in optexe.strpath, binexe.strpath, binexe_versioned.strpath:
        assert b"0.1.2" in subprocess.check_output(
            args=[i, "--version"], env={"TMP": "/tmp"}, stderr=subprocess.STDOUT
        )

    assert "--volumes /tmp /carlos" in optexe.read()
    assert "--workDir $TMP" in optexe.read()
