"""步骤模型：Step / Verdict / FirstErrorResult。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Step:
    """单个解题步骤。"""

    step_no: int
    raw_text: str
    source_line_start: int
    source_line_end: int
    reasoning_tag: Optional[str] = None  # \u003c\u0069\u006d\u0065\u003e 标签
    expr: Any = None  # SymPy 表达式或 None
    status: str = "pending"  # pending | normalized | unsymbolizable
    reason: Optional[str] = None  # 归一化失败原因


@dataclass
class Verdict:
    """三级判定语义（K1）。"""

    status: str  # ok | invalid | unverifiable
    evidence: str
    counterexample: Optional[dict] = None

    def __post_init__(self):
        if self.status not in ("ok", "invalid", "unverifiable"):
            raise ValueError(f"非法 verdict 状态: {self.status}")


@dataclass
class FirstErrorResult:
    """首错锚定结果。"""

    first_error: Optional[int]
    contaminated: list[int] = field(default_factory=list)
    independent_failures: list[int] = field(default_factory=list)
    explanation: str = ""


@dataclass
class AuditReport:
    """审计报告。"""

    steps: list[Step]
    verdicts: list[Verdict]
    first_error: FirstErrorResult
    recalc_result: str  # 一致 / 不一致 / 无法独立重算
    coverage: dict  # 覆盖率报告
    judgment_semantics: dict = field(default_factory=dict)  # 判定语义验证结果
    pending_rules: list = field(default_factory=list)  # 待核对规则列表
    unverified_rules: list = field(default_factory=list)  # 未验证规则列表
    # 报告头（阶段三 任务 5）：工具版本与依据（阈值表）版本。
    # 刻意不设「生成时间」—— 报告要「同输入同输出」，两次运行必须逐字节一致。
    tool_version: str = ""
    ruleset_version: str = ""
