# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('C:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python312\\tcl\\tcl8.6', 'tcl8.6'), ('C:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python312\\tcl\\tk8.6', 'tk8.6')]
binaries = [('C:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python312\\DLLs\\tcl86t.dll', '.'), ('C:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python312\\DLLs\\tk86t.dll', '.'), ('C:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python312\\python312.dll', '.')]
hiddenimports = ['tkinter', 'tkinter.ttk', '_tkinter', 'requests', 'psutil']
tmp_ret = collect_all('tkinter')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['CleanMaster.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['_pyi_rth_tkinter'],
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
    name='文洲系统清理大师',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.ico'],
)
