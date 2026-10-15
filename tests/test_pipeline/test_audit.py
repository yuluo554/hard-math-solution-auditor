"""pipeline 集成测试。"""

import pytest

from hws_math_auditor.pipeline import AuditRequest, audit


class TestAuditPipeline:
    def test_audit_clean(self, sample_solution_clean):
        request = AuditRequest(solution_text=sample_solution_clean)
        result = audit(request)
        assert result.exit_code == 0  # 无错误

    def test_audit_dirty(self, sample_solution_dirty):
        request = AuditRequest(solution_text=sample_solution_dirty)
        result = audit(request)
        # 含错解答应检出错误
        assert result.exit_code == 1

    def test_audit_empty(self):
        request = AuditRequest(solution_text="")
        result = audit(request)
        assert result.exit_code == 2  # 输入不可用
