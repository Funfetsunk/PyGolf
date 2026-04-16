"""
editor.py — Course Editor entry point.

Run with:
    python editor.py

This is a developer tool.  Players should run main.py to play the game.
"""

import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(__file__))

import pygame


def main():
    try:
        import pygame_gui  # noqa: F401
    except ImportError:
        print("pygame_gui is required for the editor.")
        print("Install it with:  pip install pygame_gui")
        sys.exit(1)

    pygame.init()

    from tools.editor.editor_app import EditorApp
    app = EditorApp()
    app.run()


if __name__ == "__main__":
    main()
