"""模块④：LLM 兜底层（M4）。

职责：
- 抽取兜底：当解析器无法归一化时，LLM 兜底提取表达式
- 别名归一：LLM 识别变量别名并归一
- 复核：LLM 对引擎判定结果做行文复核
- 行文：LLM 生成人类可读的审计报告

铁律：
- 数值结论永远来自确定性规则（K7 模型默认关）
- LLM 不得输出数值结论
- 快照机制：离线复跑用快照，不依赖当场跑模型
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from hws_math_auditor.config import config


# ---------------------------------------------------------------------------
# 数据类
# ---------------------------------------------------------------------------

@dataclass
class LLMRequest:
    """LLM 请求。"""

    task: str  # extraction / alias_normalization / review / report
    raw_text: str
    context: Optional[dict] = None
    model_params: Optional[dict] = None


@dataclass
class LLMResponse:
    """LLM 响应。"""

    success: bool
    content: str
    model_name: str = ""
    model_version: str = ""
    generation_params: dict = field(default_factory=dict)
    raw_output: str = ""
    sha256: str = ""
    timestamp: str = ""

    @classmethod
    def from_snapshot(cls, snapshot: dict) -> "LLMResponse":
        """从快照创建响应。"""
        return cls(
            success=snapshot.get("success", False),
            content=snapshot.get("content", ""),
            model_name=snapshot.get("model_name", ""),
            model_version=snapshot.get("model_version", ""),
            generation_params=snapshot.get("generation_params", {}),
            raw_output=snapshot.get("raw_output", ""),
            sha256=snapshot.get("sha256", ""),
            timestamp=snapshot.get("timestamp", ""),
        )

    def to_snapshot(self) -> dict:
        """转为快照字典。"""
        return {
            "success": self.success,
            "content": self.content,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "generation_params": self.generation_params,
            "raw_output": self.raw_output,
            "sha256": self.sha256,
            "timestamp": self.timestamp,
        }


@dataclass
class LLMResult:
    """LLM 兜底结果。"""

    used_model: bool
    response: Optional[LLMResponse] = None
    fallback_reason: str = ""


# ---------------------------------------------------------------------------
# 快照机制
# ---------------------------------------------------------------------------

def compute_sha256(text: str) -> str:
    """计算文本的 sha256。"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def validate_snapshot(snapshot: dict, expected_sha256: str) -> bool:
    """验证快照完整性。

    Args:
        snapshot: 快照字典
        expected_sha256: 期望的 sha256

    Returns:
        快照是否完整
    """
    actual_sha256 = snapshot.get("sha256", "")
    return actual_sha256 == expected_sha256


# ---------------------------------------------------------------------------
# 模型开关
# ---------------------------------------------------------------------------

def is_model_enabled() -> bool:
    """检查模型是否启用。

    K7: 默认关，显式启用才生效。
    """
    return config.model_enabled


def check_model_availability() -> tuple[bool, str]:
    """检查模型可用性。

    Returns:
        (是否可用, 原因)
    """
    if not is_model_enabled():
        return False, "模型未启用（K7: 默认关）"

    if not config.model_endpoint:
        return False, "模型端点未配置"

    return True, ""


# ---------------------------------------------------------------------------
# 数值结论守门
# ---------------------------------------------------------------------------

# 禁止 LLM 输出的数值结论模式
NUMERIC_OUTPUT_PATTERNS = [
    r"[-+]?\d*\.?\d+\s*[-+*/]\s*[-+]?\d*\.?\d+",  # 算术表达式
    r"[-+]?\d*\.?\d+\s*=\s*[-+]?\d*\.?\d+",  # 等式
    r"\b\d+\.?\d*\s*%",  # 百分比
]


def contains_numeric_conclusion(text: str) -> bool:
    """检查文本是否包含数值结论。

    用于守门：LLM 输出不得包含数值结论。
    """
    import re

    for pattern in NUMERIC_OUTPUT_PATTERNS:
        if re.search(pattern, text):
            return True
    return False


def validate_llm_output(output: str) -> tuple[bool, str]:
    """验证 LLM 输出。

    Returns:
        (是否通过, 违规信息)
    """
    if contains_numeric_conclusion(output):
        return False, "LLM 输出包含数值结论，违反铁律：数值结论必须来自确定性规则"

    return True, ""


# ---------------------------------------------------------------------------
# LLM 调用（带快照支持）
# ---------------------------------------------------------------------------

def call_llm(request: LLMRequest, snapshot: Optional[dict] = None) -> LLMResult:
    """调用 LLM。

    若模型未启用，返回 fallback 结果。
    若提供快照，使用快照（离线复跑）。

    Args:
        request: LLM 请求
        snapshot: 快照字典（可选）

    Returns:
        LLM 结果
    """
    # 检查模型可用性
    available, reason = check_model_availability()

    if not available:
        return LLMResult(
            used_model=False,
            fallback_reason=reason,
        )

    # 若提供快照，使用快照
    if snapshot:
        response = LLMResponse.from_snapshot(snapshot)
        return LLMResult(
            used_model=True,
            response=response,
            fallback_reason="",
        )

    # 实际调用 LLM（占位）
    # 实际实现会调用 config.model_endpoint
    response = LLMResponse(
        success=False,
        content="",
        model_name=config.model_provider,
        model_version="",
        generation_params={"timeout": config.model_timeout},
        raw_output="",
        sha256="",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    return LLMResult(
        used_model=True,
        response=response,
        fallback_reason="LLM 调用未实现（占位）",
    )


# ---------------------------------------------------------------------------
# 抽取兜底
# ---------------------------------------------------------------------------

def fallback_extraction(raw_text: str) -> LLMResult:
    """抽取兜底。

    当解析器无法归一化时，LLM 兜底提取表达式。

    Args:
        raw_text: 原始文本

    Returns:
        LLM 结果
    """
    request = LLMRequest(
        task="extraction",
        raw_text=raw_text,
        context={"reason": "解析器归一化失败"},
    )

    return call_llm(request)


# ---------------------------------------------------------------------------
# 别名归一
# ---------------------------------------------------------------------------

def alias_normalization(raw_text: str, variables: list[str]) -> LLMResult:
    """别名归一。

    LLM 识别变量别名并归一。

    Args:
        raw_text: 原始文本
        variables: 已知变量列表

    Returns:
        LLM 结果
    """
    request = LLMRequest(
        task="alias_normalization",
        raw_text=raw_text,
        context={"variables": variables},
    )

    return call_llm(request)


# ---------------------------------------------------------------------------
# 复核
# ---------------------------------------------------------------------------

def review_verdict(verdict: dict, steps: list[dict]) -> LLMResult:
    """复核。

    LLM 对引擎判定结果做行文复核。

    Args:
        verdict: 引擎判定结果
        steps: 步骤列表

    Returns:
        LLM 结果
    """
    request = LLMRequest(
        task="review",
        raw_text=json.dumps(steps, ensure_ascii=False),
        context={"verdict": verdict},
    )

    return call_llm(request)


# ---------------------------------------------------------------------------
# 行文
# ---------------------------------------------------------------------------

def generate_report(report_data: dict) -> LLMResult:
    """行文。

    LLM 生成人类可读的审计报告。

    Args:
        report_data: 报告数据

    Returns:
        LLM 结果
    """
    request = LLMRequest(
        task="report",
        raw_text=json.dumps(report_data, ensure_ascii=False),
    )

    return call_llm(request)
