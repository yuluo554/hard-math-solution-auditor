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
    """快照 / 基准台账 / 规则表必须真冻结字节（`text` 为 unset）。

    判据来自 `.gitattributes`，只在 git 工作树里成立；sdist（无 `.git`）里
    skip —— 与本文件 `_tracked_files()` 的既有口径一致，**不是放宽门禁**：
    CI 与任何真实仓库检出都带 `.git`，这条会真跑。

    **口径修正（2026-10-21，D8）**：旧写法是 `text=-text`，`git check-attr`
    回显字面量 `-text`，看着像冻结、实际被当成"文本"处理（真实验证：往里写
    CRLF 后提交，blob 里 CR 被抹掉）。正确写法是裸 `-text`（回显 `text: unset`）。
    因此这里不再匹配字符串 "-text"，而是断言**真语义 + 真实字节不变**。
    """
    if not (REPO_ROOT / ".git").exists():
        pytest.skip("非 git 工作树（如 sdist 内），.gitattributes 判据不适用")

    for rel in (
        "data/snapshots/BENCH-001.json",
        "data/benchmarks/BENCH-001.json",
        "data/rules/thresholds.json",
        "data/rules/error_types.json",
    ):
        out = subprocess.run(
            ["git", "check-attr", "text", "--", rel],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        assert out.returncode == 0, out.stderr
        assert "text: unset" in out.stdout, (
            f"{rel} 的 text 属性不是 unset（克隆时字节可能被归一化，sha256 会失配）: {out.stdout}"
        )


def test_frozen_files_blob_bytes_equal_worktree_bytes():
    """行为面自证：已提交 blob 的字节 == 工作树字节（EOL 未被改写）。"""
    if not (REPO_ROOT / ".git").exists():
        pytest.skip("非 git 工作树（如 sdist 内）")

    for rel in (
        "data/snapshots/BENCH-001.json",
        "data/benchmarks/BENCH-001.json",
        "data/rules/thresholds.json",
    ):
        blob = subprocess.run(
            ["git", "cat-file", "blob", f"HEAD:{rel}"],
            cwd=str(REPO_ROOT),
            capture_output=True,
        )
        assert blob.returncode == 0, f"取不到 HEAD:{rel}"
        worktree = (REPO_ROOT / rel).read_bytes()
        assert blob.stdout == worktree, (
            f"{rel} 的提交字节与工作树字节不同（EOL 被归一化了）"
        )


def test_binary_macro_not_applied_to_json():
    """JSON 不得被 `binary` 宏覆盖（否则 `git diff` 只输出 Bin N -> M bytes，D8）。

    真正的二进制（png/gif/zip/exe）仍应是 binary；JSON 只冻结字节、保留 diff。
    """
    if not (REPO_ROOT / ".git").exists():
        pytest.skip("非 git 工作树（如 sdist 内）")

    for rel in ("data/rules/thresholds.json", "data/benchmarks/BENCH-001.json"):
        out = subprocess.run(
            ["git", "check-attr", "diff", "--", rel],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        assert out.returncode == 0, out.stderr
        assert "diff: unset" not in out.stdout, (
            f"{rel} 被标成 binary（diff 失效，看不到改了哪条阈值）: {out.stdout}"
        )
