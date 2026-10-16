"""README 三面交叉守门测试。

三面 = README 指令面 ↔ CLI 命令面 ↔ 源码/测试面。
- 命令面：README 提到的子命令必须真存在（反射 argparse）
- 数值口径面：政策数值字面量只允许出现在唯一来源（config.py）
- 结构面：README 承诺的退出码语义与诚实声明在位
"""

import ast
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _cli_subcommands() -> set:
    """反射 cli.py 的 argparse，取真实子命令集合。"""
    src = (SRC / "hws_math_auditor" / "cli.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    subs = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "add_parser"
            and node.args
            and isinstance(node.args[0], ast.Constant)
        ):
            subs.add(node.args[0].value)
    return subs


def test_cli_commands_match_readme():
    """README 命令表必须覆盖 CLI 全部真实子命令。"""
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    subs = _cli_subcommands()
    assert subs, "未从 cli.py 反射到任何子命令（扫描面为空 = 假门）"

    for sub in sorted(subs):
        assert f"hws-audit {sub}" in readme, f"README 未提及子命令: {sub}"


def test_readme_has_exit_code_semantics():
    """README 必须写明退出码三语义（0/1/2）。"""
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "退出码" in readme, "README 缺少退出码章节"
    for token in ("0", "1", "2"):
        assert re.search(rf"\|\s*{token}\s*\|", readme), f"退出码 {token} 未在表中"


def _release_record_exists() -> bool:
    """发布留档是否存在。

    用**仓库内文件**而不是 `git tag -l` 作判据——CI 浅克隆（actions/checkout
    默认 fetch-depth=1 且不取 tag）里 `git tag` 会返回空，判据就随环境变
    （本机绿、CI 红）。入库文件在任何检出形态下都在，是稳定的判据输入。
    """
    return (REPO_ROOT / "plan" / "RELEASE-M6.md").exists()


def test_readme_ci_claim_matches_reality():
    """诚实声明：README 的 CI 表述必须与实况一致。

    已发布（有发布留档）后应声称 CI 已跑；否则必须写"未跑过 CI"。
    """
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    claims_ci_ran = "首跑即绿" in readme or "CI 状态" in readme
    claims_ci_not_run = "未跑过 CI" in readme

    assert claims_ci_ran or claims_ci_not_run, "README 未就 CI 状态作任何声明"
    assert not (claims_ci_ran and claims_ci_not_run), "README 的 CI 声明自相矛盾"

    if _release_record_exists():
        assert claims_ci_ran, "已发布却声称未跑过 CI"
    else:
        assert claims_ci_not_run, "未发布却声称 CI 已跑（虚高）"


def test_readme_release_status_matches_record():
    """诚实声明：README 的 M6 发布状态必须与发布留档存在与否一致。"""
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    m = re.search(r"\| M6 发布（GitHub）\s*\|([^|]*)\|", readme)
    assert m, "README 缺少 M6 发布状态行"
    cell = m.group(1)

    if _release_record_exists():
        assert "✅" in cell, "已有发布留档却把 M6 发布标为未完成"
    else:
        assert "⬜" in cell, "M6 发布未完成却标为完成（虚高）"


def test_tolerance_single_source():
    """守门：政策数值字面量只允许出现在 config.py（K8 唯一定义点）。

    受管面 = src/hws_math_auditor 下全部 .py（config.py 除外）。
    任何其他文件出现数值口径字面量即红——含 recalc / verifier / benchmark。
    """
    literal = "1e" + "-9"
    allowed = {SRC / "hws_math_auditor" / "config.py"}

    offenders = []
    scanned = 0
    for f in sorted((SRC / "hws_math_auditor").rglob("*.py")):
        if f in allowed:
            continue
        scanned += 1
        content = f.read_text(encoding="utf-8", errors="ignore")
        if literal in content:
            offenders.append(str(f.relative_to(REPO_ROOT)))

    assert scanned >= 10, f"扫描面仅 {scanned} 个文件，疑似路径解析错误（假门）"
    assert offenders == [], f"数值口径字面量出现在: {offenders}"
