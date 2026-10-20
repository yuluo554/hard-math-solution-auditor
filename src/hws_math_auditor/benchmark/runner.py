"""模块⑤-b：基准 Runner。

加载真值台账 → 运行引擎 → 计算指标。
零模型依赖，离线可复跑。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from hws_math_auditor.benchmark.generator import BenchmarkCase, BenchmarkGenerator
from hws_math_auditor.model import AuditReport
from hws_math_auditor.pipeline import AuditRequest, audit


# ---------------------------------------------------------------------------
# 数据类
# ---------------------------------------------------------------------------

@dataclass
class BenchmarkResult:
    """单条基准运行结果。"""

    case: BenchmarkCase
    report: AuditReport
    first_error_step: Optional[int]
    error_type_detected: Optional[str]
    passed: bool  # 是否通过（干净判干净 / 含错判含错且定位正确）
    explanation: str


@dataclass
class Metrics:
    """基准指标。"""

    false_positive_rate: float  # 误报率：干净解答被判为错
    localization_accuracy: float  # 错误定位准确率
    total_cases: int
    clean_cases: int
    dirty_cases: int
    coverage: dict  # 按错误类型的覆盖度

    def to_dict(self) -> dict[str, Any]:
        return {
            "false_positive_rate": self.false_positive_rate,
            "localization_accuracy": self.localization_accuracy,
            "total_cases": self.total_cases,
            "clean_cases": self.clean_cases,
            "dirty_cases": self.dirty_cases,
            "coverage": self.coverage,
        }


# ---------------------------------------------------------------------------
# 加载真值台账
# ---------------------------------------------------------------------------

def load_ground_truth(bench_dir: str | Path) -> list[BenchmarkCase]:
    """加载真值台账。

    从 {bench_dir}/benchmarks/ 目录读取所有 BENCH-*.json 文件。
    """
    bench_path = Path(bench_dir)
    if not bench_path.exists():
        raise FileNotFoundError(f"基准目录不存在: {bench_path}")

    cases: list[BenchmarkCase] = []
    for f in sorted(bench_path.glob("BENCH-*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        case = BenchmarkCase(
            id=data["id"],
            input=data["input"],
            expect=data["expect"],
            meta=data["meta"],
        )
        cases.append(case)

    if not cases:
        raise FileNotFoundError(f"基准目录中无 BENCH-*.json 文件: {bench_path}")

    return cases


# ---------------------------------------------------------------------------
# 运行单条
# ---------------------------------------------------------------------------

def run_single(case: BenchmarkCase) -> BenchmarkResult:
    """运行单条基准用例。"""
    solution = case.input["solution"]
    problem = case.input.get("problem", "")

    request = AuditRequest(solution_text=solution, final_assertion=problem)
    result = audit(request)

    report = result.report
    first_error = report.first_error.first_error if report else None

    # 判定是否通过
    is_clean_expected = case.expect["is_clean"]
    is_clean_observed = first_error is None

    if is_clean_expected and is_clean_observed:
        passed = True
    elif not is_clean_expected and not is_clean_observed:
        # 含错解答：检查首错定位是否正确
        expected_step = case.expect["first_error_step"]
        passed = first_error == expected_step
    else:
        passed = False

    # 检测到的错误类型
    error_type_detected = None
    if first_error is not None and report and report.verdicts:
        # 从 verdicts 推断错误类型
        for i, v in enumerate(report.verdicts):
            if v.status == "invalid":
                # 根据证据内容推断具体错误类型
                evidence = v.evidence or ""
                if "常数差异" in evidence or "constant" in evidence.lower():
                    error_type_detected = "constant_diff_boundary"
                elif "数值反例" in evidence or "counterexample" in evidence.lower():
                    error_type_detected = "variable_diff_boundary"
                elif "非法代数" in evidence or "illegal" in evidence.lower():
                    error_type_detected = "illegal_algebra"
                elif "除以零" in evidence or "divide" in evidence.lower():
                    error_type_detected = "divide_by_zero"
                elif "量纲" in evidence or "dimension" in evidence.lower():
                    error_type_detected = "dimension_mismatch"
                elif "归纳" in evidence or "induction" in evidence.lower():
                    error_type_detected = "induction_failure"
                elif "边界" in evidence or "boundary" in evidence.lower():
                    error_type_detected = "boundary_omission"
                elif "符号" in evidence or "symbol" in evidence.lower():
                    error_type_detected = "symbol_typo"
                else:
                    error_type_detected = "invalid_step"
                break

    return BenchmarkResult(
        case=case,
        report=report,
        first_error_step=first_error,
        error_type_detected=error_type_detected,
        passed=passed,
        explanation=report.first_error.explanation if report else "",
    )


# ---------------------------------------------------------------------------
# 运行基准
# ---------------------------------------------------------------------------

def run_benchmark(
    cases: list[BenchmarkCase] | None = None,
    bench_dir: str | Path | None = None,
) -> tuple[list[BenchmarkResult], Metrics]:
    """运行基准套件。

    Args:
        cases: 若提供，直接使用此列表。
        bench_dir: 若提供，从目录加载真值台账。

    Returns:
        (结果列表, 指标)
    """
    if cases is None:
        if bench_dir is None:
            raise ValueError("必须提供 cases 或 bench_dir")
        cases = load_ground_truth(bench_dir)

    results = [run_single(c) for c in cases]
    metrics = compute_metrics(results, cases)

    return results, metrics


def compute_metrics(
    results: list[BenchmarkResult], cases: list[BenchmarkCase]
) -> Metrics:
    """计算基准指标。"""
    total = len(results)
    clean_results = [r for r, c in zip(results, cases) if c.expect["is_clean"]]
    dirty_results = [r for r, c in zip(results, cases) if not c.expect["is_clean"]]

    # 误报率：干净解答被判为错（K4: 0 优先）
    false_positives = sum(1 for r in clean_results if r.first_error_step is not None)
    false_positive_rate = (
        false_positives / len(clean_results) if clean_results else 0.0
    )

    # 错误定位准确率
    correct_loc = sum(
        1
        for r, c in zip(results, cases)
        if not c.expect["is_clean"]
        and r.first_error_step == c.expect["first_error_step"]
    )
    localization_accuracy = (
        correct_loc / len(dirty_results) if dirty_results else 0.0
    )

    # 覆盖度
    coverage = compute_coverage(cases)

    return Metrics(
        false_positive_rate=false_positive_rate,
        localization_accuracy=localization_accuracy,
        total_cases=total,
        clean_cases=len(clean_results),
        dirty_cases=len(dirty_results),
        coverage=coverage,
    )


def compute_coverage(cases: list[BenchmarkCase]) -> dict[str, Any]:
    """按错误类型计算覆盖度。

    分母反射自代码常量（GeneratorConfig.min_coverage），不手写。
    """
    from hws_math_auditor.benchmark.generator import GeneratorConfig

    config = GeneratorConfig()
    coverage: dict[str, Any] = {}

    for error_type, min_count in config.min_coverage.items():
        count = sum(
            1
            for c in cases
            if not c.expect["is_clean"] and c.expect["error_type"] == error_type
        )
        coverage[error_type] = {
            "count": count,
            "min_required": min_count,
            "met": count >= min_count,
        }

    # 干净用例覆盖
    clean_count = sum(1 for c in cases if c.expect["is_clean"])
    coverage["clean"] = {
        "count": clean_count,
        "min_required": config.clean_cases,
        "met": clean_count >= config.clean_cases,
    }

    return coverage


# ---------------------------------------------------------------------------
# 探活：坏实现必须暴露
# ---------------------------------------------------------------------------

def probe_broken_implementation() -> bool:
    """探活：故意用坏实现跑基准，必须报未达标。

    坏实现 = 总是返回 ok 的 verifier。
    期望：误报率 > 0 或 定位准确率 < 100%。

    注意：函数名不用 test_ 前缀——它由测试显式调用，
    名字以 test_ 开头会被 pytest 误收集。
    """
    # 临时替换 verify_step 为总是返回 ok
    from hws_math_auditor import verifier

    original_verify = verifier.verify_step

    def broken_verify(prev, curr):
        from hws_math_auditor.model import Verdict

        return Verdict("ok", "broken: always ok", None)

    verifier.verify_step = broken_verify

    try:
        # 生成少量用例
        gen = BenchmarkGenerator()
        cases = gen.generate_all()[:5]
        results, metrics = run_benchmark(cases)

        # 坏实现必须暴露
        exposed = metrics.false_positive_rate > 0 or metrics.localization_accuracy < 1.0
        return exposed
    finally:
        verifier.verify_step = original_verify


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    # 生成并运行
    gen = BenchmarkGenerator()
    cases = gen.generate_all()

    # 覆盖度守门
    missing = gen.check_coverage(cases)
    if missing:
        print(f"⚠ 覆盖度不足: {missing}")
        sys.exit(1)

    print(f"运行 {len(cases)} 条基准用例...")
    results, metrics = run_benchmark(cases)

    print("\n=== 指标 ===")
    print(f"总用例: {metrics.total_cases}")
    print(f"干净: {metrics.clean_cases}, 含错: {metrics.dirty_cases}")
    print(f"误报率: {metrics.false_positive_rate:.2%}")
    print(f"定位准确率: {metrics.localization_accuracy:.2%}")

    print("\n=== 覆盖度 ===")
    for et, info in metrics.coverage.items():
        status = "✅" if info["met"] else "❌"
        print(f"  {status} {et}: {info['count']}/{info['min_required']}")

    print("\n=== 逐条结果 ===")
    failed = []
    for r in results:
        status = "✅" if r.passed else "❌"
        print(
            f"  {status} {r.case.id}: "
            f"expect={'clean' if r.case.expect['is_clean'] else r.case.expect['error_type']}, "
            f"observed={'clean' if r.first_error_step is None else f'step {r.first_error_step+1}'}, "
            f"passed={r.passed}"
        )
        if not r.passed:
            failed.append(r.case.id)

    # 与 CLI 同一判定：这条入口也不是"跑完就 0"（D1 的同一缺陷）
    if failed:
        print(f"\n❌ 基准未达标：{len(failed)} 条未通过 → {', '.join(failed)}")
        sys.exit(1)
    if metrics.false_positive_rate > 0 or metrics.localization_accuracy < 1.0:
        print(
            f"\n❌ 基准未达标：误报率 {metrics.false_positive_rate:.2%} / "
            f"定位准确率 {metrics.localization_accuracy:.2%}"
        )
        sys.exit(1)

    print(f"\n✅ 基准达标：{metrics.total_cases} 条全部通过")
    sys.exit(0)
