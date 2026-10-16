"""模块②：步骤级符号验证。"""

from typing import List, Optional

from sympy import simplify, Symbol

from hws_math_auditor.model import Step, Verdict


def verify_step(prev_expr, curr_expr) -> Verdict:
    """验证相邻步骤的等价性。

    返回三级语义（K1）：
    - ok: 符号等价
    - invalid: 确证错误，附最小反例
    - unverifiable: 引擎能力外
    """
    # 1. 检查是否可符号化
    if prev_expr is None or curr_expr is None:
        return Verdict("unverifiable", "不可符号化步骤", None)

    # 2. 尝试符号等价性
    try:
        diff = simplify(curr_expr - prev_expr)
        if diff == 0:
            return Verdict("ok", "符号等价", None)
        # 若 diff 为非零常数，直接判定为 invalid（无需反例）
        if diff.is_number and diff != 0:
            return Verdict("invalid", "常数差异", {"diff": float(diff)})
    except Exception:
        pass

    # 3. 尝试数值反例
    free_vars = list(prev_expr.free_symbols | curr_expr.free_symbols)
    if free_vars:
        counterexample = find_counterexample(prev_expr, curr_expr, free_vars)
        if counterexample:
            return Verdict("invalid", "数值反例", counterexample)

    # 4. 无法判定
    return Verdict("unverifiable", "符号与数值均无法判定", None)


def find_counterexample(
    prev_expr, curr_expr, free_vars: List[Symbol]
) -> Optional[dict]:
    """构造最小反例。

    自由变量取 {-3, -2, -1, 0, 1, 2, 3} 的笛卡尔积。
    """
    import itertools

    values_range = range(-3, 4)
    for values_tuple in itertools.product(values_range, repeat=len(free_vars)):
        subs = dict(zip(free_vars, values_tuple))
        try:
            prev_val = prev_expr.subs(subs).evalf()
            curr_val = curr_expr.subs(subs).evalf()
            if abs(float(prev_val) - float(curr_val)) > 1e-9:
                return {str(v): int(subs[v]) for v in free_vars}
        except (TypeError, ZeroDivisionError, ValueError):
            continue

    return None


def verify_all(steps: List[Step]) -> List[Verdict]:
    """验证所有相邻步骤。"""
    verdicts = []
    for i in range(len(steps)):
        if i == 0:
            # 第一步：检查自身是否可符号化
            if steps[i].expr is not None:
                verdicts.append(Verdict("ok", "第一步可符号化", None))
            else:
                verdicts.append(Verdict("unverifiable", "第一步不可符号化", None))
        else:
            prev = steps[i - 1].expr
            curr = steps[i].expr
            verdicts.append(verify_step(prev, curr))

    return verdicts
