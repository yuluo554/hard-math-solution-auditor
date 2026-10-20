"""判定依据「表 ↔ 代码」对撞守门（2026-10-21 诊断 D8 的第二条）。

背景：`data/rules/thresholds.json` 里的 `threshold` 只被 `validate_threshold_table`
做格式校验，**引擎侧真正用的是 `config.tolerance`**。也就是说改表里的 `1e-09`
不会改变任何判定，而此前没有任何一条测试断言"两边相等"——表可以是"装饰"。

同理 `error_types.json` 的 `min_coverage` 只保证"条目级之和 == 汇总"（json 自洽），
引擎侧的覆盖度分母来自 `GeneratorConfig.min_coverage` 硬编码。两处漂移不会红。

本文件把这两对钉死：
1. `THR-001` / `THR-002` 的 `threshold` == `config.tolerance`（数值相等）
2. `error_types.json` 的 8 个 `min_coverage` 逐项 == `GeneratorConfig.min_coverage`

破坏任一即红；负控见 plan/RELEASE-M9.md §六。
"""

import json
import math
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
THRESHOLDS = REPO_ROOT / "data" / "rules" / "thresholds.json"
ERROR_TYPES = REPO_ROOT / "data" / "rules" / "error_types.json"

#: 引擎实际消费的两个规则（tolerance 的唯一定义点在 config.py）
COUPLED_RULES = ("THR-001", "THR-002")


def _rules():
    return json.loads(THRESHOLDS.read_text(encoding="utf-8"))["rules"]


def _error_types():
    return json.loads(ERROR_TYPES.read_text(encoding="utf-8"))["error_types"]


def test_thresholds_match_config_tolerance():
    """阈值表里引擎实际使用的那几条必须等于 config.tolerance。

    这是把"判定依据文件"与"代码里的唯一定义点"钉在一起的唯一办法：
    否则表可以被改成任意值而不影响判定（D8 附带发现）。
    """
    from hws_math_auditor.config import config

    rules = {r["id"]: r for r in _rules()}
    assert rules, "阈值表没有规则（扫描面为空）"

    checked = 0
    for rid in COUPLED_RULES:
        assert rid in rules, f"阈值表缺 {rid}（引擎消费口径变了？）"
        rule = rules[rid]
        assert math.isclose(rule["threshold"], config.tolerance, rel_tol=0, abs_tol=0), (
            f"{rid}.threshold={rule['threshold']!r} != config.tolerance={config.tolerance!r}"
            f" —— 改表不改判定，两边必须逐位相等"
        )
        checked += 1

    assert checked == len(COUPLED_RULES), "耦合规则未全部校验（假门）"


def test_threshold_table_is_not_decoration():
    """至少有一条 verified 规则确实被引擎口径引用（不是全表装饰）。"""
    from hws_math_auditor.config import config

    rules = [r for r in _rules() if r.get("status") == "verified"]
    assert rules, "阈值表没有 verified 规则"
    hits = [r["id"] for r in rules if math.isclose(r["threshold"], config.tolerance,
                                                   rel_tol=0, abs_tol=0)]
    assert hits, (
        "没有任何 verified 规则的 threshold 等于 config.tolerance —— "
        "阈值表完全没被引擎口径使用（判定依据是装饰）"
    )


def test_error_type_min_coverage_matches_generator_config():
    """error_types.json 的 min_coverage 必须逐项等于 GeneratorConfig.min_coverage。"""
    from hws_math_auditor.benchmark.generator import GeneratorConfig

    expected = GeneratorConfig().min_coverage
    actual = {item["code"]: item["min_coverage"] for item in _error_types()}

    assert actual, "error_types.json 没有条目（扫描面为空）"
    assert set(actual) == set(expected), (
        f"错误类型集合不一致：json={sorted(actual)} vs 代码={sorted(expected)}"
    )
    mismatched = {
        k: (actual[k], expected[k]) for k in actual if actual[k] != expected[k]
    }
    assert not mismatched, (
        f"min_coverage 与代码常量不一致（改 json 不改覆盖度分母）: {mismatched}"
    )


def test_error_type_total_matches_generator_sum():
    """json 的 total_min_coverage 必须等于代码侧分母之和。"""
    from hws_math_auditor.benchmark.generator import GeneratorConfig

    payload = json.loads(ERROR_TYPES.read_text(encoding="utf-8"))
    assert payload["total_min_coverage"] == sum(GeneratorConfig().min_coverage.values()), (
        "total_min_coverage 与 GeneratorConfig.min_coverage 之和不等"
    )


def test_clean_cases_min_matches_generator_config():
    """干净对照条数（clean_cases_min）必须等于 GeneratorConfig.clean_cases。"""
    from hws_math_auditor.benchmark.generator import GeneratorConfig

    payload = json.loads(ERROR_TYPES.read_text(encoding="utf-8"))
    assert payload["clean_cases_min"] == GeneratorConfig().clean_cases, (
        f"clean_cases_min={payload['clean_cases_min']} != "
        f"GeneratorConfig.clean_cases={GeneratorConfig().clean_cases}"
    )


def test_benchmark_run_reports_these_numbers():
    """CLI 实跑必须印证上面几个数（防"测试打的是另一份数据"）。"""
    import re
    import subprocess
    import sys

    r = subprocess.run(
        [sys.executable, "-m", "hws_math_auditor", "benchmark", "--run"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert r.returncode == 0, r.stdout + r.stderr

    total = re.search(r"总用例:\s*(\d+)", r.stdout)
    clean = re.search(r"干净:\s*(\d+)", r.stdout)
    assert total, "benchmark --run 未打印总用例"
    assert clean, "benchmark --run 未打印干净用例数"

    from hws_math_auditor.benchmark.generator import GeneratorConfig

    cfg = GeneratorConfig()
    assert int(total.group(1)) == cfg.clean_cases + sum(cfg.min_coverage.values())
    assert int(clean.group(1)) == cfg.clean_cases
