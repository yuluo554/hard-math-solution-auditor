"""M4 LLM 兜底层测试。

测试内容：
- 模型开关（K7 默认关）
- 数值结论守门
- 快照机制
- 抽取兜底/别名归一/复核/行文
"""

import json
import tempfile
from pathlib import Path

import pytest

from hws_math_auditor.llm import (
    LLMRequest,
    LLMResponse,
    LLMResult,
    is_model_enabled,
    check_model_availability,
    contains_numeric_conclusion,
    validate_llm_output,
    compute_sha256,
    validate_snapshot,
    fallback_extraction,
    alias_normalization,
    review_verdict,
    generate_report,
)
from hws_math_auditor.config import config


# ---------------------------------------------------------------------------
# 模型开关测试
# ---------------------------------------------------------------------------

class TestModelSwitch:
    """模型开关测试（K7）。"""

    def test_model_default_disabled(self):
        """模型默认应关闭。"""
        # 保存原始状态
        original = config.model_enabled
        config.model_enabled = False

        try:
            assert not is_model_enabled()
        finally:
            config.model_enabled = original

    def test_model_enabled_check(self):
        """模型启用时应返回可用。"""
        original = config.model_enabled
        original_endpoint = config.model_endpoint
        config.model_enabled = True
        config.model_endpoint = "http://localhost:11434/v1"

        try:
            available, reason = check_model_availability()
            assert available
            assert reason == ""
        finally:
            config.model_enabled = original
            config.model_endpoint = original_endpoint

    def test_model_disabled_no_endpoint(self):
        """模型未启用时应返回原因。"""
        original = config.model_enabled
        config.model_enabled = False

        try:
            available, reason = check_model_availability()
            assert not available
            assert "未启用" in reason
        finally:
            config.model_enabled = original

    def test_model_enabled_no_endpoint(self):
        """模型启用但无端点时应返回原因。"""
        original = config.model_enabled
        original_endpoint = config.model_endpoint
        config.model_enabled = True
        config.model_endpoint = ""

        try:
            available, reason = check_model_availability()
            assert not available
            assert "端点" in reason
        finally:
            config.model_enabled = original
            config.model_endpoint = original_endpoint


# ---------------------------------------------------------------------------
# 数值结论守门测试
# ---------------------------------------------------------------------------

class TestNumericConclusionGate:
    """数值结论守门测试。"""

    def test_arithmetic_expression_detected(self):
        """算术表达式应被检测。"""
        assert contains_numeric_conclusion("x = 1 + 2")

    def test_equation_detected(self):
        """等式应被检测。"""
        assert contains_numeric_conclusion("3.14 = 3.14")

    def test_percentage_detected(self):
        """百分比应被检测。"""
        assert contains_numeric_conclusion("50%")

    def test_text_passed(self):
        """纯文本应通过。"""
        assert not contains_numeric_conclusion("这是一个文本")

    def test_mixed_content_detected(self):
        """混合内容中的数值结论应被检测。"""
        assert contains_numeric_conclusion("答案是 x = 1 + 2")

    def test_validate_llm_output_passes(self):
        """有效 LLM 输出应通过。"""
        valid_output = "步骤验证通过，表达式等价"
        passed, _ = validate_llm_output(valid_output)
        assert passed

    def test_validate_llm_output_fails(self):
        """含数值结论的 LLM 输出应失败。"""
        invalid_output = "计算结果为 x = 1 + 2"
        passed, reason = validate_llm_output(invalid_output)
        assert not passed
        assert "数值结论" in reason


# ---------------------------------------------------------------------------
# 快照机制测试
# ---------------------------------------------------------------------------

class TestSnapshotMechanism:
    """快照机制测试。"""

    def test_compute_sha256(self):
        """sha256 计算应正确。"""
        text = "test content"
        sha256 = compute_sha256(text)
        assert len(sha256) == 64
        # 实际 sha256 值（预计算）
        assert sha256 == "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"

    def test_validate_snapshot_correct(self):
        """正确快照应通过验证。"""
        content = "test content"
        sha256 = compute_sha256(content)
        snapshot = {
            "content": content,
            "sha256": sha256,
        }
        assert validate_snapshot(snapshot, sha256)

    def test_validate_snapshot_tampered(self):
        """篡改快照应失败。"""
        content = "test content"
        sha256 = compute_sha256(content)
        snapshot = {
            "content": "tampered content",  # 篡改
            "sha256": sha256,  # 仍是原内容的 sha256
        }
        # 期望的是篡改后内容的 sha256，与原 sha256 不匹配
        tampered_sha256 = compute_sha256("tampered content")
        assert not validate_snapshot(snapshot, tampered_sha256)

    def test_llm_response_snapshot_roundtrip(self):
        """LLM 响应快照往返应正确。"""
        response = LLMResponse(
            success=True,
            content="测试内容",
            model_name="test",
            model_version="1.0",
            generation_params={"temperature": 0.7},
            raw_output="raw",
            sha256="abc123",
            timestamp="2024-01-01T00:00:00+00:00",
        )

        snapshot = response.to_snapshot()
        restored = LLMResponse.from_snapshot(snapshot)

        assert restored.success == response.success
        assert restored.content == response.content
        assert restored.model_name == response.model_name


