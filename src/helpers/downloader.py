import requests
from pathlib import Path


def download_file_to_local(url: str, local_path: Path, parent_mkdir: bool = True) -> bool:
    if not isinstance(local_path, Path):
        raise TypeError("local_path must be a pathlib.Path")

    if parent_mkdir:
        local_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        local_path.write_bytes(r.content)
        return True
    except requests.RequestException as e:
        print(f"Failed downloading file from {url}: {e}")
        return False
