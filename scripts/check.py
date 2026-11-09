import ast
import subprocess
import sys
import warnings
from pathlib import Path


def main() -> None:
    warnings.simplefilter("error")
    for directory in (Path("."), Path("scripts"), Path("tests")):
        for path in directory.glob("*.py"):
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for arguments in (
        ["ruff", "check", "."],
        [sys.executable, "-m", "pytest", "-W", "error"],
        ["pip-audit", "--progress-spinner=off"],
    ):
        subprocess.run(arguments, check=True)


if __name__ == "__main__":
    main()
