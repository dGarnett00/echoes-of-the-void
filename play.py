#!/usr/bin/env python3
"""One-command launcher for Echoes of the Void.

Usage:
    python play.py

Automatically checks Python version and installs missing dependencies,
then starts the game. Works on Windows, macOS, and Linux.
"""

import sys
import subprocess
import importlib


def _check_python_version() -> None:
    if sys.version_info < (3, 8):
        print(
            f"Python 3.8 or higher is required. "
            f"You are running Python {sys.version_info.major}.{sys.version_info.minor}.\n"
            "Please upgrade Python and try again."
        )
        sys.exit(1)


def _ensure_dependencies() -> None:
    packages = {"colorama": "colorama", "yaml": "pyyaml"}
    missing = [pkg for mod, pkg in packages.items() if importlib.util.find_spec(mod) is None]
    if missing:
        print(f"Installing missing dependencies: {', '.join(missing)} ...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install"] + missing,
                stdout=subprocess.DEVNULL,
            )
            print("Dependencies installed successfully.\n")
        except subprocess.CalledProcessError:
            print(
                f"Failed to install dependencies: {', '.join(missing)}.\n"
                "Try running: pip install colorama pyyaml"
            )
            sys.exit(1)


def main() -> None:
    _check_python_version()
    _ensure_dependencies()
    try:
        import run
        run.main()
    except (ImportError, ModuleNotFoundError) as exc:
        print(f"Could not load game module: {exc}\nEnsure you are running from the project root.")
        sys.exit(1)
    except Exception as exc:
        print(f"An unexpected error occurred while starting the game: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
