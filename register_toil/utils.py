"""register_toil utils."""

import os
import tarfile


from register_toil import exceptions


def force_link(src, dst):
    """Force a link between src and dst."""
    try:
        os.unlink(dst)
        os.link(src, dst)
    except OSError:
        os.link(src, dst)


def force_symlink(src, dst):
    """Force a symlink between src and dst."""
    try:
        os.unlink(dst)
        os.symlink(src, dst)
    except OSError:
        os.symlink(src, dst)


def tar_dir(output_path, source_dir):
    """Compress a `source_dir` in `output_path`."""
    with tarfile.open(output_path, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))


def which(program, raise_error=True):
    """
    Locate a program file in the user's path.

    Python implementation to mimic the behavior of the UNIX 'which' command
    And shutil.which() is not supported in python 2.x.
    See: https://stackoverflow.com/questions/377017

    Arguments:
        program (str): command to be tested. Can be relative or absolute path.
        raise_error(bool): raise error if program not available in PATH.

    Raises:
        exceptions.MissingRequirementError: if `raise_error` and `program`
            not found.

    Return:
        str: program file in the user's path.
    """
    fpath, _ = os.path.split(program)
    if fpath:
        if _is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if _is_exe(exe_file):
                return exe_file

    if raise_error:
        raise exceptions.MissingRequirementError(
            f"{program} is required and not available in path."
        )

    return None


def _is_exe(fpath):
    """
    Check if fpath is executable for the current user.

    Arguments:
        fpath (str): relative or absolute path.

    Return:
        bool: True if execution is granted, else False.
    """
    return os.path.isfile(fpath) and os.access(fpath, os.X_OK)
