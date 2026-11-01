# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build specification for Project Report Manager desktop application."""

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

project_root = Path.cwd().resolve()

# 1. Collect Datas (Alembic configuration and migration versions)
datas = [
    (str(project_root / "alembic.ini"), "."),
    (str(project_root / "migrations"), "migrations"),
]

# Collect any package-specific data files
datas += collect_data_files("openpyxl")
datas += collect_data_files("reportlab")

# 2. Collect Hidden Imports
hiddenimports = [
    "app",
    "app.main",
    "app.config",
    "app.common",
    "app.domain",
    "app.application",
    "app.infrastructure",
    "app.presentation",
    "sqlalchemy",
    "sqlalchemy.sql.default_comparator",
    "alembic",
    "alembic.runtime.migration",
    "alembic.script",
    "cryptography",
    "openpyxl",
    "docx",
    "reportlab",
    "reportlab.lib",
    "reportlab.platypus",
    "reportlab.pdfgen",
    "PySide6",
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
]

# Add all application submodules to hiddenimports
hiddenimports += collect_submodules("app")
hiddenimports += collect_submodules("migrations.versions")

a = Analysis(
    [str(project_root / "app" / "main.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "scipy", "numpy", "IPython", "jupyter"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ProjectReportManager",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI application, no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="ProjectReportManager",
)
