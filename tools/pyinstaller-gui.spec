"""PyInstaller spec for GUI build.

目标：桌面报告形态，包含 Qt。
"""

import sys
from pathlib import Path

# 项目根目录：由本 spec 位置反推（tools/ 的上一级），不写死本机盘符
PROJECT_ROOT = Path(SPECPATH).resolve().parent

# PyInstaller 配置
a = Analysis(
    [str(PROJECT_ROOT / "src" / "hws_math_auditor" / "gui" / "__main__.py")],
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
        # 只用到 QtCore/QtGui/QtWidgets
        "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtQuick3D", "PySide6.QtQuickWidgets",
        "PySide6.QtPdf", "PySide6.QtPdfWidgets", "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets", "PySide6.Qt3DCore", "PySide6.Qt3DRender",
        "PySide6.QtMultimedia", "PySide6.QtCharts", "PySide6.QtDataVisualization",
        "PySide6.QtOpenGL", "PySide6.QtOpenGLWidgets", "PySide6.QtSql",
        "PySide6.QtTest", "PySide6.QtDesigner", "PySide6.QtUiTools",
        "PySide6.QtNetwork", "PySide6.QtSvg", "PySide6.QtPrintSupport",
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
    name="hws-audit-gui-win64",
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
