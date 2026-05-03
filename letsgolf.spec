# letsgolf.spec — PyInstaller build spec for Let's Golf!
#
# Build:  pyinstaller letsgolf.spec
# Output: dist/LetsGolf/  (zip this folder for distribution)
#
# Saves and settings redirect to %APPDATA%\LetsGolf\ at runtime via
# src/utils/paths.py — the bundled data/settings.json is NOT included
# because it is user-writable.
#
# Icon: place a valid icon.ico at assets/ui/icon.ico to enable a custom
# icon.  The file assets/ui/icon.ico.png is not a valid .ico and is ignored.

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('assets',               'assets'),
        ('data/courses',         'data/courses'),
        ('data/game_config.json','data'),
        ('src',                  'src'),
    ],
    hiddenimports=['pygame', 'pygame._sdl2'],
    hookspath=[],
    runtime_hooks=[],
    excludes=['tools', 'editor'],
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name='LetsGolf',
    debug=False,
    console=False,
    icon=None,  # replace with 'assets/ui/icon.ico' once a valid .ico exists
)

coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    strip=False,
    name='LetsGolf',
)
