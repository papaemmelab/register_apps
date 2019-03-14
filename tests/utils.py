
"""Utils for tests."""
import subprocess


def is_singularity_available():
    """
    Check if singularity is available to run in the current environment.

    Returns:
        bool: True if singularity is available.
    """
    try:
        subprocess.check_output(["singularity", "--version"])
        return True
    except (subprocess.CalledProcessError, OSError):
        return False
