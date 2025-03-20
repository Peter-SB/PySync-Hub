# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['./run.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('settings.yml', 'settings.yml'),
        ('database.db', 'database.db')
    ],
    hiddenimports=[
        'flask',
        'flask_socketio',
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
    a.binaries,
    a.datas,
    [],
    name='pysync-hub-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
