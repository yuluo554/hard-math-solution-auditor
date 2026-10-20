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

    判据从"出现『CI 状态』四个字"收紧为**必须给出可核对的具体信息**
    （job 名 / Python 版本 / run id）——"字符串存在"式判据换掉那行文字仍绿，
    等于没有门（2026-10-21 诊断 D12b）。
    """
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    claims_ci_ran = "CI 状态" in readme or "首跑即绿" in readme
    claims_ci_not_run = "未跑过 CI" in readme

    assert claims_ci_ran or claims_ci_not_run, "README 未就 CI 状态作任何声明"
    assert not (claims_ci_ran and claims_ci_not_run), "README 的 CI 声明自相矛盾"

    if _release_record_exists():
        assert claims_ci_ran, "已发布却声称未跑过 CI"

    if claims_ci_ran:
        # 必须点出具体 job / 版本 / run id 之一 —— 否则"CI 状态"只是空话
        concrete = re.search(r"run \d{6,}|\(windows-latest / py3\.\d+\)|windows-latest", readme)
        assert concrete, (
            "README 声称跑过 CI，但没有给出可核对的 job 名 / 版本 / run id"
        )


def test_readme_release_status_shows_current_version():
    """诚实声明：README 的发布状态必须把**当前版本**标出来（D12a）。

    旧判据只查「M6 行有没有 ✅」，于是 M6 行永远停在 v0.1.1 也能绿——
    读者会以为最新发布是 v0.1.1。这里改成两个断言的合取：
    ① `pyproject.toml` 的版本号在 README 里出现（说明写的是当前版本）；
    ② 「当前最新」行必须 ✅。
    """
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    version = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.M)
    assert version, "pyproject.toml 未声明 version"
    current = version.group(1)

    assert f"v{current}" in readme, (
        f"README 未提及当前版本 v{current}（发布状态行可能停在旧版本）"
    )

    m = re.search(r"^\|.*当前最新.*\|.*$", readme, re.M)
    assert m, "README 缺少「当前最新」发布状态行"
    row = m.group(0)
    assert "✅" in row, "「当前最新」行未标 ✅（虚高或未更新）"
    assert f"v{current}" in row, (
        f"「当前最新」行写的不是 v{current}（版本口径漂移）: {row}"
    )


def test_readme_release_status_matches_record():
    """诚实声明：README 的 M6 发布状态必须与发布留档存在与否一致。"""
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    m = re.search(r"\| M6 发布（[^|]*\|([^|]*)\|", readme)
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


# ---------------------------------------------------------------------------
# 自述数字 ↔ 实物对撞（D4 / D5）
# ---------------------------------------------------------------------------
#
# 这类漂移的根因是「文档写的数字没人为它背书」：22 份台账被抄进四处文档，
# 而盘上只有 21 份也没人红。这里把口径钉在**盘上的实物**上：
# 文档里的份数 / 类数必须由 `data/` 真实文件算出，否则红。

DOC_FILES = ("README.md", "DEVELOPMENT.md", "data/README.md", "docs/技术报告.md")


def _doc_texts() -> dict:
    texts = {}
    for rel in DOC_FILES:
        path = REPO_ROOT / rel
        if path.exists():
            texts[rel] = path.read_text(encoding="utf-8")
    assert len(texts) >= 3, f"文档扫描面仅 {len(texts)} 份，疑似路径解析错误（假门）"
    return texts


def _ledger_count() -> int:
    """盘上冻结台账的真实份数。"""
    files = sorted((REPO_ROOT / "data" / "benchmarks").glob("BENCH-*.json"))
    assert files, "data/benchmarks 下没有任何 BENCH-*.json（扫描面为空）"
    return len(files)


def _error_type_count() -> int:
    """error_types.json 里的真实错误类型数。"""
    import json

    payload = json.loads(
        (REPO_ROOT / "data" / "rules" / "error_types.json").read_text(encoding="utf-8")
    )
    items = payload.get("error_types") or []
    assert items, "error_types.json 没有条目"
    return len(items)


def test_readme_ledger_count_matches_actual_files():
    """README 写的台账份数必须等于盘上真实份数（21）。"""
    count = _ledger_count()
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    m = re.search(r"BENCH-001\.\.(\d{3})", readme)
    assert m, "README 未写出台账编号区间（BENCH-001..NNN）"
    assert int(m.group(1)) == count, (
        f"README 写的末位编号 BENCH-{m.group(1)} != 盘上份数 {count}"
    )

    m2 = re.search(r"BENCH-001\.\.\d{3}[^|\n]*\|\s*\*{0,2}(\d+)\s*份", readme)
    assert m2, "README 判定依据表未写出台账份数"
    assert int(m2.group(1)) == count, (
        f"README 写的份数 {m2.group(1)} != 盘上份数 {count}"
    )


def test_no_doc_claims_wrong_ledger_count():
    """任何文档都不得写与实物不符的台账份数（防再次漂移）。"""
    count = _ledger_count()
    offenders = []
    for rel, text in _doc_texts().items():
        for m in re.finditer(r"BENCH-001\.\.(\d{3})", text):
            if int(m.group(1)) != count:
                offenders.append(f"{rel}: BENCH-001..{m.group(1)}（实际 {count} 份）")
        # 「N 份 ... 台账」形态
        for m in re.finditer(r"(\d+)\s*份[^\n]{0,12}台账", text):
            if int(m.group(1)) != count:
                offenders.append(f"{rel}: 「{m.group(1)} 份台账」（实际 {count} 份）")
    assert offenders == [], f"文档台账份数与实物不符: {offenders}"


def test_no_doc_says_wrong_error_type_count():
    """文档不得写与 error_types.json 不符的错误类型数（D5：8 类 / 9 类 / 六类）。

    唯一允许的"多一类"是**说清楚了**它多的是干净对照行：
    ``N+1`` 只有在同一句（前后 40 字内）出现「对照 / clean / 行覆盖度」时才放行，
    否则「9 类错误类型」这种把 clean 混算成错误类型的写法照样红。
    """
    count = _error_type_count()
    offenders = []
    for rel, text in _doc_texts().items():
        for m in re.finditer(r"(\d+|[一二三四五六七八九十])\s*类(?:错误|植入)", text):
            token = m.group(1)
            digits = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
                      "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}.get(token)
            value = int(token) if token.isdigit() else digits
            if value is None or value == count:
                continue
            window = text[max(0, m.start() - 40): m.end() + 40]
            explains_clean = (
                value == count + 1
                and any(k in window for k in ("对照", "clean", "行覆盖度", "干净"))
            )
            if not explains_clean:
                offenders.append(
                    f"{rel}: 「{token} 类」（实际 {count} 类 + 1 类干净对照）→ …{window.strip()}…"
                )
    assert offenders == [], f"文档错误类型数与实物不符: {offenders}"


def test_benchmark_output_prints_error_types_plus_clean():
    """`benchmark --run` 的覆盖度行数 == error_types 条目数 + 1（clean）。"""
    r = subprocess.run(
        [sys.executable, "-m", "hws_math_auditor", "benchmark", "--run"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert r.returncode == 0, r.stdout + r.stderr

    # 抓「=== 覆盖度 ===」到「=== 逐条结果 ===」之间的 ✅/❌ 行
    block = r.stdout.split("=== 覆盖度 ===")[1].split("=== 逐条结果 ===")[0]
    rows = [ln for ln in block.splitlines() if "✅" in ln or "❌" in ln]
    assert len(rows) == _error_type_count() + 1, (
        f"覆盖度打印 {len(rows)} 行，期望 {_error_type_count()} 类 + 1 行 clean\n"
        + "\n".join(rows)
    )
    assert any("clean" in ln for ln in rows), "覆盖度未单列 clean 行"
