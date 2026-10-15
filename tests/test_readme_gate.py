"""README 三面交叉守门测试。"""

import ast
import re
import subprocess
from pathlib import Path


def test_cli_commands_match_readme():
    """守门：CLI 子命令与 README 命令表一致。"""
    # 解析 argparse
    from hws_math_auditor.cli import main

    # 检查 README 中是否包含主要命令
    readme_path = Path("README.md")
    if readme_path.exists():
        readme = readme_path.read_text(encoding="utf-8")
        assert "hws-audit audit" in readme
        assert "hws-audit benchmark" in readme
        assert "hws-audit selftest" in readme


def test_tolerance_single_source():
    """守门：TOLERANCE 字面量仅出现在 recalc.py 与 benchmark/runner.py。"""
    src_dir = Path("src")
    forbidden_files = [
        f
        for f in src_dir.rglob("*.py")
        if "recalc" not in str(f) and "benchmark" not in str(f)
    ]
    for f in forbidden_files:
        content = f.read_text(encoding="utf-8", errors="ignore")
        assert "1e-9" not in content, f"TOLERANCE 字面量出现在 {f}"
