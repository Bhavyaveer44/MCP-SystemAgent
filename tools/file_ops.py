from pathlib import Path

WORKSPACE = (Path(__file__).parent.parent / "workspace").resolve()
WORKSPACE.mkdir(exist_ok=True)


class PathEscapeError(Exception):
    pass

def _safe_path(relative_path: str) -> Path:
    cleaned = (relative_path or ".").strip().replace("\\", "/").lstrip("/")
    if cleaned == "workspace" or cleaned.startswith("workspace/"):
        cleaned = cleaned[len("workspace"):].lstrip("/")
    cleaned = cleaned or "."
    candidate = (WORKSPACE / cleaned).resolve()
    if not candidate.is_relative_to(WORKSPACE):
        raise PathEscapeError(f"'{relative_path}' escapes the workspace jail")
    return candidate


def read_file(relative_path: str) -> str:
    path = _safe_path(relative_path)
    if not path.is_file():
        raise FileNotFoundError(f"{relative_path} not found")
    return path.read_text()


def read_files(relative_paths: list[str]) -> str:
    parts = []
    for p in relative_paths:
        try:
            parts.append(f"--- {p} ---\n{read_file(p)}")
        except Exception as e:
            parts.append(f"--- {p} ---\nERROR: {type(e).__name__}: {e}")
    return "\n\n".join(parts)


def write_file(relative_path: str, content: str) -> str:
    path = _safe_path(relative_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return f"Wrote {len(content)} bytes to {relative_path}"


def list_dir(relative_path: str = ".") -> list[str]:
    path = _safe_path(relative_path)
    if not path.is_dir():
        raise NotADirectoryError(f"{relative_path} is not a directory")
    return sorted(p.name for p in path.iterdir())


def delete_file(relative_path: str) -> str:
    path = _safe_path(relative_path)
    if not path.is_file():
        raise FileNotFoundError(f"{relative_path} not found")
    path.unlink()
    return f"Deleted {relative_path}"