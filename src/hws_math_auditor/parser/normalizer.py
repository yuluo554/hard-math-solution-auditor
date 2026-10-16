"""步骤归一化：将自然语言/LaTeX 表达式转为 SymPy 可计算形式。"""

import re
from typing import List, Optional, Tuple

from sympy import sympify, Symbol

from hws_math_auditor.model import Step


# ---------------------------------------------------------------------------
# 不可符号化原因枚举（K5）
# ---------------------------------------------------------------------------
REASON_UNPARSEABLE_LATEX = "unparseable_latex"
REASON_UNKNOWN_SYMBOL = "unknown_symbol"
REASON_UNSUPPORTED_CONSTRUCT = "unsupported_construct"
REASON_SYMPIFY_ERROR = "sympify_error"
REASON_TUPLE_FROM_CHINESE = "tuple_result_from_chinese_text"


# LaTeX 符号替换表
LATEX_REPLACEMENTS = [
    (r"\\alpha", "a"),
    (r"\\beta", "b"),
    (r"\\gamma", "g"),
    (r"\\delta", "d"),
    (r"\\theta", "t"),
    (r"\\lambda", "l"),
    (r"\\mu", "m"),
    (r"\\pi", "p"),
    (r"\\sigma", "s"),
    (r"\\phi", "f"),
    (r"\\omega", "w"),
    (r"\\sum", "Sum"),
    (r"\\int", "Integral"),
    (r"\\lim", "Limit"),
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
    (r"\u2074", "**4"),
    (r"\u2075", "**5"),
    (r"\u2076", "**6"),
    (r"\u2077", "**7"),
    (r"\u2078", "**8"),
    (r"\u2079", "**9"),
    (r"\u2070", "**0"),
    (r"\u221a", "sqrt"),
    # 数字后跟字母（5x -> 5*x）
    (r"(\d)([a-zA-Z\u03b1-\u03c9\u0391-\u03a9])", r"\1*\2"),
    # 括号前数字（2(x) -> 2*(x)）
    (r"(\d)\((\w)", r"\1*(\2"),
    # 括号后括号（(x)(y) -> (x)*(y)）
    (r"\)\(", r")*("),
]


# LaTeX 环境替换：将 \begin{env}...\end{env} 提取内容
LATEX_ENV_PATTERNS = [
    # 提取 align 环境中的内容
    (r"\\begin\{align\*?\}(.*?)\\end\{align\*?\}", r"\1"),
    # 提取 equation 环境
    (r"\\begin\{equation\*?\}(.*?)\\end\{equation\*?\}", r"\1"),
    # 提取 gather 环境
    (r"\\begin\{gather\*?\}(.*?)\\end\{gather\*?\}", r"\1"),
    # 提取 matrix 系列环境
    (r"\\begin\{matrix\*?\}(.*?)\\end\{matrix\*?\}", r"\1"),
    (r"\\begin\{pmatrix\*?\}(.*?)\\end\{pmatrix\*?\}", r"(\1)"),
    (r"\\begin\{bmatrix\*?\}(.*?)\\end\{bmatrix\*?\}", r"[\1]"),
    # 提取 case 环境
    (r"\\begin\{cases\}(.*?)\\end\{cases\}", r"\1"),
]


# 中文前缀剥离模式（扩展版）
CHINESE_PREFIX_PATTERNS = [
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
    r"^化简\s*",
    r"^计算\s*",
    r"^验证\s*",
    r"^令\s*",
    r"^设\s*",
    r"^代入\s*",
    r"^展开\s*",
    r"^合并\s*",
    r"^移项\s*",
    r"^两边\s*",
    r"^取对数\s*",
    r"^取指数\s*",
    r"^通分\s*",
    r"^去分母\s*",
    r"^配方\s*",
    r"^判别式\s*",
]


def latex_to_symbolic(text: str) -> str:
    """LaTeX 到符号表达式的转换。"""
    result = text
    for pattern, replacement in LATEX_REPLACEMENTS:
        result = re.sub(pattern, replacement, result)
    return result


def extract_latex_environments(text: str) -> str:
    """提取 LaTeX 环境内容，移除环境标记。

    将 \\begin{align}...\\end{align} 替换为内部内容。
    """
    result = text
    for pattern, replacement in LATEX_ENV_PATTERNS:
        result = re.sub(pattern, replacement, result, flags=re.DOTALL)
    return result


def strip_chinese_prefix(text: str) -> str:
    """剥离中文前缀，保留数学表达式部分。

    如 "解方程 x\u00b2 - 5x + 6 = 0" -> "x**2 - 5*x + 6 = 0"
    """
    result = text
    for p in CHINESE_PREFIX_PATTERNS:
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
    or_pattern = (
        r"([a-zA-Z\u03b1-\u03c9\u0391-\u03a9])\s*=\s*"
        r"([-+]?\d*\.?\d+)\s*\u6216\s*\1\s*=\s*([-+]?\d*\.?\d+)"
    )
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


def _classify_sympify_error(error_msg: str) -> str:
    """根据 sympify 错误信息分类不可符号化原因。"""
    msg = str(error_msg).lower()

    if "could not parse" in msg:
        # 检查是否包含未知符号
        if "\\" in msg:
            return REASON_UNPARSEABLE_LATEX
        return REASON_SYMPIFY_ERROR

    if "unrecognized" in msg or "unknown" in msg:
        return REASON_UNKNOWN_SYMBOL

    if "not supported" in msg or "unsupported" in msg:
        return REASON_UNSUPPORTED_CONSTRUCT

    return REASON_SYMPIFY_ERROR


def normalize_step_expr(step: Step) -> Tuple[Step, Optional[str]]:
    """归一化步骤表达式。

    返回: (step, error_reason)
    成功时 error_reason 为 None
    """
    raw = step.raw_text

    # 剥离中文前缀
    raw = strip_chinese_prefix(raw)

    # 提取 LaTeX 环境内容
    raw = extract_latex_environments(raw)

    # 方程转表达式
    raw = parse_equation_to_expr(raw)

    # 1. LaTeX 提取与转换
    try:
        symbolic = latex_to_symbolic(raw)
    except Exception:
        step.status = "unsymbolizable"
        step.reason = REASON_UNPARSEABLE_LATEX
        return step, REASON_UNPARSEABLE_LATEX

    # 2. SymPy sympify
    try:
        expr = sympify(symbolic, evaluate=True)
        # 检查是否意外产出 tuple（如中文逗号被解析）
        if isinstance(expr, tuple):
            step.status = "unsymbolizable"
            step.reason = REASON_TUPLE_FROM_CHINESE
            return step, REASON_SYMPIFY_ERROR
        step.expr = expr
        step.status = "normalized"
        return step, None
    except (SyntaxError, ValueError) as e:
        step.status = "unsymbolizable"
        step.reason = _classify_sympify_error(str(e))
        return step, step.reason


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
            # 标准化原因名称
            reason = s.reason
            if reason.startswith("sympify_error:"):
                reason = REASON_SYMPIFY_ERROR
            reasons[reason] = reasons.get(reason, 0) + 1

    return {
        "total_steps": total,
        "normalized": normalized,
        "unsymbolizable": unsymbolizable,
        "coverage": normalized / total if total > 0 else 0,
        "reasons": reasons,
    }
