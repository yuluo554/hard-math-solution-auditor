"""步骤归一化：将自然语言/LaTeX 表达式转为 SymPy 可计算形式。"""

import re
from typing import Optional, Tuple

from sympy import sympify, Symbol

from hws_math_auditor.model import Step


# LaTeX 符号替换表
LATEX_REPLACEMENTS = [
    (r"\\alpha", "a"),
    (r"\\beta", "b"),
    (r"\\gamma", "g"),
    (r"\\delta", "d"),
    (r"\\sum", "Sum"),
    (r"\\int", "Integral"),
    (r"\\times", "*"),
    (r"\\cdot", "*"),
    (r"\\div", "/"),
    (r"\\frac\{([^}]+)\}\{([^}]+)\}", r"(\1)/(\2)"),
    (r"\\sqrt\{([^}]+)\}", r"sqrt(\1)"),
    (r"\$\$(.*?)\$\$", r"\1"),
    (r"\$(.*?)\$", r"\1"),
]


def latex_to_symbolic(text: str) -> str:
    """LaTeX 到符号表达式的简单转换。"""
    result = text
    for pattern, replacement in LATEX_REPLACEMENTS:
        result = re.sub(pattern, replacement, result)
    return result


def normalize_step_expr(step: Step) -> Tuple[Step, Optional[str]]:
    """归一化步骤表达式。

    返回: (step, error_reason)
    成功时 error_reason 为 None
    """
    raw = step.raw_text

    # 1. LaTeX 提取与转换
    try:
        symbolic = latex_to_symbolic(raw)
    except Exception:
        step.status = "unsymbolizable"
        step.reason = "unparseable_latex"
        return step, "unparseable_latex"

    # 2. SymPy sympify
    try:
        expr = sympify(symbolic, evaluate=False)
        step.expr = expr
        step.status = "normalized"
        return step, None
    except (SyntaxError, ValueError) as e:
        step.status = "unsymbolizable"
        step.reason = f"sympify_error: {e}"
        return step, "sympify_error"


def compute_coverage(steps: List[Step]) -> dict:
    """计算归一化覆盖率。

    分母 = 检出步骤数，分子 = 成功归一化数。
    """
    total = len(steps)
    normalized = sum(1 for s in steps if s.status == "normalized")
    unsymbolizable = sum(1 for s in steps if s.status == "unsymbolizable")

    # 不可符号化原因分布
    reasons = {}
    for s in steps:
        if s.status == "unsymbolizable" and s.reason:
            reasons[s.reason] = reasons.get(s.reason, 0) + 1

    return {
        "total_steps": total,
        "normalized": normalized,
        "unsymbolizable": unsymbolizable,
        "coverage": normalized / total if total > 0 else 0,
        "reasons": reasons,
    }
