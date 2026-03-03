# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec 文件 - 报纸下载器
# 用法: pyinstaller newspaper_downloader.spec

block_cipher = None

# 数据文件（若有自定义配置文件可在此添加）
datas = []

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'requests',
        'PyPDF2',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='报纸下载器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,   # 无控制台窗口（GUI 应用）
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# 使用 onefile=False 可改为目录模式（启动更快）
# 目录模式需将 EXE 改为：
# exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='报纸下载器', ...)
# coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, ...)
