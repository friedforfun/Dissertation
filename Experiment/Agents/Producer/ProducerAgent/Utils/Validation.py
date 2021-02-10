import errno
import os
import socket
import sys
from .Logging import logger

# Sadly, Python fails to provide the following magic number for us.
ERROR_INVALID_NAME = 123
'''
Windows-specific error code indicating an invalid pathname.
See Also
----------
https://docs.microsoft.com/en-us/windows/win32/debug/system-error-codes--0-499-
    Official listing of all such codes.
'''


def is_pathname_valid(pathname: str) -> bool:
    """Entertaining stack overflow post by Cecil Curry. Path validity checks use this. 
        https://stackoverflow.com/questions/9532499/check-whether-a-path-is-valid-in-python-without-creating-a-file-at-the-paths-ta
    
    
    `True` if the passed pathname is a valid pathname for the current OS;
    `False` otherwise.
    """
    # If this pathname is either not a string or is but is empty, this pathname
    # is invalid.
    try:
        if not isinstance(pathname, str) or not pathname:
            return False

        # Strip this pathname's Windows-specific drive specifier (e.g., `C:\`)
        # if any. Since Windows prohibits path components from containing `:`
        # characters, failing to strip this `:`-suffixed prefix would
        # erroneously invalidate all valid absolute Windows pathnames.
        _, pathname = os.path.splitdrive(pathname)

        # Directory guaranteed to exist. If the current OS is Windows, this is
        # the drive to which Windows was installed (e.g., the "%HOMEDRIVE%"
        # environment variable); else, the typical root directory.
        root_dirname = os.environ.get('HOMEDRIVE', 'C:') \
            if sys.platform == 'win32' else os.path.sep
        assert os.path.isdir(root_dirname)   # ...Murphy and her ironclad Law

        # Append a path separator to this directory if needed.
        root_dirname = root_dirname.rstrip(os.path.sep) + os.path.sep

        # Test whether each path component split from this pathname is valid or
        # not, ignoring non-existent and non-readable path components.
        for pathname_part in pathname.split(os.path.sep):
            try:
                os.lstat(root_dirname + pathname_part)
            # If an OS-specific exception is raised, its error code
            # indicates whether this pathname is valid or not. Unless this
            # is the case, this exception implies an ignorable kernel or
            # filesystem complaint (e.g., path not found or inaccessible).
            #
            # Only the following exceptions indicate invalid pathnames:
            #
            # * Instances of the Windows-specific "WindowsError" class
            #   defining the "winerror" attribute whose value is
            #   "ERROR_INVALID_NAME". Under Windows, "winerror" is more
            #   fine-grained and hence useful than the generic "errno"
            #   attribute. When a too-long pathname is passed, for example,
            #   "errno" is "ENOENT" (i.e., no such file or directory) rather
            #   than "ENAMETOOLONG" (i.e., file name too long).
            # * Instances of the cross-platform "OSError" class defining the
            #   generic "errno" attribute whose value is either:
            #   * Under most POSIX-compatible OSes, "ENAMETOOLONG".
            #   * Under some edge-case OSes (e.g., SunOS, *BSD), "ERANGE".
            except OSError as exc:
                if hasattr(exc, 'winerror'):
                    if exc.winerror == ERROR_INVALID_NAME:
                        return False
                elif exc.errno in {errno.ENAMETOOLONG, errno.ERANGE}:
                    return False
    # If a "TypeError" exception was raised, it almost certainly has the
    # error message "embedded NUL character" indicating an invalid pathname.
    except TypeError as exc:
        return False
    # If no exception was raised, all path components and hence this
    # pathname itself are valid. (Praise be to the curmudgeonly python.)
    else:
        return True
    # If any other exception was raised, this is an unrelated fatal issue
    # (e.g., a bug). Permit this exception to unwind the call stack.
    #
    # Did we mention this should be shipped with Python already?

def validate_path(path: str):
    """Check if the path is valid and that it exists

    :param path: Path to validate
    :type path: str
    :raises ValueError: Path is invalid or doesnt exist
    :return: Validated path
    :rtype: str
    """
    if is_pathname_valid(path):
        if os.path.exists(path):
            return path
        else:
            raise ValueError('Path doesnt exist')
    else:
        raise ValueError('Invalid path')


def check_model(model: str):
    """Verify model is expected

    Args:
        model (str): Model name

    Raises:
        ValueError: Unexpected model supplied

    Returns:
        str: Model name
    """
    model_name = model.lower().replace(' ', '')
    valid_models = [
        'resnet20_cifar',
        'resnet50_cifar'
    ]

    if model_name in valid_models:
        return model
    else :
        raise ValueError('Unexpected model')


def validate_ipv4(addr: str):
    """Validate IPv4 redis socket

    Args:
        addr (str): [description]

    Returns:
        bool: Is valid IPv4
    """
    try:
        socket.inet_aton(addr)
    except socket.error as err:
        raise ValueError("IP address failed validation check. Error: {}".format(err))
    return addr

def validate_port(port: int):
    port_int = port
    if port_int < 65536:
        return port_int
    else:
        raise ValueError('Redis port out of range')

def get_check_path(env_key, arg_data):
    if env_key is not None:
        env_data = os.getenv(env_key)
    if arg_data is not None:
        #print("Checking arg value: {}".format(arg_data))
        return validate_path(arg_data)
    elif env_data is not None:
        return validate_path(env_data)
    else:
        raise ValueError('Unspecified or invalid {} parameter'.format(env_key))


def get_check_IPv4(env_key, arg_data):
    env_data = os.getenv(env_key)
    if arg_data is not None:
        return validate_ipv4(arg_data)
    elif env_data is not None:
        return validate_ipv4(env_data)
    else:
        raise ValueError('Unspecified {}'.format(env_key))

def get_check_port(env_key, arg_data):
    env_data = os.getenv(env_key)
    # if CLI specifies different port use that
    if arg_data != 6379:
        return validate_port(arg_data)

    # Otherwise check environment var
    elif env_data is not None and env_data != 6379:
        return validate_port(int(env_data))

    # return default
    elif env_data == 6379 or arg_data == 6379:
        return 6379
    else:
        raise ValueError('Unspecified or invalid redis port, add it to .env or CLI args')

def get_check_password(env_key, arg_data):
    logger.todo('Ping redis to check password is valid here')
    env_data = os.getenv(env_key)
    if arg_data is not None:
        return arg_data
    elif env_data is not None:
        return env_data
    else:
        return None