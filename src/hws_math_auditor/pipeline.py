"""编排层：审计 / 基准 / 自检。

CLI 与 GUI 共用同一编排层，零判定逻辑复现。
"""

from dataclasses import dataclass
from typing import Optional

from hws_math_auditor.config import config
from hws_math_auditor.model import AuditReport, FirstErrorResult, Step, Verdict
from hws_math_auditor.parser import extract_reasoning, split_steps
from hws_math_auditor.parser.normalizer import normalize_step_expr, compute_coverage
from hws_math_auditor.verifier import verify_all
from hws_math_auditor.locator import locate_first_error
from hws_math_auditor.recalc import independent_recalc


@dataclass
class AuditRequest:
    """审计请求。"""

    solution_text: str
    final_assertion: str = ""
    enable_model: bool = False


@dataclass
class AuditResult:
    """审计结果。"""

    report: AuditReport
    exit_code: int  # 0=成功, 1=检出错误, 2=输入不可用


def audit(request: AuditRequest) -> AuditResult:
    """端到端审计。"""
    # 1. 输入检查
    if not request.solution_text or not request.solution_text.strip():
        return AuditResult(report=None, exit_code=2)

    # 2. 步骤切分
    reasoning, _ = extract_reasoning(request.solution_text)
    steps = split_steps(reasoning or request.solution_text)

    if not steps:
        return AuditResult(report=None, exit_code=2)

    # 3. 归一化
    for step in steps:
        normalize_step_expr(step)

    # 4. 符号验证
    verdicts = verify_all(steps)

    # 5. 首错锚定
    first_error = locate_first_error(verdicts, steps)

    # 6. 独立重算
    recalc_result = independent_recalc(
        request.final_assertion, steps
    )

    # 7. 覆盖率
    coverage = compute_coverage(steps)

    report = AuditReport(
        steps=steps,
        verdicts=verdicts,
        first_error=first_error,
        recalc_result=recalc_result,
        coverage=coverage,
    )

    # 退出码：检出错误 → 1
    exit_code = 1 if first_error.first_error is not None else 0

    return AuditResult(report=report, exit_code=exit_code)


def selftest() -> bool:
    """冻结态自检。"""
    # 占位：实际实现会检查内嵌数据定位
    return True
