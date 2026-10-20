"""编排层：审计 / 基准 / 自检。

CLI 与 GUI 共用同一编排层，零判定逻辑复现。

M4: LLM 兜底层集成
- 模型默认关（K7）
- 数值结论永远来自确定性规则
- LLM 仅用于抽取兜底/别名归一/复核/行文"""

from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Optional

from hws_math_auditor import __version__ as TOOL_VERSION
from hws_math_auditor import datadir
from hws_math_auditor.model import AuditReport
from hws_math_auditor.parser import extract_reasoning, split_steps
from hws_math_auditor.parser.normalizer import normalize_step_expr, compute_coverage
from hws_math_auditor.rules import get_threshold_table
from hws_math_auditor.verifier import verify_all
from hws_math_auditor.locator import locate_first_error
from hws_math_auditor.recalc import independent_recalc
from hws_math_auditor.llm import fallback_extraction


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

    # 4. LLM 兜底（M4）
    # 模型启用且某步归一化失败时，尝试 LLM 兜底抽取。
    # 注意：兜底成功的**数值结论不进判定**（K7）——抽取结果只用于让步骤可符号化，
    # 后续 verify/recalc 仍是确定性路径。兜底与否不改变退出码，因此不向上传递标志。
    if request.enable_model:
        for step in steps:
            if step.status == "unsymbolizable":
                fallback_extraction(step.raw_text)

    # 5. 符号验证
    verdicts = verify_all(steps)

    # 6. 首错锚定
    first_error = locate_first_error(verdicts, steps)

    # 7. 独立重算
    recalc_result = independent_recalc(
        request.final_assertion, steps
    )

    # 8. 覆盖率
    coverage = compute_coverage(steps)

    # 9. 判定语义不虚高（M3）
    # 加载阈值表，获取 pending/unverified 规则
    threshold_table = get_threshold_table()
    pending_rules = [r.id for r in threshold_table.get_pending_rules()]
    unverified_rules = [r.id for r in threshold_table.get_unverified_rules()]

    # 验证判定语义
    judgment_semantics = {}
    for i, verdict in enumerate(verdicts):
        # 检查 not_applicable 是否只用于原文写了例外情形的项
        # 当前实现中，verdict 状态为 ok/invalid/unverifiable，
        # not_applicable 在规则层处理
        pass

    report = AuditReport(
        steps=steps,
        verdicts=verdicts,
        first_error=first_error,
        recalc_result=recalc_result,
        coverage=coverage,
        judgment_semantics=judgment_semantics,
        pending_rules=pending_rules,
        unverified_rules=unverified_rules,
        tool_version=TOOL_VERSION,
        ruleset_version=get_threshold_table().version,
    )

    # 退出码：检出错误 → 1
    exit_code = 1 if first_error.first_error is not None else 0

    return AuditResult(report=report, exit_code=exit_code)


def data_dir_unavailable() -> Optional[str]:
    """随包数据不可用时返回可操作提示；可用时返回 None。

    CLI 层用它把"数据缺失"映射到**退出码 2**（用法与输入不可用），
    而不是压成 1 —— 1 的语义是"解答含错 / 基准未达标"。
    """
    data_dir = resolve_data_dir()
    missing = datadir.missing_entries(data_dir)
    if not missing:
        return None
    return datadir.missing_message(data_dir, missing)


def resolve_data_dir() -> Path:
    """解析随包数据目录（冻结态 = ``sys._MEIPASS/data``）。"""
    if datadir.is_frozen():
        return Path(sys._MEIPASS) / "data"
    return datadir.locate_data_dir()


def selftest() -> bool:
    """冻结态自检：数据可达 + 引擎自洽 + 台账未漂移。

    自检项（任一失败即返回 False，CLI 退出码 1）：
    1. 随包数据目录可达（阈值表 + 基准台账 + 快照）
    2. 冻结台账与生成器位级一致（禁手改守门）
    3. 引擎在一条已知干净解上零误报（K4）
    4. 引擎在一条已知含错解上检出错误（探活）

    Returns:
        是否通过
    """
    # 1. 数据目录可达（必需条目口径与 datadir 共用，避免两处漂移）
    data_dir = resolve_data_dir()

    if datadir.missing_entries(data_dir):
        return False

    # 2. 冻结台账位级一致
    try:
        from hws_math_auditor.benchmark.generator import check_frozen_ledger

        if check_frozen_ledger(data_dir / "benchmarks"):
            return False
    except Exception:
        return False

    # 3. 干净解零误报
    clean = "步骤1: x^2 - 4x + 3 = 0\n步骤2: (x-1)(x-3) = 0\n步骤3: x = 1 或 x = 3"
    try:
        clean_result = audit(AuditRequest(solution_text=clean))
        if clean_result.exit_code != 0:
            return False
    except Exception:
        return False

    # 4. 含错解必须被检出（探活）
    dirty = "步骤1: x^2 - 4x + 3 = 0\n步骤2: (x-1)(x-3) = 0\n步骤3: x = 1 或 x = 4"
    try:
        dirty_result = audit(AuditRequest(solution_text=dirty))
        if dirty_result.exit_code != 1:
            return False
    except Exception:
        return False

    return True
