#!/usr/bin/env python3
"""Entry point for Echoes of the Void."""

import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.game import Game


def main() -> None:
    """Start the game."""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
