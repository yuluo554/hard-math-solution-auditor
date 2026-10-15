"""CLI 命令集。"""

import argparse
import json
import sys

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
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            solution_text = f.read()
    except UnicodeDecodeError:
        print(f"错误: 文件 {args.input} 非 UTF-8 编码，请另存为 UTF-8")
        return 2
    except FileNotFoundError:
        print(f"错误: 文件 {args.input} 不存在")
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
            "first_error": result.report.first_error.first_error,
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
        print(f"首错步骤: {result.report.first_error.first_error}")
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

    return result.exit_code


def cmd_benchmark(args):
    """运行基准。"""
    _ensure_utf8_stdio()
    print("基准运行（占位）")
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
