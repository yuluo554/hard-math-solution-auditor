"""PyInstaller spec for CLI build.

目标：纯 CLI，排除 Qt，最小化体积。
"""

import sys
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(r"D:\ProgramData\zcode\HWS-hard-math-solution-auditor")

# PyInstaller 配置
a = Analysis(
    [str(PROJECT_ROOT / "src" / "hws_math_auditor" / "__main__.py")],
    pathto=[str(PROJECT_ROOT / "src")],
    binaries=[],
    datas=[
        # 数据文件
        (str(PROJECT_ROOT / "data" / "snapshots"), "data/snapshots"),
        (str(PROJECT_ROOT / "data" / "benchmarks"), "data/benchmarks"),
        (str(PROJECT_ROOT / "data" / "rules"), "data/rules"),
        (str(PROJECT_ROOT / "data" / "samples"), "data/samples"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除 Qt
        "PySide6",
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "PySide6.QtQuick",
        "PySide6.QtQml",
        "PySide6.QtWebEngine",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebChannel",
        "PySide6.QtSvg",
        "PySide6.QtOpenGL",
        "PySide6.QtPrintSupport",
        "PySide6.QtHelp",
        "PySide6.QtTest",
        "PySide6.QtSql",
        "PySide6.QtNetwork",
        "PySide6.QtSerialPort",
        "PySide6.QtScxml",
        "PySide6.QtStateMachine",
        "PySide6.QtLocation",
        "PySide6.QtPositioning",
        "PySide6.QtSensors",
        "PySide6.QtSerialBus",
        "PySide6.QtRemoteObjects",
        "PySide6.QtWebSockets",
        "PySide6.QtTextToSpeech",
        "PySide6.Qt3D",
        "PySide6.QtCharts",
        "PySide6.QtDataVisualization",
        "PySide6.QtUiTools",
        # 排除 GUI 相关
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
    name="hws-audit-cli",
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
    icon=None,
)
