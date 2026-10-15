"""模块④：独立重算路径。

K8: 数值口径唯一定义点。
"""

from typing import Optional

from sympy import N

from hws_math_auditor.model import Step


# K8: 全项目唯一数值口径（plan/02 唯一定义点）
TOLERANCE = 1e-9


def numeric_evaluate(expr) -> float:
    """独立数值计算。

    与符号路径实现独立，防"同源错误互相印证"。
    """
    if expr is None:
        raise ValueError("表达式为 None")

    try:
        return float(N(expr))
    except Exception:
        # 尝试逐变量代入
        return float(expr.evalf())


def independent_recalc(final_assertion: str, steps: list[Step]) -> str:
    """独立数值重算。

    返回: 一致 / 不一致 / 无法独立重算
    """
    # 1. 从归一化步骤中提取最终断言
    # 简化实现：取最后一步的表达式
    computed = None
    for step in steps:
        if step.expr is None:
            return "无法独立重算"
        try:
            computed = numeric_evaluate(step.expr)
        except Exception:
            return "无法独立重算"

    # 2. 解析最终断言
    target_value = parse_assertion_value(final_assertion)
    if target_value is None:
        return "无法独立重算"

    # 3. 比对
    if abs(computed - target_value) < TOLERANCE:
        return "一致"
    else:
        return "不一致"


def parse_assertion_value(assertion: str) -> Optional[float]:
    """解析最终断言的数值。

    如 "x = 5" → 5.0
    """
    import re

    # 尝试提取等号右侧的数值
    match = re.search(r"=\s*([-+]?\d*\.?\d+)", assertion)
    if match:
        return float(match.group(1))

    # 尝试直接解析
    try:
        return float(assertion)
    except ValueError:
        return None
