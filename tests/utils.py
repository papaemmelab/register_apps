
"""Utils for tests."""
import subprocess


def is_executable_available(executable):
    """
    Check if an executable is available to run in the current environment.

    Args:
        executable (str): name of the executable to check.

    Returns:
        bool: True if the executable is available.
    """
    try:
        subprocess.check_output([executable, "--version"])
        return True
    except (subprocess.CalledProcessError, OSError):
        return False