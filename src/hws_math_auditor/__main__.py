"""CLI 入口 — 绝对导入薄模块（PyInstaller 构建安全）。"""

import sys

from hws_math_auditor.cli import main

if __name__ == "__main__":
    sys.exit(main())
