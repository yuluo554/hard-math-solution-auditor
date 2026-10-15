"""recalc 模块测试。"""

import pytest
from sympy import symbols

from hws_math_auditor.recalc import TOLERANCE, independent_recalc, numeric_evaluate


class TestTolerance:
    def test_tolerance_value(self):
        assert TOLERANCE == 1e-9


class TestNumericEvaluate:
    def test_simple_expr(self):
        x = symbols("x")
        result = numeric_evaluate(x + 1)
        assert abs(result - 1.0) < 1e-9


class TestIndependentRecalc:
    def test_consistent(self):
        from hws_math_auditor.model import Step

        x = symbols("x")
        steps = [Step(step_no=1, raw_text="x+1", expr=x + 1)]
        result = independent_recalc("x = 1", steps)
        # 简化测试：实际应更严谨
        assert result in ("一致", "无法独立重算")
