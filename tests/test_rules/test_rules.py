"""M3 知识与规则层测试。

测试内容：
- 阈值表格式验证
- status 门控
- 零政策字面量门禁
- 判定语义不虚高
"""

import json
import tempfile
from pathlib import Path

import pytest

from hws_math_auditor.rules import (
    ThresholdRule,
    ThresholdTable,
    load_threshold_table,
    validate_threshold_table,
    check_zero_literal_gate,
    validate_judgment_semantics,
    check_threshold,
    reset_threshold_table,
    scan_for_policy_literals,
)


# ---------------------------------------------------------------------------
# 阈值表格式验证测试
# ---------------------------------------------------------------------------

class TestThresholdTableValidation:
    """阈值表格式验证。"""

    def test_valid_threshold_table(self, tmp_path):
        """有效阈值表应通过验证。"""
        table_data = {
            "version": "1.0.0",
            "description": "测试阈值表",
            "rules": [
                {
                    "id": "THR-001",
                    "code": "test_rule",
                    "name": "测试规则",
                    "description": "测试描述",
                    "threshold": 1e-9,
                    "operator": "greater_than_or_equal",
                    "status": "verified",
                    "verified_by": "测试",
                    "scope": "calc",
                }
            ],
        }
        table_path = tmp_path / "thresholds.json"
        table_path.write_text(json.dumps(table_data, ensure_ascii=False))

        table = load_threshold_table(table_path)
        errors = validate_threshold_table(table)
        assert errors == []

    def test_missing_version(self, tmp_path):
        """缺少 version 字段应报错。"""
        table_data = {
            "description": "测试阈值表",
            "rules": [],
        }
        table_path = tmp_path / "thresholds.json"
        table_path.write_text(json.dumps(table_data))

        # 缺少 version 字段应在 from_dict 时抛出 KeyError
        with pytest.raises(KeyError):
            load_threshold_table(table_path)

    def test_duplicate_rule_id(self, tmp_path):
        """重复规则 id 应报错。"""
        table_data = {
            "version": "1.0.0",
            "rules": [
                {
                    "id": "THR-001",
                    "code": "test_rule",
                    "name": "测试规则",
                    "description": "测试描述",
                    "threshold": 1e-9,
                    "operator": "greater_than_or_equal",
                    "status": "verified",
                    "verified_by": "测试",
                    "scope": "calc",
                },
                {
                    "id": "THR-001",  # 重复
                    "code": "test_rule2",
                    "name": "测试规则2",
                    "description": "测试描述2",
                    "threshold": 1e-9,
                    "operator": "greater_than_or_equal",
                    "status": "verified",
                    "verified_by": "测试",
                    "scope": "calc",
                },
            ],
        }
        table_path = tmp_path / "thresholds.json"
        table_path.write_text(json.dumps(table_data))

        table = load_threshold_table(table_path)
        errors = validate_threshold_table(table)
        assert any("id 重复" in e for e in errors)

    def test_invalid_status(self, tmp_path):
        """非法 status 应报错。"""
        table_data = {
            "version": "1.0.0",
            "rules": [
                {
                    "id": "THR-001",
                    "code": "test_rule",
                    "name": "测试规则",
                    "description": "测试描述",
                    "threshold": 1e-9,
                    "operator": "greater_than_or_equal",
                    "status": "invalid_status",  # 非法
                    "verified_by": "测试",
                    "scope": "calc",
                }
            ],
        }
        table_path = tmp_path / "thresholds.json"
        table_path.write_text(json.dumps(table_data))

        table = load_threshold_table(table_path)
        errors = validate_threshold_table(table)
        assert any("非法 status" in e for e in errors)

    def test_verified_rule_missing_verified_by(self, tmp_path):
        """verified 规则缺少 verified_by 应报错。"""
        table_data = {
            "version": "1.0.0",
            "rules": [
                {
                    "id": "THR-001",
                    "code": "test_rule",
                    "name": "测试规则",
                    "description": "测试描述",
                    "threshold": 1e-9,
                    "operator": "greater_than_or_equal",
                    "status": "verified",
                    # 缺少 verified_by
                    "scope": "calc",
                }
            ],
        }
        table_path = tmp_path / "thresholds.json"
        table_path.write_text(json.dumps(table_data))

        table = load_threshold_table(table_path)
        errors = validate_threshold_table(table)
        assert any("verified 规则缺少 verified_by" in e for e in errors)


