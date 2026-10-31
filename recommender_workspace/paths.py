"""Keep user data outside the installed package, including through symlinks."""

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def private_path(path: Path) -> Path:
    """Resolve a user-data path and reject destinations inside this package."""
    resolved = path.expanduser().resolve()
    if resolved == PACKAGE_ROOT or PACKAGE_ROOT in resolved.parents:
        raise ValueError("user data must be stored outside the public skill package")
    return resolved
