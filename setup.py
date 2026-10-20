"""构建钩子：把仓根 ``data/`` 拷进包内 ``_data/``，让 wheel 装完可用。

背景（2026-10-21 诊断 D2）：此前 wheel/sdist 里 ``data/`` 命中 0，
pip 常规安装后 ``selftest`` 报「自检失败」、``audit`` 抛 ``FileNotFoundError``。
``[tool.setuptools.package-data]`` 只能收**包目录内**的文件，收不到
``src/`` 之外的仓根 ``data/``，所以在 ``build_py`` 阶段先拷进包内再交给
setuptools 收——数据仍以仓根 ``data/`` 为唯一真源，不 `git mv`、不改布局。

冻结态（PyInstaller）不受影响：spec 的 datas 仍直接从仓根 ``data/`` 取，
运行时读 ``sys._MEIPASS/data``。

``_data/`` 是构建产物，已被 ``.gitignore`` 排除，不随仓库分发。
"""

import shutil
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py

ROOT = Path(__file__).resolve().parent
SOURCE_DATA = ROOT / "data"
PACKAGE_DATA = ROOT / "src" / "hws_math_auditor" / "_data"

#: 需要随包分发的数据子目录（与 tools/*.spec 的 datas 白名单同一口径）
DATA_SUBDIRS = ("rules", "benchmarks", "snapshots", "samples")


class build_py(_build_py):
    """把仓根 ``data/`` 的子目录拷进包内 ``_data/``，再走标准 build_py。"""

    def run(self):
        if PACKAGE_DATA.exists():
            shutil.rmtree(PACKAGE_DATA)
        PACKAGE_DATA.mkdir(parents=True)
        for name in DATA_SUBDIRS:
            source = SOURCE_DATA / name
            if not source.is_dir():
                raise SystemExit(
                    f"构建中止：缺少数据目录 {source}（wheel 装完会不可用）"
                )
            shutil.copytree(source, PACKAGE_DATA / name)
        super().run()


setup(cmdclass={"build_py": build_py})
