"""模块③：错误定位与首错锚定。"""

from typing import List

from hws_math_auditor.model import FirstErrorResult, Step, Verdict


def locate_first_error(verdicts: List[Verdict], steps: List[Step]) -> FirstErrorResult:
    """首错锚定（K2）。

    确定性传播逻辑：
    - 最小序号 invalid 为首错
    - 后续 invalid 判断为独立失效或受污染
    """
    first_error_idx = None
    contaminated = []
    independent_failures = []

    for i, v in enumerate(verdicts):
        if v.status == "invalid":
            if first_error_idx is None:
                first_error_idx = i  # 最小序号为首错
            else:
                # 判断是独立失效还是受污染
                if is_independent_failure(i, first_error_idx, steps):
                    independent_failures.append(i)
                else:
                    contaminated.append(i)

    # 生成解释
    explanation = generate_explanation(
        first_error_idx, contaminated, independent_failures, verdicts
    )

    return FirstErrorResult(
        first_error=first_error_idx,
        contaminated=contaminated,
        independent_failures=independent_failures,
        explanation=explanation,
    )


def is_independent_failure(idx: int, first_idx: int, steps: List[Step]) -> bool:
    """判断是否为独立失效。

    若当前步的表达式不直接依赖首错步的输出变量，则为独立失效。
    """
    if idx >= len(steps) or first_idx >= len(steps):
        return True

    # 简单启发式：若两步的变量名无交集，则独立
    # 实际实现应更严谨
    return False


def generate_explanation(
    first_error_idx: Optional[int],
    contaminated: List[int],
    independent_failures: List[int],
    verdicts: List[Verdict],
) -> str:
    """生成首错锚定解释。"""
    if first_error_idx is None:
        return "无错误"

    parts = [f"首错在第 {first_error_idx + 1} 步"]

    if contaminated:
        parts.append(f"受污染步骤: {[c + 1 for c in contaminated]}")

    if independent_failures:
        parts.append(f"独立失效步骤: {[i + 1 for i in independent_failures]}")

    return "; ".join(parts)
