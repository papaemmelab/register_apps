# register_apps

[![pypi badge][pypi_badge]][pypi_base]
[![travis badge][travis_badge]][travis_base]
[![codecov badge][codecov_badge]][codecov_base]
[![docker badge][docker_badge]][docker_base]
[![docker badge][automated_badge]][docker_base]
[![code formatting][black_badge]][black_base]

👾 Register versioned [toil container] pipelines, singularity containers, and python packages.

## Installation

This package is available at [PyPi][pypi_base]:

    pip install register_apps

## Usage

This package it's used to register versionized and containerized applications within a production environment. It provides 3 commands:

* 🍡 `register_toil`
* 📦 `register_singularity`
* 🐍 `register_python`

⚠️ **WARNING:** This package only works with singularity 2.4+

### Register a toil containerized application

* 🍡 **`register_toil`** will install [toil container] pipelines in separate [virtual environments], pull a singularity image from the dockerhub and create executables that call the pipeline with the right parameters:

        register_toil \
            --pypi_name toil_disambiguate \
            --pypi_version v0.1.2 \
            --bindir /example/bin \
            --optdir /example/opt \
            --tmpvar $TMP \
            --volumes /ifs /ifs

    Given this call, the following directory structure is created:

        /example/
        ├── bin
        │   └── toil_disambiguate_v0.1.2 -> /example/opt/toil_disambiguate/v0.1.2/toil_disambiguate
        └── opt
            └── toil_disambiguate
                └── v0.1.2
                    ├── toil_disambiguate
                    └── toil_disambiguate-v0.1.2.simg

    And the executables look like this:

        cat /example/bin/toil_disambiguate
        #!/bin/bash
        /path/to/.virtualenvs/production__toil_disambiguate__v0.1.2/bin/toil_disambiguate $@ \
            --singularity /example/opt/toil_disambiguate/v0.1.2/toil_disambiguate-v0.1.2.simg \
            --volumes /ifs /ifs \
            --workDir $TMP_DIR

* 📦 **`register_singularity`** provides a similar usage to register regular commands that will run inside a container, it will create the same directory structure but the executables created will execute commands inside the container:

        register_singularity \
            --target svaba \
            --command svaba \
            --image_url docker://papaemmelab/docker-svaba:v1.0.0 \
            --bindir /example/bin \
            --optdir /example/opt \
            --tmpvar $TMP \
            --volumes /ifs /ifs

    Given this call, the following directory structure is created:

        /example/
        ├── bin
        │   └── svaba -> /example/opt/docker-svaba/v1.0.0/svaba
        └── opt
            └── docker_svaba
                └── v1.0.0
                    ├── svaba
                    └── docker-svaba-v1.0.0

    And the executables look like this:

        cat /example/bin/svaba
        #!/bin/bash
        singularity exec \
            --workdir $TMP_DIR/${USER}_docker-svaba_v1.0.0_`uuidgen` \
            --pwd `pwd` \
            --bind /ifs:/ifs \
            /example/opt/docker-svaba/v1.0.0/docker-svaba-v1.0.0.simg svaba "$@"

* 🐍 **`register_python`** provides a method to register python packages without registering to run inside a container. It will create a similiar versionized directory structure and installing the python package and its dependencies within a virtual environemnt:

        register_python \
            --pypi_name click_annotvcf \
            --pypi_version v1.0.7
            --bindir /example/bin \
            --optdir /example/opt

    Given this call, the following directory structure is created:

        /example/
        ├── bin
        │   └── click_annotvcf_v1.0.7 -> /example/opt/click_annotvcfs/v1.0.7/click_annotvcf
        └── opt
            └── click_annotvcf
                └── v1.0.7
                    └── click_annotvcf

    And the executables look like this:

        cat /example/bin/click_annotvcf_v1.0.7
        #!/bin/bash
        /path/to/.virtualenvs/production__click_annotvcf__v1.0.7/bin/click_annotvcf "$@"


## Contributing

Contributions are welcome, and they are greatly appreciated, check our [contributing guidelines](.github/CONTRIBUTING.md)!

## Credits

This package was created using [Cookiecutter] and the
[papaemmelab/cookiecutter-toil] project template.

[virtual environments]: http://virtualenvwrapper.readthedocs.io/en/latest/
[toil container]: https://github.com/papaemmelab/toil_container
[singularity]: http://singularity.lbl.gov/
[docker2singularity]: https://github.com/singularityware/docker2singularity
[cookiecutter]: https://github.com/audreyr/cookiecutter
[papaemmelab/cookiecutter-toil]: https://github.com/papaemmelab/cookiecutter-toil
[`--batchSystem`]: http://toil.readthedocs.io/en/latest/developingWorkflows/batchSystem.html?highlight=BatchSystem
[docker_base]: https://hub.docker.com/r/papaemmelab/register_apps
[docker_badge]: https://img.shields.io/docker/cloud/build/papaemmelab/register_apps.svg
[automated_badge]: https://img.shields.io/docker/cloud/automated/papaemmelab/register_apps.svg
[codecov_badge]: https://codecov.io/gh/papaemmelab/register_apps/branch/master/graph/badge.svg
[codecov_base]: https://codecov.io/gh/papaemmelab/register_apps
[pypi_badge]: https://img.shields.io/pypi/v/register_apps.svg
[pypi_base]: https://pypi.org/pypi/register_apps
[travis_badge]: https://img.shields.io/travis/papaemmelab/register_apps.svg
[travis_base]: https://travis-ci.org/papaemmelab/register_apps
[black_badge]: https://img.shields.io/badge/code%20style-black-000000.svg
[black_base]: https://github.com/ambv/black
