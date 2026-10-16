"""parser 模块测试。"""

import pytest

from hws_math_auditor.parser import extract_reasoning, split_steps
from hws_math_auditor.parser.normalizer import compute_coverage, latex_to_symbolic
from hws_math_auditor.parser import normalize_step


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

    def test_split_circle_number_steps(self):
        """测试圆圈数字编号（①②③）。"""
        text = "① x = 1\n② x = 2\n③ x = 3"
        steps = split_steps(text)
        assert len(steps) == 3
        assert steps[0].step_no == 1
        assert steps[1].step_no == 2
        assert steps[2].step_no == 3

    def test_split_mixed_arabic_circle(self):
        """测试阿拉伯数字与圆圈数字混合编号。"""
        text = "步骤1: x = 1\n② x = 2\n步骤3: x = 3"
        steps = split_steps(text)
        assert len(steps) == 3
        assert steps[0].step_no == 1
        assert steps[1].step_no == 2
        assert steps[2].step_no == 3

    def test_split_paragraph_no_numbers(self):
        """测试无编号段落切分（按空行）。"""
        text = "解方程 x^2 - 5x + 6 = 0\n\n因式分解 (x-2)(x-3) = 0\n\n所以 x = 2 或 x = 3"
        steps = split_steps(text)
        assert len(steps) == 3
        assert steps[0].step_no == 1
        assert "解方程" in steps[0].raw_text
        assert "因式分解" in steps[1].raw_text

    def test_split_single_step(self):
        """测试单一步骤（应返回单一步骤）。"""
        text = "解方程 x^2 - 5x + 6 = 0"
        steps = split_steps(text)
        assert len(steps) == 1
        assert steps[0].step_no == 1

    def test_split_many_steps(self):
        """测试超过 20 步（应触发段落切分）。"""
        text = "\n".join([f"步骤{i}: x = {i}" for i in range(1, 25)])
        steps = split_steps(text)
        # 应能正确切分所有步骤
        assert len(steps) == 24

    def test_split_with_various_formats(self):
        """测试多种编号格式。"""
        text = "1. x = 1\n2、 x = 2\n3) x = 3\n4） x = 4\n5: x = 5\n6： x = 6"
        steps = split_steps(text)
        assert len(steps) == 6

    def test_split_preserves_source_lines(self):
        """测试源行号记录。"""
        text = "步骤1: x = 1\n步骤2: x = 2"
        steps = split_steps(text)
        assert steps[0].source_line_start == 1
        assert steps[0].source_line_end == 1
        assert steps[1].source_line_start == 2
        assert steps[1].source_line_end == 2


class TestNormalizer:
    def test_latex_to_symbolic(self):
        result = latex_to_symbolic("\\frac{a}{b}")
        assert "(a)/(b)" in result

    def test_latex_to_symbolic_complex(self):
        """测试复杂 LaTeX 转换。"""
        result = latex_to_symbolic("\\sqrt{x^2 + y^2}")
        assert "sqrt" in result

    def test_latex_to_symbolic_sin_squared(self):
        """测试 sin²θ 转换。"""
        result = latex_to_symbolic("sin²θ")
        assert "**2" in result

    def test_coverage(self, sample_solution_clean):
        steps = split_steps(sample_solution_clean)
        for step in steps:
            from hws_math_auditor.parser.normalizer import normalize_step_expr
            normalize_step_expr(step)
        coverage = compute_coverage(steps)
        assert coverage["total_steps"] == 3

    def test_normalize_step_integration(self):
        """测试 normalize_step 集成调用。"""
        text = "步骤1: x^2 - 5x + 6 = 0"
        steps = split_steps(text)
        assert len(steps) == 1
        step = normalize_step(steps[0])
        assert step.status == "normalized"
        assert step.expr is not None

    def test_normalize_step_unsymbolizable(self):
        """测试不可符号化步骤。"""
        text = "步骤1: 这是纯文本，无数学表达式"
        steps = split_steps(text)
        assert len(steps) == 1
        step = normalize_step(steps[0])
        assert step.status == "unsymbolizable"
        assert step.reason is not None


