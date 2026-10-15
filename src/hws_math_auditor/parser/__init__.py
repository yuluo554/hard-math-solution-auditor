"""模块①：解答摄入与步骤切分。"""

import re
from typing import List, Optional, Tuple

from hws_math_auditor.model import Step


# 思维链标签
REASONING_START = "\u003c\u0069\u006d\u0065\u003e"
REASONING_END = "\u003c/\u0069\u006d\u0065\u003e"

# 步骤编号正则
STEP_PATTERN = re.compile(r"^\s*(\d+)[.、)）]\s+", re.MULTILINE)

# 思维链提取
REASONING_PATTERN = re.compile(
    f"{re.escape(REASONING_START)}(.*?){re.escape(REASONING_END)}",
    re.DOTALL,
)


def extract_reasoning(text: str) -> Tuple[str, str]:
    """提取 \u003c\u0069\u006d\u0065\u003e 思维链段。

    返回: (reasoning_text, outside_text)
    """
    match = REASONING_PATTERN.search(text)
    if match:
        reasoning = match.group(1)
        outside = text[: match.start()] + text[match.end() :]
        return reasoning, outside
    return text, ""


def split_steps(text: str) -> List[Step]:
    """步骤切分（确定性，零模型）。

    切分策略：
    1. 优先按显式编号切分
    2. 其次按空行+新段落切分
    3. 每步记录源行号
    """
    lines = text.split("\n")
    steps = []
    current_no = 1
    current_start = 0
    current_lines = []

    for i, line in enumerate(lines):
        # 检测新步骤开始（非首行且匹配编号）
        if i > 0 and STEP_PATTERN.match(line):
            if current_lines:
                step_text = "\n".join(current_lines).strip()
                if step_text:
                    steps.append(
                        Step(
                            step_no=current_no,
                            raw_text=step_text,
                            source_line_start=current_start + 1,
                            source_line_end=i,
                        )
                    )
                    current_no += 1
                current_lines = []
            current_start = i

        current_lines.append(line)

    # 最后一步
    if current_lines:
        step_text = "\n".join(current_lines).strip()
        if step_text:
            steps.append(
                Step(
                    step_no=current_no,
                    raw_text=step_text,
                    source_line_start=current_start + 1,
                    source_line_end=len(lines),
                )
            )

    return steps


def normalize_step(step: Step) -> Step:
    """步骤归一化（占位，由 normalizer 模块实现）。"""
    # 占位：实际实现在 normalizer.py
    step.status = "normalized"
    return step
