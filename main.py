"""
Let's Golf! - Main entry point.
Run this file to start the game: python main.py

The main loop is `async` so the same file can be built for the web/Android
with pygbag (`pygbag main.py`). On CPython `asyncio.run(main())` behaves
exactly like a normal loop; on Emscripten pygbag rewrites the `while True`
into a requestAnimationFrame driver, and the `await asyncio.sleep(0)` at the
bottom of the loop is what hands control back to the browser each frame.
"""

import asyncio
import sys

import pygame

from src.constants import SCREEN_W, SCREEN_H, FPS
from src.game import Game


_IS_WEB = sys.platform == "emscripten"


def _create_display():
    """Open the window/canvas at the logical 1280×720 size.

    On Emscripten (pygbag → phone browser) we also request FULLSCREEN and
    SCALED so the canvas fills the device and pygame auto-scales the logical
    surface — including translating mouse/touch event positions back into
    1280×720 coordinates, which is what every state expects.

    On desktop SCALED alone lets the player resize the window without any
    layout code having to care.
    """
    pygame.display.set_caption("Let's Golf!")
    flags = pygame.SCALED
    if _IS_WEB:
        flags |= pygame.FULLSCREEN
    return pygame.display.set_mode((SCREEN_W, SCREEN_H), flags)


async def main():
    pygame.init()
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

    screen = _create_display()
    clock  = pygame.time.Clock()

    # Pre-build all synthetic sounds (< 0.5 s; happens before the first frame)
    from src.utils.sound_manager import SoundManager
    SoundManager.instance().init()

    game = Game(screen)

    running = True
    while running:
        # Delta time in seconds — keeps game speed independent of frame rate
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            game.handle_event(event)

        if not running:
            break

        game.update(dt)
        game.draw()
        pygame.display.flip()

        # Yield to the browser event loop on Emscripten; no-op on desktop.
        await asyncio.sleep(0)

    pygame.quit()
    if not _IS_WEB:
        sys.exit()


if __name__ == "__main__":
    asyncio.run(main())
