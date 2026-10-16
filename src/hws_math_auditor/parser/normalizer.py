"""步骤归一化：将自然语言/LaTeX 表达式转为 SymPy 可计算形式。"""

import re
from typing import List, Optional, Tuple

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
    # 函数名后上标（sin²θ -> sin(θ)**2, cos²φ -> cos(φ)**2）
    (r"(sin|cos|tan|cot|sec|csc)\u00b2([\u03b1-\u03c9\u0391-\u03a9a-zA-Z])", r"\1(\2)**2"),
    # 函数名后上标带括号（sin²(θ) -> sin(θ)**2）
    (r"(sin|cos|tan|cot|sec|csc)\u00b2\(", r"\1("),
    # Unicode 上标（必须在函数名上标之后，否则 sin²θ -> sin**2θ）
    (r"\u00b2", "**2"),
    (r"\u00b3", "**3"),
    (r"\u221a", "sqrt"),
    # 数字后跟字母（5x -> 5*x）
    (r"(\d)([a-zA-Z\u03b1-\u03c9\u0391-\u03a9])", r"\1*\2"),
    # 括号前数字（2(x) -> 2*(x)）
    (r"(\d)\((\w)", r"\1*(\2"),
    # 括号后括号（(x)(y) -> (x)*(y)）
    (r"\)\(", r")*("),
]


def latex_to_symbolic(text: str) -> str:
    """LaTeX 到符号表达式的简单转换。"""
    result = text
    for pattern, replacement in LATEX_REPLACEMENTS:
        result = re.sub(pattern, replacement, result)
    return result


def strip_chinese_prefix(text: str) -> str:
    """剥离中文前缀，保留数学表达式部分。

    如 "解方程 x\u00b2 - 5x + 6 = 0" -> "x**2 - 5*x + 6 = 0"
    """
    patterns = [
        r"^步骤\d+[.、)）:：]\s*",
        r"^解方程\s*",
        r"^因式分解\s*",
        r"^所以\s*",
        r"^故\s*",
        r"^即\s*",
        r"^求\s*",
        r"^证明\s*",
        r"^由\s*",
        r"^得\s*",
        r"^整理得\s*",
        r"^解得\s*",
    ]
    result = text
    for p in patterns:
        result = re.sub(p, "", result)
    return result


def parse_equation_to_expr(text: str) -> str:
    """将方程转为可比较的表达式。

    如 "x**2 - 5*x + 6 = 0" -> "x**2 - 5*x + 6"
    如 "(x-2)*(x-3) = 0" -> "(x-2)*(x-3)"
    如 "a + b = 2*sqrt(a*b)" -> "a + b - 2*sqrt(a*b)"
    如 "x = 2 或 x = 3" -> "(x - 2)*(x - 3)"（多解取乘积）
    """
    if "=" not in text:
        return text

    # 检查是否为 "x = A 或 x = B" 格式
    or_pattern = r"([a-zA-Z\u03b1-\u03c9\u0391-\u03a9])\s*=\s*([-+]?\d*\.?\d+)\s*\u6216\s*\1\s*=\s*([-+]?\d*\.?\d+)"
    match = re.search(or_pattern, text)
    if match:
        var = match.group(1)
        val1 = match.group(2)
        val2 = match.group(3)
        return f"({var} - {val1})*({var} - {val2})"

    parts = text.split("=")
    if len(parts) > 2:
        # 链式等号：左边是第一个部分，右边是最后一个部分
        # 但需检查中间部分是否包含 "或"
        middle = "=".join(parts[1:-1])
        if "\u6216" in middle or "or" in middle.lower():
            # 多解格式：取第一个等号
            left = parts[0].strip()
            right = parts[1].strip()
            return f"({left}) - ({right})"
        left = parts[0].strip()
        right = parts[-1].strip()
        return f"({left}) - ({right})"

    left = parts[0].strip()
    right = parts[1].strip()

    if right == "0":
        return left

    return f"({left}) - ({right})"


def normalize_step_expr(step: Step) -> Tuple[Step, Optional[str]]:
    """归一化步骤表达式。

    返回: (step, error_reason)
    成功时 error_reason 为 None
    """
    raw = step.raw_text

    # 剥离中文前缀
    raw = strip_chinese_prefix(raw)

    # 方程转表达式
    raw = parse_equation_to_expr(raw)

    # 1. LaTeX 提取与转换
    try:
        symbolic = latex_to_symbolic(raw)
    except Exception:
        step.status = "unsymbolizable"
        step.reason = "unparseable_latex"
        return step, "unparseable_latex"

    # 2. SymPy sympify
    try:
        expr = sympify(symbolic, evaluate=True)
        # 检查是否意外产出 tuple（如中文逗号被解析）
        if isinstance(expr, tuple):
            step.status = "unsymbolizable"
            step.reason = "tuple_result_from_chinese_text"
            return step, "sympify_error"
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