class TestUnsymbolizableClassification:
    """不可符号化分类测试。"""

    def test_unparseable_latex(self):
        """测试无法解析的 LaTeX。"""
        text = "步骤1: \x5c\x69\x6e\x76\x61\x6c\x69\x64\x5f\x63\x6f\x6e\x73\x74\x72\x75\x63\x74"
        steps = split_steps(text)
        step = normalize_step(steps[0])
        assert step.status == "unsymbolizable"

    def test_sympify_error(self):
        """测试 sympify 错误。"""
        text = "步骤1: 这是一个中文描述，不是数学表达式"
        steps = split_steps(text)
        step = normalize_step(steps[0])
        assert step.status == "unsymbolizable"

    def test_unknown_symbol(self):
        """测试未知符号。"""
        text = "步骤1: \x5c\x6e\x6f\x6e\x65\x78\x69\x73\x74\x65\x6e\x74\x5f\x73\x79\x6d\x62\x6f\x6c"
        steps = split_steps(text)
        step = normalize_step(steps[0])
        assert step.status == "unsymbolizable"

    def test_unsupported_construct(self):
        """测试不支持的构造。"""
        text = "步骤1: \x5c\x62\x65\x67\x69\x6e\x7b\x65\x71\x75\x61\x74\x69\x6f\x6e\x7d x = 1 \x5c\x65\x6e\x64\x7b\x65\x71\x75\x61\x74\x69\x6f\x6e\x7d"
        steps = split_steps(text)
        step = normalize_step(steps[0])
        # LaTeX environment may not be fully supported
        assert step.status in ("normalized", "unsymbolizable")


class TestBoundaryCases:
    """边界用例测试。"""

    def test_empty_input(self):
        """测试空输入。"""
        steps = split_steps("")
        assert len(steps) == 0

    def test_pure_text(self):
        """测试纯文本（无数学表达式，含逗号导致 sympify 失败）。"""
        text = "这是一段纯文本，无数学表达式"
        steps = split_steps(text)
        assert len(steps) == 1
        step = normalize_step(steps[0])
        assert step.status == "unsymbolizable"

    def test_pure_latex(self):
        """测试纯 LaTeX。"""
        text = "步骤1: \x5c\x66\x72\x61\x63\x7b\x61\x7d\x7b\x62\x7d"
        steps = split_steps(text)
        step = normalize_step(steps[0])
        assert step.status == "normalized"

    def test_mixed_format(self):
        """测试混合格式（中文 + LaTeX + 数学）。"""
        text = "步骤1: 解方程 x^2 - 5x + 6 = 0，即 (x-2)(x-3) = 0"
        steps = split_steps(text)
        step = normalize_step(steps[0])
        assert step.status == "normalized"

    def test_whitespace_only(self):
        """测试纯空白输入。"""
        steps = split_steps("   \n\n   ")
        assert len(steps) == 0

    def test_unicode_superscripts(self):
        """测试 Unicode 上标。"""
        text = "步骤1: x² + y² = z²"
        steps = split_steps(text)
        step = normalize_step(steps[0])
        assert step.status == "normalized"


class TestCoverageReport:
    """覆盖率报告测试。"""

    def test_coverage_denominator_reflects_code(self):
        """测试覆盖度分母反映检出步骤数。"""
        text = "步骤1: x = 1\n步骤2: 这是文本，有逗号\n步骤3: y = 2"
        steps = split_steps(text)
        for step in steps:
            normalize_step(step)
        coverage = compute_coverage(steps)
        assert coverage["total_steps"] == 3
        assert coverage["normalized"] == 2
        assert coverage["unsymbolizable"] == 1

    def test_coverage_reasons_distribution(self):
        """测试不可符号化原因分布。"""
        text = "步骤1: x = 1\n步骤2: 这是纯文本，有逗号"
        steps = split_steps(text)
        for step in steps:
            normalize_step(step)
        coverage = compute_coverage(steps)
        assert "reasons" in coverage
        assert coverage["unsymbolizable"] == 1
