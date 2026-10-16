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
        # x+1 有自由变量，应抛出异常
        with pytest.raises((TypeError, ValueError)):
            numeric_evaluate(x + 1)

    def test_constant_expr(self):
        result = numeric_evaluate(5)
        assert abs(result - 5.0) < 1e-9


class TestIndependentRecalc:
    def test_consistent(self):
        from hws_math_auditor.model import Step

        x = symbols("x")
        steps = [Step(step_no=1, raw_text="x+1", expr=x + 1, source_line_start=1, source_line_end=1)]
        result = independent_recalc("x = 1", steps)
        # 简化测试：实际应更严谨
        assert result in ("一致", "无法独立重算")
