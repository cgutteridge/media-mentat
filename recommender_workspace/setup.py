"""Create blank private records without replacing existing answers."""

from pathlib import Path

from recommender_workspace.paths import PACKAGE_ROOT, private_path


def init_workspace(workspace: Path) -> list[Path]:
    """Create missing workspace files only; refuse paths into the package."""
    root = private_path(workspace)
    targets = {
        root / "taste/grilling-record.md": "grilling-record.md",
        root / "taste/inventory.md": "inventory.md",
        root / "sources.md": "sources.md",
    }
    # Validate all destinations before any filesystem mutation, including links.
    for target in (*targets, root / "findings", root / "research", root / "history", root / "documents"):
        private_path(target)
    created = []
    for target, template in targets.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            with target.open("x", encoding="utf-8") as stream:
                stream.write((PACKAGE_ROOT / "templates" / template).read_text(encoding="utf-8"))
        except FileExistsError:
            continue
        created.append(target)
    for name in ("findings", "research", "history", "documents"):
        (root / name).mkdir(parents=True, exist_ok=True)
    return created