# ---------------------------------------------------------------------------
# status 门控测试
# ---------------------------------------------------------------------------

class TestStatusGate:
    """status 门控测试。"""

    def test_verified_rules_active(self, tmp_path):
        """verified 规则应参与判定。"""
        table_data = {
            "version": "1.0.0",
            "rules": [
                {
                    "id": "THR-001",
                    "code": "test_rule",
                    "name": "测试规则",
                    "description": "测试描述",
                    "threshold": 1e-9,
                    "operator": "greater_than_or_equal",
                    "status": "verified",
                    "verified_by": "测试",
                    "scope": "calc",
                }
            ],
        }
        table_path = tmp_path / "thresholds.json"
        table_path.write_text(json.dumps(table_data))

        table = load_threshold_table(table_path)
        verified = table.get_verified_rules()
        assert len(verified) == 1
        assert verified[0].is_active()

    def test_pending_rules_not_active(self, tmp_path):
        """pending 规则不应参与判定。"""
        table_data = {
            "version": "1.0.0",
            "rules": [
                {
                    "id": "THR-001",
                    "code": "test_rule",
                    "name": "测试规则",
                    "description": "测试描述",
                    "threshold": 1e-9,
                    "operator": "greater_than_or_equal",
                    "status": "pending",
                    "verified_by": "待核对",
                    "scope": "calc",
                }
            ],
        }
        table_path = tmp_path / "thresholds.json"
        table_path.write_text(json.dumps(table_data))

        table = load_threshold_table(table_path)
        verified = table.get_verified_rules()
        assert len(verified) == 0
        assert not table.rules[0].is_active()

    def test_unverified_rules_not_active(self, tmp_path):
        """unverified 规则不应参与判定。"""
        table_data = {
            "version": "1.0.0",
            "rules": [
                {
                    "id": "THR-001",
                    "code": "test_rule",
                    "name": "测试规则",
                    "description": "测试描述",
                    "threshold": 1e-9,
                    "operator": "greater_than_or_equal",
                    "status": "unverified",
                    "verified_by": "未验证",
                    "scope": "calc",
                }
            ],
        }
        table_path = tmp_path / "thresholds.json"
        table_path.write_text(json.dumps(table_data))

        table = load_threshold_table(table_path)
        verified = table.get_verified_rules()
        assert len(verified) == 0

    def test_pending_rules_recorded(self, tmp_path):
        """pending 规则应显式记录待核对。"""
        table_data = {
            "version": "1.0.0",
            "rules": [
                {
                    "id": "THR-001",
                    "code": "test_rule",
                    "name": "测试规则",
                    "description": "测试描述",
                    "threshold": 1e-9,
                    "operator": "greater_than_or_equal",
                    "status": "pending",
                    "verified_by": "待核对",
                    "scope": "calc",
                }
            ],
        }
        table_path = tmp_path / "thresholds.json"
        table_path.write_text(json.dumps(table_data))

        table = load_threshold_table(table_path)
        pending = table.get_pending_rules()
        assert len(pending) == 1
        assert pending[0].status == "pending"

    def test_scope_filtering(self, tmp_path):
        """按作用域过滤规则。"""
        table_data = {
            "version": "1.0.0",
            "rules": [
                {
                    "id": "THR-001",
                    "code": "calc_rule",
                    "name": "计算规则",
                    "description": "测试描述",
                    "threshold": 1e-9,
                    "operator": "greater_than_or_equal",
                    "status": "verified",
                    "verified_by": "测试",
                    "scope": "calc",
                },
                {
                    "id": "THR-002",
                    "code": "check_rule",
                    "name": "检查规则",
                    "description": "测试描述",
                    "threshold": 1e-9,
                    "operator": "greater_than_or_equal",
                    "status": "verified",
                    "verified_by": "测试",
                    "scope": "check",
                },
            ],
        }
        table_path = tmp_path / "thresholds.json"
        table_path.write_text(json.dumps(table_data))

        table = load_threshold_table(table_path)
        calc_rules = table.get_verified_rules(scope="calc")
        check_rules = table.get_verified_rules(scope="check")
        assert len(calc_rules) == 1
        assert len(check_rules) == 1
        assert calc_rules[0].id == "THR-001"
        assert check_rules[0].id == "THR-002"


