"""locator 模块测试。"""

import pytest

from hws_math_auditor.model import Step, Verdict
from hws_math_auditor.locator import locate_first_error


class TestFirstError:
    def test_no_error(self):
        steps = [Step(step_no=i, raw_text=f"step{i}") for i in range(1, 4)]
        verdicts = [Verdict("ok", "", None) for _ in range(3)]
        result = locate_first_error(verdicts, steps)
        assert result.first_error is None

    def test_single_error(self):
        steps = [Step(step_no=i, raw_text=f"step{i}") for i in range(1, 4)]
        verdicts = [
            Verdict("ok", "", None),
            Verdict("invalid", "", None),
            Verdict("ok", "", None),
        ]
        result = locate_first_error(verdicts, steps)
        assert result.first_error == 1  # 0-indexed

    def test_multiple_errors(self):
        """多步同时 invalid，取最小序号为首错。"""
        steps = [Step(step_no=i, raw_text=f"step{i}") for i in range(1, 5)]
        verdicts = [
            Verdict("ok", "", None),
            Verdict("invalid", "", None),
            Verdict("invalid", "", None),
            Verdict("ok", "", None),
        ]
        result = locate_first_error(verdicts, steps)
        assert result.first_error == 1  # 最小序号
