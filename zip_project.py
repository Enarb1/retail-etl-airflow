from __future__ import annotations

import argparse
import fnmatch
import os
from datetime import datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


EXCLUDED_DIRECTORY_NAMES = {
    ".git",
    ".github",
    ".idea",
    ".vscode",
    ".astro",
    ".venv",
    "venv",
    "env",
    "notebooks",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "htmlcov",
}

EXCLUDED_FILE_NAMES = {
    ".env",
    ".DS_Store",
    ".coverage",
}

EXCLUDED_FILE_PATTERNS = {
    "*.zip",
    "*.pyc",
    "*.pyo",
    "*.log",
}


def should_exclude(path: Path, project_dir: Path) -> bool:
    """Return True when a file or directory should not be archived."""
    relative_path = path.relative_to(project_dir)

    if any(part in EXCLUDED_DIRECTORY_NAMES for part in relative_path.parts):
        return True

    if path.name in EXCLUDED_FILE_NAMES:
        return True

    return any(
        fnmatch.fnmatch(path.name, pattern)
        for pattern in EXCLUDED_FILE_PATTERNS
    )


def create_project_zip(project_dir: Path, output_path: Path) -> int:
    """Create the ZIP archive and return the number of included files."""
    project_dir = project_dir.resolve()
    output_path = output_path.resolve()

    if not project_dir.is_dir():
        raise NotADirectoryError(f"Project directory does not exist: {project_dir}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists():
        output_path.unlink()

    included_files = 0

    with ZipFile(output_path, mode="w", compression=ZIP_DEFLATED) as archive:
        for root, directory_names, file_names in os.walk(project_dir):
            root_path = Path(root)

            # Prevent os.walk from entering excluded directories.
            directory_names[:] = [
                name
                for name in directory_names
                if not should_exclude(root_path / name, project_dir)
            ]

            for file_name in file_names:
                file_path = root_path / file_name

                if should_exclude(file_path, project_dir):
                    continue

                # Avoid including the output archive if it is inside the project.
                if file_path.resolve() == output_path:
                    continue

                # Keep the project folder as the ZIP's top-level directory.
                archive_name = Path(project_dir.name) / file_path.relative_to(project_dir)
                archive.write(file_path, archive_name)
                included_files += 1

    return included_files


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a clean ZIP archive of a project."
    )
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Project directory to archive. Defaults to this script's directory.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output ZIP path. Defaults to a timestamped ZIP beside the project.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()
    project_dir = args.project_dir.resolve()

    if args.output:
        output_path = args.output.expanduser()
        if not output_path.is_absolute():
            output_path = project_dir.parent / output_path
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = project_dir.parent / f"{project_dir.name}_{timestamp}.zip"

    try:
        included_files = create_project_zip(project_dir, output_path)
    except (OSError, ValueError) as error:
        raise SystemExit(f"Error: {error}") from error

    print(f"Created: {output_path}")
    print(f"Included files: {included_files}")


if __name__ == "__main__":
    main()
