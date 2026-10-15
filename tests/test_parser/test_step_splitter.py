"""parser 模块测试。"""

import pytest

from hws_math_auditor.parser import extract_reasoning, split_steps
from hws_math_auditor.parser.normalizer import compute_coverage, latex_to_symbolic


class TestReasoningExtraction:
    def test_extract_reasoning_with_tag(self):
        text = "\u003c\u0069\u006d\u0065\u003e步骤1: x = 1\u003c/\u0069\u006d\u0065\u003e"
        reasoning, outside = extract_reasoning(text)
        assert "步骤1: x = 1" in reasoning

    def test_extract_reasoning_without_tag(self):
        text = "步骤1: x = 1"
        reasoning, outside = extract_reasoning(text)
        assert reasoning == text


class TestStepSplitting:
    def test_split_numbered_steps(self):
        text = "步骤1: x = 1\n步骤2: x = 2"
        steps = split_steps(text)
        assert len(steps) == 2
        assert steps[0].step_no == 1
        assert steps[1].step_no == 2

    def test_split_empty(self):
        steps = split_steps("")
        assert len(steps) == 0


class TestNormalizer:
    def test_latex_to_symbolic(self):
        result = latex_to_symbolic("\\frac{a}{b}")
        assert "(a)/(b)" in result

    def test_coverage(self, sample_solution_clean):
        steps = split_steps(sample_solution_clean)
        for step in steps:
            from hws_math_auditor.parser.normalizer import normalize_step_expr
            normalize_step_expr(step)
        coverage = compute_coverage(steps)
        assert coverage["total_steps"] == 3