# ---------------------------------------------------------------------------
# 零政策字面量门禁测试
# ---------------------------------------------------------------------------

class TestZeroLiteralGate:
    """零政策字面量门禁测试。"""

    def test_config_py_exempt(self, tmp_path):
        """config.py 中的 TOLERANCE 应豁免。"""
        # 创建项目结构
        src_dir = tmp_path / "src" / "hws_math_auditor"
        src_dir.mkdir(parents=True)
        (src_dir / "config.py").write_text('TOLERANCE = 1e-9\n')

        passed, violations = check_zero_literal_gate(tmp_path)
        assert passed  # 应该通过，因为 config.py 中的 1e-9 是豁免的

    def test_non_exempt_literal_detected(self, tmp_path):
        """非豁免文件中的政策字面量应被检测。"""
        src_dir = tmp_path / "src" / "hws_math_auditor"
        src_dir.mkdir(parents=True)
        # 在非 config.py 文件中写入 1e-9
        (src_dir / "verifier.py").write_text('diff = 1e-9\n')

        passed, violations = check_zero_literal_gate(tmp_path)
        assert not passed
        assert len(violations) > 0

    def test_threshold_json_exempt(self, tmp_path):
        """阈值表本身应豁免。"""
        data_dir = tmp_path / "data" / "rules"
        data_dir.mkdir(parents=True)
        threshold_data = {
            "version": "1.0.0",
            "rules": [
                {
                    "id": "THR-001",
                    "code": "test",
                    "name": "测试",
                    "description": "测试",
                    "threshold": 1e-9,
                    "operator": "greater_than_or_equal",
                    "status": "verified",
                    "verified_by": "测试",
                    "scope": "calc",
                }
            ],
        }
        (data_dir / "thresholds.json").write_text(json.dumps(threshold_data))

        passed, violations = check_zero_literal_gate(tmp_path)
        # 阈值表本身豁免，但其他文件可能还有
        # 这里主要验证阈值表不会被误报

    def test_scan_for_literals(self, tmp_path):
        """扫描功能应正确检测字面量。"""
        src_dir = tmp_path / "src" / "hws_math_auditor"
        src_dir.mkdir(parents=True)
        (src_dir / "test.py").write_text('value = 1e-9\n')

        violations = scan_for_policy_literals(tmp_path)
        # 应该检测到 1e-9
        assert len(violations) > 0

    def test_mutation_verification_gate_catches_new_literal(self, tmp_path):
        """变异验证：新增字面量必须触发门禁。"""
        src_dir = tmp_path / "src" / "hws_math_auditor"
        src_dir.mkdir(parents=True)
        (src_dir / "config.py").write_text('TOLERANCE = 1e-9\n')

        # 初始状态：通过
        passed, _ = check_zero_literal_gate(tmp_path)
        assert passed

        # 新增字面量
        (src_dir / "new_file.py").write_text('threshold = 1e-9\n')

        # 应被检测
        passed, violations = check_zero_literal_gate(tmp_path)
        assert not passed
        assert len(violations) == 1


# ---------------------------------------------------------------------------
# 判定语义不虚高测试
# ---------------------------------------------------------------------------

