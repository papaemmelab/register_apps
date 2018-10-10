# register_toil

[![pypi badge][pypi_badge]][pypi_base]
[![travis badge][travis_badge]][travis_base]
[![codecov badge][codecov_badge]][codecov_base]
[![docker badge][docker_badge]][docker_base]
[![docker badge][automated_badge]][docker_base]
[![code formatting][black_badge]][black_base]

👾 Simple utility to register versioned [toil container] pipelines in a `bin` directory.

## Installation

This package is available at [PyPi][pypi_base]:

    pip install register_toil

⚠️ **WARNING:** This package only works with singularity 2.4+

## Usage

`register_toil` will install [toil container] pipelines in separate [virtual environments], pull a singularity image from the dockerhub and create executables that call the pipeline with the right parameters:

    register_toil \
        --bindir /example/bin \
        --optdir /example/opt \
        --tmpvar $TMP \
        --pypi_name toil_disambiguate \
        --pypi_version v0.1.2 \
        --volumes /ifs /ifs

Given this call, the following directory structure is created:

    /example/
    ├── bin
    │   ├── toil_disambiguate -> /example/opt/toil_disambiguate/v0.1.2/toil_disambiguate
    │   └── toil_disambiguate_v0.1.2 -> /example/opt/toil_disambiguate/v0.1.2/toil_disambiguate
    └── opt
        └── toil_disambiguate
            └── v0.1.2
                ├── toil_disambiguate
                └── toil_disambiguate-v0.1.2.simg

And the executables look like this:

    cat /example/bin/toil_disambiguate
    #!/bin/bash
    /path/to/.virtualenvs/production__toil_disambiguate__v0.1.2/bin/toil_disambiguate \
        --singularity /example/opt/toil_disambiguate/v0.1.2/toil_disambiguate-v0.1.2.simg \
        --volumes /ifs /ifs \
        --workDir $TMP_DIR $@

## Contributing

Contributions are welcome, and they are greatly appreciated, check our [contributing guidelines](.github/CONTRIBUTING.md)!

## Credits

This package was created using [Cookiecutter] and the
[leukgen/cookiecutter-toil] project template.

[virtual environments]: http://virtualenvwrapper.readthedocs.io/en/latest/
[toil container]: https://github.com/leukgen/toil_container
[singularity]: http://singularity.lbl.gov/
[docker2singularity]: https://github.com/singularityware/docker2singularity
[cookiecutter]: https://github.com/audreyr/cookiecutter
[leukgen/cookiecutter-toil]: https://github.com/leukgen/cookiecutter-toil
[`--batchSystem`]: http://toil.readthedocs.io/en/latest/developingWorkflows/batchSystem.html?highlight=BatchSystem
[docker_base]: https://hub.docker.com/r/leukgen/register_toil
[docker_badge]: https://img.shields.io/docker/build/leukgen/register_toil.svg
[automated_badge]: https://img.shields.io/docker/automated/leukgen/register_toil.svg
[codecov_badge]: https://codecov.io/gh/leukgen/register_toil/branch/master/graph/badge.svg
[codecov_base]: https://codecov.io/gh/leukgen/register_toil
[pypi_badge]: https://img.shields.io/pypi/v/register_toil.svg
[pypi_base]: https://pypi.org/pypi/register_toil
[travis_badge]: https://img.shields.io/travis/leukgen/register_toil.svg
[travis_base]: https://travis-ci.org/leukgen/register_toil
[black_badge]: https://img.shields.io/badge/code%20style-black-000000.svg
[black_base]: https://github.com/ambv/black
