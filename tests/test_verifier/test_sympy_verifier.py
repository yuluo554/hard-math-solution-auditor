"""verifier 模块测试。"""

import pytest
from sympy import symbols, simplify

from hws_math_auditor.verifier import verify_step, verify_all


class TestVerifier:
    def test_ok_verdict(self):
        x = symbols("x")
        prev = x + 1
        curr = simplify(x + 1)
        verdict = verify_step(prev, curr)
        assert verdict.status == "ok"

    def test_invalid_verdict(self):
        x = symbols("x")
        prev = x + 1
        curr = x + 2
        verdict = verify_step(prev, curr)
        assert verdict.status == "invalid"
        assert verdict.counterexample is not None

    def test_unverifiable(self):
        verdict = verify_step(None, None)
        assert verdict.status == "unverifiable"

    def test_verify_all(self):
        from hws_math_auditor.model import Step

        x = symbols("x")
        steps = [
            Step(step_no=1, raw_text="x+1", expr=x + 1, source_line_start=1, source_line_end=1),
            Step(step_no=2, raw_text="x+1", expr=x + 1, source_line_start=2, source_line_end=2),
        ]
        verdicts = verify_all(steps)
        assert len(verdicts) == 2
