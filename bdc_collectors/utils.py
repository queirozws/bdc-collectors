#
# This file is part of Brazil Data Cube BDC-Collectors.
# Copyright (C) 2022 INPE.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/gpl-3.0.html>.
#

"""Define the BDC-Collector utilities used along the package."""

import contextlib
import logging
import os
from typing import Any

import requests
from tqdm import tqdm

from .exceptions import DownloadError


@contextlib.contextmanager
def working_directory(path):
    """Change working directory and returns to previous on exit.

    Exceptions:
        FileNotFoundError when could not change to directory provided.

    Args:
        path (str): Directory to change

    Returns:
        str Path to the changed directory

    Example:
        >>> import os
        >>> from tempfile import gettempdir
        >>> TEMP_DIR = gettempdir()
        >>> @working_directory(TEMP_DIR)
        ... def create_file(filename):
        ...     # Create file in Temporary folder
        ...     print('Current dir: {}'.format(os.getcwd()))
        ...     with open(filename, 'w') as f:
        ...         f.write('Hello World')
    """
    owd = os.getcwd()
    logging.debug("Changing working dir from %s to %s", owd, path)
    try:
        os.chdir(path)
        yield path
    finally:
        logging.debug("Back to working dir %s", owd)
        os.chdir(owd)


def download_stream(file_path: str, response: requests.Response, chunk_size=1024*64, progress=False, offset=0, total_size=None):
    """Download request stream data to disk.

    Args:
        file_path - Absolute file path to save
        response - HTTP Response object
    """
    parent = os.path.dirname(file_path)

    if parent:
        os.makedirs(parent, exist_ok=True)

    if not total_size:
        total_size = int(response.headers.get('Content-Length', 0))

    file_name = os.path.basename(file_path)

    progress_bar = tqdm(
        desc=file_name,
        total=total_size,
        unit="B",
        unit_scale=True,
        disable=not progress,
        initial=offset
    )

    mode = 'a+b' if offset else 'wb'

    # May throw exception for read-only directory
    with response:
        with open(file_path, mode) as stream:
            for chunk in response.iter_content(chunk_size):
                stream.write(chunk)
                progress_bar.update(chunk_size)

    file_size = os.stat(file_path).st_size

    if file_size != total_size:
        os.remove(file_path)
        raise DownloadError(f'Download file is corrupt. Expected {total_size} bytes, got {file_size}')


def entry_version(version: Any) -> str:
    """Retrieve the string representation of collection version for folders."""
    if (isinstance(version, str) and '.' in version) or isinstance(version, float):
        return f'v{version}'
    return 'v{0:03d}'.format(int(version))
