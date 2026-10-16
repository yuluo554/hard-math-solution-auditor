"""README 三面交叉守门测试。

三面 = README 指令面 ↔ CLI 命令面 ↔ 源码/测试面。
- 命令面：README 提到的子命令必须真存在（反射 argparse）
- 数值口径面：政策数值字面量只允许出现在唯一来源（config.py）
- 结构面：README 承诺的退出码语义与诚实声明在位
"""

import ast
import re
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


def test_readme_states_ci_not_run():
    """诚实声明：未推送时 README 不得声称 CI 已跑。"""
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "未跑过 CI" in readme, "README 缺少'未跑过 CI'的诚实声明"


def test_readme_release_status_not_claimed_done():
    """诚实声明：M6 发布未完成时不得标 ✅。"""
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    m = re.search(r"\| M6 发布（GitHub）\s*\|([^|]*)\|", readme)
    assert m, "README 缺少 M6 发布状态行"
    assert "⬜" in m.group(1), "M6 发布未完成却标为完成（虚高）"


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
