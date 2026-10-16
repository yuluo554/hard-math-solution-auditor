"""字节冻结守门测试：文本行尾（eol=lf + CR 守门）。

纪律：源码与文档一律 LF；CR 进仓会在跨平台/CI 上引发 diff 噪声，
并可能污染被 sha256 登记的快照字节。快照与基准台账另有 `.gitattributes`
`-text` 保护（见 test_snapshot_bytes_are_not_renormalized）。
"""

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

# 豁免：明确声明为二进制的路径（.gitattributes 里标 binary / -text 的）
BINARY_SUFFIXES = {".exe", ".png", ".jpg", ".gif", ".pdf", ".zip", ".pyc"}


def _tracked_files():
    """取受跟踪文件列表（对非 ASCII 文件名稳健）。

    `git ls-files` 默认对非 ASCII 路径加引号 + 八进制转义（core.quotePath），
    且 Python 3.8 与 3.12 对该输出的解码行为不同——直接用会让判据
    随解释器版本变化（"本机 3.12 绿、3.8 红"）。故用 `-z`
    （NUL 分隔、不引号不转义）+ 显式 utf-8 解码。
    """
    out = subprocess.run(
        ["git", "-c", "core.quotePath=false", "ls-files", "-z"],
        cwd=str(REPO_ROOT),
        capture_output=True,
    )
    if out.returncode != 0:
        pytest.skip("非 git 工作树，跳过 CR 守门")
    return [
        p.decode("utf-8", errors="replace")
        for p in out.stdout.split(b"\x00")
        if p
    ]


def test_no_cr_in_tracked_text_files():
    """受跟踪的文本文件不得含 CR 字节。"""
    offenders = []
    scanned = 0
    for rel in _tracked_files():
        p = REPO_ROOT / rel
        if not p.exists():
            continue
        if p.suffix.lower() in BINARY_SUFFIXES:
            continue
        try:
            data = p.read_bytes()
        except OSError:
            continue
        scanned += 1
        if b"\r" in data:
            offenders.append(rel)

    assert scanned >= 30, f"扫描面仅 {scanned} 个文件，疑似路径解析错误（假门）"
    assert offenders == [], f"以下受跟踪文本文件含 CR 字节: {offenders}"


def test_snapshot_and_ledger_marked_text_negated():
    """快照与基准台账必须标 `-text`（防克隆时 EOL 归一破坏 sha256）。"""
    for rel in ("data/snapshots/BENCH-001.json", "data/benchmarks/BENCH-001.json"):
        out = subprocess.run(
            ["git", "check-attr", "text", "--", rel],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        assert out.returncode == 0, out.stderr
        assert "-text" in out.stdout, (
            f"{rel} 未标 -text，克隆时字节可能被归一化（sha256 会失配）: {out.stdout}"
        )
