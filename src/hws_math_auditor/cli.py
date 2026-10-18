"""CLI 命令集。"""

import argparse
import json
import sys
from pathlib import Path

from hws_math_auditor.config import config
from hws_math_auditor.model import AuditReport
from hws_math_auditor.pipeline import AuditRequest, audit, selftest


def _ensure_utf8_stdio():
    """编码守卫：确保 stdio 可打印中文。"""
    import sys
    import io

    if sys.stdout.encoding != "utf-8":
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace"
        )
    if sys.stderr.encoding != "utf-8":
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer, encoding="utf-8", errors="replace"
        )


def cmd_audit(args):
    """审计单个解答。"""
    _ensure_utf8_stdio()

    # 读取输入
    encoding = args.encoding or "utf-8"
    try:
        with open(args.input, "r", encoding=encoding) as f:
            solution_text = f.read()
    except UnicodeDecodeError:
        print(
            f"错误: 文件 {args.input} 非 {encoding} 编码，"
            f"请使用 --encoding 指定正确编码或另存为 UTF-8"
        )
        return 2
    except FileNotFoundError:
        print(f"错误: 文件 {args.input} 不存在")
        return 2
    except LookupError:
        print(f"错误: 未知编码 '{encoding}'，请使用标准编码名（如 utf-8, gbk, gb2312）")
        return 2

    # 执行审计
    request = AuditRequest(
        solution_text=solution_text,
        final_assertion=args.assertion or "",
        enable_model=args.model,
    )
    result = audit(request)

    # 输出结果
    if args.format == "json":
        output = {
            # 对外 1 基（内部 locator 是 0 基）
            "first_error": (
                None if result.report.first_error.first_error is None
                else result.report.first_error.first_error + 1
            ),
            "contaminated": result.report.first_error.contaminated,
            "independent_failures": result.report.first_error.independent_failures,
            "explanation": result.report.first_error.explanation,
            "recalc_result": result.report.recalc_result,
            "coverage": result.report.coverage,
            "verdicts": [
                {
                    "step": v.step_no,
                    "status": v.status,
                    "evidence": v.evidence,
                    "counterexample": v.counterexample,
                }
                for v in result.report.verdicts
            ],
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        # 人读格式
        print("=" * 60)
        print("审计报告")
        print("=" * 60)
        _fe = result.report.first_error.first_error
        print(f"首错步骤: {_fe + 1 if _fe is not None else '无（未检出错误）'}")
        print(f"解释: {result.report.first_error.explanation}")
        print(f"独立重算: {result.report.recalc_result}")
        print(f"覆盖率: {result.report.coverage.get('coverage', 0):.1%}")
        print("-" * 60)
        for i, (step, verdict) in enumerate(
            zip(result.report.steps, result.report.verdicts)
        ):
            print(f"步骤 {step.step_no}: {verdict.status}")
            print(f"  证据: {verdict.evidence}")
            if verdict.counterexample:
                print(f"  反例: {verdict.counterexample}")

    # 报告导出（plan/05 §1.2 承诺：Markdown + JSON + HTML）
    if args.report:
        from hws_math_auditor.report import write_report

        stem = Path(args.report)
        formats = [f.strip().lower() for f in args.report_formats.split(",") if f.strip()]
        written = []
        for fmt in formats:
            try:
                written.append(write_report(result.report, stem, fmt))
            except ValueError as exc:
                print(f"错误: {exc}")
                return 2
        for path in written:
            print(f"✅ 报告已导出: {path}")

    return result.exit_code


def _resolve_data_dir() -> Path:
    """解析随包数据目录。

    源码态 = <root>/data；冻结态 = sys._MEIPASS/data。
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "data"
    # cli.py = <root>/src/hws_math_auditor/cli.py → parents[2] = <root>
    return Path(__file__).parents[2] / "data"


class FrozenLedgerError(Exception):
    """冻结台账与生成器不一致。"""

    def __init__(self, problems):
        self.problems = problems
        super().__init__("; ".join(problems))


def _load_frozen_cases():
    """加载冻结真值台账，并先做"再生成位级一致"守门。

    基准消费的是**冻结台账**（禁手改），不是当场生成的内存对象——
    否则"台账被手改 / 生成器漂移"永远不红（K3）。
    """
    from hws_math_auditor.benchmark.generator import check_frozen_ledger
    from hws_math_auditor.benchmark.runner import load_ground_truth

    bench_dir = _resolve_data_dir() / "benchmarks"
    problems = check_frozen_ledger(bench_dir)
    if problems:
        raise FrozenLedgerError(problems)
    return load_ground_truth(bench_dir)


def cmd_benchmark(args):
    """运行基准。"""
    _ensure_utf8_stdio()

    from hws_math_auditor.benchmark.generator import BenchmarkGenerator
    from hws_math_auditor.benchmark.runner import run_benchmark

    if not (args.run or args.metrics):
        print("用法: hws-audit benchmark (--run | --metrics)")
        return 2

    try:
        cases = _load_frozen_cases()
    except FrozenLedgerError as e:
        print("❌ 冻结台账与生成器不一致（禁手改台账）:")
        for p in e.problems:
            print(f"  - {p}")
        return 1
    except FileNotFoundError as e:
        print(f"❌ 基准数据不可用: {e}")
        return 2

    # 覆盖度守门（分母反射自代码常量，K9）
    gen = BenchmarkGenerator()
    missing = gen.check_coverage(cases)
    if missing:
        print(f"⚠ 覆盖度不足: {missing}")
        return 1

    if args.metrics:
        _, metrics = run_benchmark(cases)
        print(json.dumps(metrics.to_dict(), ensure_ascii=False, indent=2))
        return 0

    print(f"运行 {len(cases)} 条基准用例...")
    results, metrics = run_benchmark(cases)

    print(f"\n=== 指标 ===")
    print(f"总用例: {metrics.total_cases}")
    print(f"干净: {metrics.clean_cases}, 含错: {metrics.dirty_cases}")
    print(f"误报率: {metrics.false_positive_rate:.2%}")
    print(f"定位准确率: {metrics.localization_accuracy:.2%}")

    print(f"\n=== 覆盖度 ===")
    for et, info in metrics.coverage.items():
        status = "✅" if info["met"] else "❌"
        print(f"  {status} {et}: {info['count']}/{info['min_required']}")

    print(f"\n=== 逐条结果 ===")
    for r in results:
        status = "✅" if r.passed else "❌"
        print(
            f"  {status} {r.case.id}: "
            f"expect={'clean' if r.case.expect['is_clean'] else r.case.expect['error_type']}, "
            f"observed={'clean' if r.first_error_step is None else f'step {r.first_error_step+1}'}, "
            f"passed={r.passed}"
        )

    return 0


def cmd_selftest(args):
    """冻结态自检。"""
    _ensure_utf8_stdio()
    if selftest():
        print("自检通过")
        return 0
    else:
        print("自检失败")
        return 1


def main():
    """CLI 入口。"""
    parser = argparse.ArgumentParser(
        prog="hws-audit",
        description="难题解答步骤级审计与错误定位器",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # audit 子命令
    p_audit = subparsers.add_parser("audit", help="审计单个解答")
    p_audit.add_argument("--input", required=True, help="解答文件路径")
    p_audit.add_argument("--assertion", help="最终断言（如 'x = 5'）")
    p_audit.add_argument(
        "--format", choices=["text", "json"], default="text", help="输出格式"
    )
    p_audit.add_argument("--model", action="store_true", help="启用模型（默认关）")
    p_audit.add_argument(
        "--report",
        nargs="?",
        const="report",
        default=None,
        metavar="PATH",
        help="导出报告（可给路径；扩展名决定格式 .md/.json/.html；不带值则写 report.<fmt>）",
    )
    p_audit.add_argument(
        "--report-formats",
        default="md,json,html",
        help="--report 要导出的格式，逗号分隔（默认三种都出）",
    )
    p_audit.add_argument(
        "--encoding",
        default="utf-8",
        help="文件编码（默认 utf-8，非 UTF-8 文件需显式指定）",
    )
    p_audit.set_defaults(func=cmd_audit)

    # benchmark 子命令
    p_bench = subparsers.add_parser("benchmark", help="运行基准")
    p_bench.add_argument("--run", action="store_true", help="运行基准")
    p_bench.add_argument("--metrics", action="store_true", help="输出指标")
    p_bench.set_defaults(func=cmd_benchmark)

    # selftest 子命令
    p_selftest = subparsers.add_parser("selftest", help="冻结态自检")
    p_selftest.set_defaults(func=cmd_selftest)

    args = parser.parse_args()
    sys.exit(args.func(args))
