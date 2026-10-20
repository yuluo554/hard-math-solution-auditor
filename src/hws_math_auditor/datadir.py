"""随包数据目录解析（单一实现点）。

三种运行形态的数据布局：

| 形态 | 解析结果 |
|---|---|
| PyInstaller 冻结态 | ``sys._MEIPASS/data``（spec 的 datas 写到这里） |
| 源码态 / editable 安装 | ``<repo>/data``（``src/hws_math_auditor/datadir.py`` → parents[2]） |
| pip 常规安装（wheel） | ``<site-packages>/hws_math_auditor/_data``（`setup.py` 的 build_py 钩子拷入） |

历史坑：三处（``cli._resolve_data_dir`` / ``pipeline.selftest`` /
``rules.load_threshold_table``）各自写 ``Path(__file__).parents[N] / "data"``，
源码态能用、**装态全废**（解析到 ``site-packages/data``）——2026-10-21 的诊断
D2/D10 就是它。本模块把"源码态 vs 装态"这一层收成唯一实现点，
冻结态（``sys._MEIPASS``）分支保持原样，三处调用方各自保留。

数据缺失一律抛 :class:`DataUnavailable`（``FileNotFoundError`` 子类，
老调用方 ``except FileNotFoundError`` 不受影响），CLI 层映射成**退出码 2**
（用法与输入不可用），而不是压成 1 让用户误以为"解答有错"。
"""

from __future__ import annotations

import sys
from pathlib import Path

#: 轮子内数据目录名（由 `setup.py` 的 build_py 钩子从仓根 `data/` 拷入）
PACKAGED_DATA_DIRNAME = "_data"

#: 数据目录下必须存在的条目（自检与装态定位共用，避免两处口径漂移）
REQUIRED_ENTRIES = ("rules/thresholds.json", "benchmarks", "snapshots")


class DataUnavailable(FileNotFoundError):
    """随包数据不可用（缺目录 / 缺必需条目）。

    继承 ``FileNotFoundError`` 是为了让既有的 ``except FileNotFoundError``
    调用点继续成立；CLI 层单独捕获本类以给出**友好提示 + exit 2**。
    """

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def is_frozen() -> bool:
    """是否运行在 PyInstaller 冻结态。"""
    return bool(getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"))


def locate_data_dir() -> Path:
    """解析随包数据目录（**不**校验存在性）。

    冻结态由调用方各自处理 ``sys._MEIPASS`` 分支；本函数只负责
    非冻结态的两种布局：
    1. 源码态 / editable：``<repo>/data``
    2. 装态：``<site-packages>/hws_math_auditor/_data``
    """
    # datadir.py = <root>/src/hws_math_auditor/datadir.py → parents[2] = <root>
    source_layout = Path(__file__).resolve().parents[2] / "data"
    if source_layout.is_dir():
        return source_layout
    return Path(__file__).resolve().parent / PACKAGED_DATA_DIRNAME


def missing_entries(data_dir: Path) -> list[str]:
    """列出数据目录下缺失的必需条目（空列表 = 齐全）。"""
    if not data_dir.is_dir():
        return [str(data_dir)]
    return [rel for rel in REQUIRED_ENTRIES if not (data_dir / rel).exists()]


def require_data_dir() -> Path:
    """取数据目录；不可用则抛 :class:`DataUnavailable`（附可操作提示）。"""
    data_dir = locate_data_dir()
    missing = missing_entries(data_dir)
    if missing:
        raise DataUnavailable(missing_message(data_dir, missing))
    return data_dir


def missing_message(data_dir: Path, missing: list[str]) -> str:
    """构造可操作的数据缺失提示（不引导用户去猜路径）。"""
    if not data_dir.is_dir():
        detail = "  整个数据目录不存在"
    else:
        detail = f"  缺失条目: {', '.join(missing)}"
    return (
        f"随包数据不可用：{data_dir}\n"
        f"{detail}\n"
        "  可能原因：\n"
        "    1. 源码树不完整（缺 data/ 目录）—— 请从完整仓库检出或解压源码包；\n"
        "    2. wheel 安装后数据未随包 —— 重装同一 wheel（v0.2.1 起数据随 wheel 分发）；\n"
        "    3. 免安装 exe 被单独改名/移走 —— 请使用 Release 原始 exe。\n"
        "  退出码 2 表示『用法与输入不可用』，不是『解答含错』。"
    )
