"""模块①：解答摄入与步骤切分。"""

import re
from typing import List, Optional, Tuple

from hws_math_auditor.model import Step


# 思维链标签
REASONING_START = "\u003c\u0069\u006d\u0065\u003e"
REASONING_END = "\u003c/\u0069\u006d\u0065\u003e"

# 步骤编号正则：匹配 1. / 1、 / 1) / 1） / 步骤1: / 步骤1、 / ① / ② / ③ 等格式
# 阿拉伯数字编号
STEP_PATTERN_ARABIC = re.compile(
    r"^\s*(?:步骤)?(\d+)[.、)）:：]\s+", re.MULTILINE
)
# 圆圈数字编号（①②③④⑤⑥⑦⑧⑨⑩）
CIRCLE_NUMBERS = "①②③④⑤⑥⑦⑧⑨⑩"
STEP_PATTERN_CIRCLE = re.compile(
    rf"^\s*([{re.escape(CIRCLE_NUMBERS)}])\s+", re.MULTILINE
)
# 合并：优先阿拉伯数字，其次圆圈数字
STEP_PATTERN = re.compile(
    r"^\s*(?:步骤)?(\d+)[.、)）:：]\s+|^\s*([" + re.escape(CIRCLE_NUMBERS) + r"])\s+",
    re.MULTILINE,
)

# 思维链提取
REASONING_PATTERN = re.compile(
    f"{re.escape(REASONING_START)}(.*?){re.escape(REASONING_END)}",
    re.DOTALL,
)

# 步骤数异常阈值
MIN_STEPS_WARNING = 2
MAX_STEPS_WARNING = 20


def _circle_to_arabic(circle: str) -> int:
    """圆圈数字转阿拉伯数字。"""
    try:
        return CIRCLE_NUMBERS.index(circle) + 1
    except ValueError:
        return 0


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
    1. 优先按显式编号切分（阿拉伯数字 1. / 圆圈数字 ①）
    2. 其次按空行+新段落切分（无编号段落）
    3. 每步记录源行号
    4. 步骤数异常检测（<2 或 >20 时标记 warning）
    """
    lines = text.split("\n")
    steps = []
    current_no = 1
    current_start = 0
    current_lines = []

    for i, line in enumerate(lines):
        # 检测新步骤开始（非首行且匹配编号）
        if i > 0:
            arabic_match = STEP_PATTERN_ARABIC.match(line)
            circle_match = STEP_PATTERN_CIRCLE.match(line)

            if arabic_match or circle_match:
                # 保存前一步
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

    # 步骤数异常检测：若步骤数 < 2 或 > 20，尝试按空行段落切分
    if len(steps) < MIN_STEPS_WARNING or len(steps) > MAX_STEPS_WARNING:
        steps = _split_by_paragraph(text, steps)

    return steps


def _split_by_paragraph(text: str, existing_steps: List[Step]) -> List[Step]:
    """按空行+新段落切分（无编号段落处理）。

    当显式编号切分得到的步骤数异常时，尝试按空行段落切分。
    若已有步骤，则合并处理。
    """
    if existing_steps and len(existing_steps) >= MIN_STEPS_WARNING:
        # 已有足够步骤，不进行段落切分
        return existing_steps

    # 按空行切分段落
    paragraphs = re.split(r"\n\s*\n", text.strip())
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    if len(paragraphs) < MIN_STEPS_WARNING:
        # 段落数仍不足，返回原步骤或单一步骤
        if existing_steps:
            return existing_steps
        if paragraphs:
            return [
                Step(
                    step_no=1,
                    raw_text=paragraphs[0],
                    source_line_start=1,
                    source_line_end=text.count("\n") + 1,
                )
            ]
        return []

    # 按段落创建步骤
    steps = []
    line_offset = 0
    for i, para in enumerate(paragraphs):
        para_lines = para.count("\n") + 1
        steps.append(
            Step(
                step_no=i + 1,
                raw_text=para,
                source_line_start=line_offset + 1,
                source_line_end=line_offset + para_lines,
            )
        )
        line_offset += para_lines + 1  # +1 for the blank line

    return steps


def normalize_step(step: Step) -> Step:
    """步骤归一化（调用 normalizer 模块）。"""
    from hws_math_auditor.parser.normalizer import normalize_step_expr

    step, _ = normalize_step_expr(step)
    return step
