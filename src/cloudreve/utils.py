import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from requests import Session


def download_file(url: str, save_path: str, session: Session = None):
    s = session if session is not None else Session()
    destination = Path(save_path)
    temporary_path = None
    try:
        with s.get(url, stream=True) as response:
            response.raise_for_status()
            with NamedTemporaryFile(dir=destination.parent, delete=False) as f:
                temporary_path = Path(f.name)
                for chunk in response.iter_content(chunk_size=64 * 1024):
                    if chunk:
                        f.write(chunk)
        os.replace(temporary_path, destination)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
        if session is None:
            s.close()
