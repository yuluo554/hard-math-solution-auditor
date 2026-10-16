"""PyInstaller spec for GUI build.

目标：桌面报告形态，包含 Qt。
"""

import sys
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(r"D:\ProgramData\zcode\HWS-hard-math-solution-auditor")

# PyInstaller 配置
a = Analysis(
    [str(PROJECT_ROOT / "src" / "hws_math_auditor" / "gui" / "__init__.py")],
    pathto=[str(PROJECT_ROOT / "src")],
    binaries=[],
    datas=[
        # 数据文件
        (str(PROJECT_ROOT / "data" / "snapshots"), "data/snapshots"),
        (str(PROJECT_ROOT / "data" / "benchmarks"), "data/benchmarks"),
        (str(PROJECT_ROOT / "data" / "rules"), "data/rules"),
        (str(PROJECT_ROOT / "data" / "samples"), "data/samples"),
    ],
    hiddenimports=[
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不相关的包
        "tkinter",
        "matplotlib",
        "scipy",
        "numpy",
        "pandas",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="hws-audit-gui",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