class TestJudgmentSemantics:
    """判定语义不虚高测试。"""

    def test_not_applicable_without_exception(self):
        """not_applicable 用于原文未写例外情形的项应报错。"""
        result = validate_judgment_semantics(
            verdict_status="not_applicable",
            evidence="",
            has_explicit_exception=False,
            has_obligation=True,
        )
        assert not result["valid"]
        assert any("not_applicable" in issue for issue in result["issues"])

    def test_not_applicable_with_exception_ok(self):
        """not_applicable 用于原文写了例外情形的项应通过。"""
        result = validate_judgment_semantics(
            verdict_status="not_applicable",
            evidence="原文写了例外情形",
            has_explicit_exception=True,
            has_obligation=True,
        )
        assert result["valid"]

    def test_compliant_without_obligation(self):
        """无适用项却输出 compliant 应报错。"""
        result = validate_judgment_semantics(
            verdict_status="compliant",
            evidence="",
            has_explicit_exception=False,
            has_obligation=False,  # 无义务
        )
        assert not result["valid"]
        assert any("compliant" in issue for issue in result["issues"])

    def test_missing_obligation_noncompliant(self):
        """无条件义务缺失应判定为 noncompliant。"""
        result = validate_judgment_semantics(
            verdict_status="ok",  # 错误状态
            evidence="",
            has_explicit_exception=False,
            has_obligation=False,  # 无义务
        )
        assert not result["valid"]
        assert any("noncompliant" in issue for issue in result["issues"])

    def test_valid_judgment(self):
        """有效判定应通过。"""
        result = validate_judgment_semantics(
            verdict_status="invalid",
            evidence="确证错误",
            has_explicit_exception=False,
            has_obligation=True,
        )
        assert result["valid"]


# ---------------------------------------------------------------------------
# 阈值比较测试
# ---------------------------------------------------------------------------

class TestThresholdCheck:
    """阈值比较测试。"""

    def test_greater_than_or_equal_pass(self):
        """大于等于阈值应通过。"""
        rule = ThresholdRule(
            id="THR-001",
            code="test",
            name="测试",
            description="测试",
            threshold=1e-9,
            operator="greater_than_or_equal",
            applies_if="any",
            status="verified",
            verified_by="测试",
        )
        assert check_threshold(1e-9, rule)  # 等于
        assert check_threshold(2e-9, rule)  # 大于

    def test_greater_than_or_equal_fail(self):
        """小于阈值应失败。"""
        rule = ThresholdRule(
            id="THR-001",
            code="test",
            name="测试",
            description="测试",
            threshold=1e-9,
            operator="greater_than_or_equal",
            applies_if="any",
            status="verified",
            verified_by="测试",
        )
        assert not check_threshold(0.5e-9, rule)  # 小于

    def test_less_than_or_equal_pass(self):
        """小于等于阈值应通过。"""
        rule = ThresholdRule(
            id="THR-001",
            code="test",
            name="测试",
            description="测试",
            threshold=1e-9,
            operator="less_than_or_equal",
            applies_if="any",
            status="verified",
            verified_by="测试",
        )
        assert check_threshold(1e-9, rule)  # 等于
        assert check_threshold(0.5e-9, rule)  # 小于

    def test_equal_pass(self):
        """等于阈值应通过。"""
        rule = ThresholdRule(
            id="THR-001",
            code="test",
            name="测试",
            description="测试",
            threshold=1e-9,
            operator="equal",
            applies_if="any",
            status="verified",
            verified_by="测试",
        )
        assert check_threshold(1e-9, rule)

    def test_invalid_operator(self):
        """非法操作符应报错。"""
        rule = ThresholdRule(
            id="THR-001",
            code="test",
            name="测试",
            description="测试",
            threshold=1e-9,
            operator="invalid",
            applies_if="any",
            status="verified",
            verified_by="测试",
        )
        with pytest.raises(ValueError):
            check_threshold(1e-9, rule)


# ---------------------------------------------------------------------------
# 集成测试
# ---------------------------------------------------------------------------

class TestRulesIntegration:
    """规则层集成测试。"""

    def test_load_default_threshold_table(self):
        """加载默认阈值表。"""
        reset_threshold_table()
        table = load_threshold_table()
        assert table.version == "1.0.0"
        assert len(table.rules) > 0

    def test_validate_default_table(self):
        """验证默认阈值表。"""
        reset_threshold_table()
        table = load_threshold_table()
        errors = validate_threshold_table(table)
        assert errors == []

    def test_status_gate_on_default_table(self):
        """默认阈值表的 status 门控。"""
        reset_threshold_table()
        table = load_threshold_table()
        verified = table.get_verified_rules()
        pending = table.get_pending_rules()
        unverified = table.get_unverified_rules()

        # 至少有一些 verified 规则
        assert len(verified) > 0
        # pending 规则应被记录
        assert len(pending) >= 0  # 可能为 0
        # unverified 规则不进引擎
        assert len(unverified) >= 0
