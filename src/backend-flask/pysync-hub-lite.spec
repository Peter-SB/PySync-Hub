# -*- mode: python ; coding: utf-8 -*-

import PyInstaller.config
PyInstaller.config.CONF['distpath'] = "../../dist"

a = Analysis(
    ['run.py'],
    pathex=['./app'],
    binaries=[],
    datas=[
        ("app", "app"), 
        ("config.py", "."),
        ("build", "build")
    ],
    hiddenimports=[
        'app',
        'flask',
        'flask_socketio',
        'flask_cors',
        'flask_migrate',
        'flask_sqlalchemy',
        'spotipy',
        'spotipy.oauth2',
        'yaml',
        'engineio.async_drivers.eventlet',  # if using eventlet
        'engineio.async_drivers.gevent',       # if using gevent
        'engineio.async_drivers.threading',   # if using threading
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='pysync-hub-lite',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='pysync-hub-lite',
)