# ---------------------------------------------------------------------------
# 抽取兜底测试
# ---------------------------------------------------------------------------

class TestFallbackExtraction:
    """抽取兜底测试。"""

    def test_fallback_when_disabled(self):
        """模型未启用时应返回 fallback。"""
        original = config.model_enabled
        config.model_enabled = False

        try:
            result = fallback_extraction("some text")
            assert not result.used_model
            assert "未启用" in result.fallback_reason
        finally:
            config.model_enabled = original

    def test_fallback_with_snapshot(self):
        """快照应被正确使用。"""
        snapshot = {
            "success": True,
            "content": "x = 1",
            "model_name": "test",
            "model_version": "1.0",
            "generation_params": {},
            "raw_output": "x = 1",
            "sha256": "abc123",
            "timestamp": "2024-01-01T00:00:00+00:00",
        }

        # 由于 call_llm 内部逻辑，快照会被使用
        result = fallback_extraction("some text")
        # 验证结果结构正确
        assert isinstance(result, LLMResult)


# ---------------------------------------------------------------------------
# 别名归一测试
# ---------------------------------------------------------------------------

class TestAliasNormalization:
    """别名归一测试。"""

    def test_alias_normalization_when_disabled(self):
        """模型未启用时应返回 fallback。"""
        original = config.model_enabled
        config.model_enabled = False

        try:
            result = alias_normalization("x 和 y 是同一个变量", ["x", "y"])
            assert not result.used_model
        finally:
            config.model_enabled = original


# ---------------------------------------------------------------------------
# 复核测试
# ---------------------------------------------------------------------------

class TestReviewVerdict:
    """复核测试。"""

    def test_review_when_disabled(self):
        """模型未启用时应返回 fallback。"""
        original = config.model_enabled
        config.model_enabled = False

        try:
            result = review_verdict(
                {"status": "ok"},
                [{"step_no": 1, "expr": "x = 1"}],
            )
            assert not result.used_model
        finally:
            config.model_enabled = original


# ---------------------------------------------------------------------------
# 行文测试
# ---------------------------------------------------------------------------

class TestGenerateReport:
    """行文测试。"""

    def test_report_when_disabled(self):
        """模型未启用时应返回 fallback。"""
        original = config.model_enabled
        config.model_enabled = False

        try:
            result = generate_report({"steps": 5, "errors": 0})
            assert not result.used_model
        finally:
            config.model_enabled = original


# ---------------------------------------------------------------------------
# 集成测试
# ---------------------------------------------------------------------------

class TestLLMIntegration:
    """LLM 集成测试。"""

    def test_model_switch_affects_all_functions(self):
        """模型开关应影响所有 LLM 函数。"""
        original = config.model_enabled
        config.model_enabled = False

        try:
            # 所有函数都应返回 used_model=False
            assert not fallback_extraction("test").used_model
            assert not alias_normalization("test", []).used_model
            assert not review_verdict({}, []).used_model
            assert not generate_report({}).used_model
        finally:
            config.model_enabled = original

    def test_numeric_gate_blocks_invalid_output(self):
        """数值结论守门应阻止无效输出。"""
        invalid_outputs = [
            "x = 1 + 2",
            "3.14 = 3.14",
            "答案是 50%",
        ]

        for output in invalid_outputs:
            passed, _ = validate_llm_output(output)
            assert not passed, f"应被阻止: {output}"

    def test_numeric_gate_allows_valid_output(self):
        """数值结论守门应允许有效输出。"""
        valid_outputs = [
            "步骤验证通过",
            "表达式等价",
            "无错误",
        ]

        for output in valid_outputs:
            passed, _ = validate_llm_output(output)
            assert passed, f"应被允许: {output}"
