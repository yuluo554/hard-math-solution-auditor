"""模块⑤-a：合成基准用例生成器。

程序化生成竞赛级题目 + 解题步骤，并植入已知错误步。
真值库只存 input + expect，不存 observed（K3）。
"""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass, field, asdict
from typing import Any, Optional


# ---------------------------------------------------------------------------
# 数据类
# ---------------------------------------------------------------------------

@dataclass
class BenchmarkCase:
    """单条基准用例。"""

    id: str
    input: dict[str, Any]
    expect: dict[str, Any]
    meta: dict[str, Any]

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)

    def sha256(self) -> str:
        """计算用例的 sha256（用于快照留档）。"""
        payload = json.dumps(asdict(self), ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass
class ProblemTemplate:
    """题目模板。"""
    id: str
    category: str
    problem: str
    correct_solution: str
    final_assertion: str
    # 预置含错解答（按错误类型）
    dirty_solutions: dict[str, tuple[str, int]] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# 题目模板库（含预置含错解答）
# ---------------------------------------------------------------------------

TEMPLATES: list[ProblemTemplate] = [
    # ---- 模板1：二次方程求解 ----
    ProblemTemplate(
        id="T01",
        category="quadratic",
        problem="解方程 x^2 - 5x + 6 = 0",
        correct_solution=(
            "步骤1: x^2 - 5x + 6 = 0\n"
            "步骤2: (x-2)(x-3) = 0\n"
            "步骤3: x = 2 或 x = 3"
        ),
        final_assertion="x = 2 or x = 3",
        dirty_solutions={
            "illegal_algebra": (
                "步骤1: x^2 - 5x + 6 = 0\n"
                "步骤2: (x-2)(x-3) = 0\n"
                "步骤3: x = 2 - 3 = -1",
                2,
            ),
            "symbol_typo": (
                "步骤1: x^2 - 5x + 6 = 0\n"
                "步骤2: (x-2)(x-3) = 0\n"
                "步骤3: y = 2 或 y = 3",
                2,
            ),
            # K8 阈值边界：变量差异反例搜索
            "variable_diff_boundary": (
                "步骤1: x^2 - 5x + 6 = 0\n"
                "步骤2: (x-2)(x-3) + 1e-9*x = 0\n"
                "步骤3: x = 2 或 x = 3",
                1,
            ),
        },
    ),
    # ---- 模板2：等式变形 ----
    ProblemTemplate(
        id="T02",
        category="equation",
        problem="解方程 3x + 5 = 2x + 10",
        correct_solution=(
            "步骤1: 3x + 5 = 2x + 10\n"
            "步骤2: 3x - 2x = 10 - 5\n"
            "步骤3: x = 5"
        ),
        final_assertion="x = 5",
        dirty_solutions={
            "divide_by_zero": (
                "步骤1: 3x + 5 = 2x + 10\n"
                "步骤2: 3x - 2x = 10 - 5\n"
                "步骤3: x = 6",
                2,
            ),
            "boundary_omission": (
                "步骤1: 3x + 5 = 2x + 10\n"
                "步骤2: 3x - 2x = 10 - 5\n"
                "步骤3: x = 6",
                2,
            ),
            "symbol_typo": (
                "步骤1: 3x + 5 = 2x + 10\n"
                "步骤2: 3x - 2x = 10 - 5\n"
                "步骤3: y = 5",
                2,
            ),
            # K8 阈值边界：常数差异恰好 1e-9（边界命中）
            "constant_diff_boundary": (
                "步骤1: 3x + 5 = 2x + 10\n"
                "步骤2: 3x - 2x = 10 - 5\n"
                "步骤3: x = 5.000000001",
                2,
            ),
        },
    ),
    # ---- 模板3：因式分解 ----
    ProblemTemplate(
        id="T03",
        category="factorization",
        problem="因式分解 x^2 - 9",
        correct_solution=(
            "步骤1: x^2 - 9 = x^2 - 3^2\n"
            "步骤2: x^2 - 3^2 = (x-3)(x+3)\n"
            "步骤3: x^2 - 9 = (x-3)(x+3)"
        ),
        final_assertion="x^2 - 9 = (x-3)(x+3)",
        dirty_solutions={
            "dimension_mismatch": (
                "步骤1: x^2 - 9 = x^2 - 3^2\n"
                "步骤2: x^2 - 3^2 = (x-3)(x+3)\n"
                "步骤3: x^2 - 9 = (x-3)(x+3) = 0",
                2,
            ),
            "induction_failure": (
                "步骤1: x^2 - 9 = x^2 - 3^2\n"
                "步骤2: x^2 - 3^2 = (x-3)(x+3)\n"
                "步骤3: x^2 - 9 = (x-3)(x+3) = 0",
                2,
            ),
            "illegal_algebra": (
                "步骤1: x^2 - 9 = x^2 - 3^2\n"
                "步骤2: x^2 - 3^2 = (x-3)(x+3)\n"
                "步骤3: x^2 - 9 = (x-3)(x+3) = 0",
                2,
            ),
            # K8 阈值边界：常数差异恰好 1e-9（边界命中）
            "constant_diff_boundary": (
                "步骤1: x^2 - 9 = x^2 - 3^2\n"
                "步骤2: x^2 - 3^2 = (x-3)(x+3)\n"
                "步骤3: x^2 - 9 = (x-3)(x+3) + 1e-9",
                2,
            ),
        },
    ),
    # ---- 模板4：展开 ----
    ProblemTemplate(
        id="T04",
        category="expansion",
        problem="展开 (x+2)(x-3)",
        correct_solution=(
            "步骤1: (x+2)(x-3) = x^2 - 3x + 2x - 6\n"
            "步骤2: x^2 - 3x + 2x - 6 = x^2 - x - 6\n"
            "步骤3: (x+2)(x-3) = x^2 - x - 6"
        ),
        final_assertion="(x+2)(x-3) = x^2 - x - 6",
        dirty_solutions={
            "illegal_algebra": (
                "步骤1: (x+2)(x-3) = x^2 - 3x + 2x - 6\n"
                "步骤2: x^2 - 3x + 2x - 6 = x^2 - x - 6\n"
                "步骤3: (x+2)(x-3) = x^2 - x - 6 = 0",
                2,
            ),
            "divide_by_zero": (
                "步骤1: (x+2)(x-3) = x^2 - 3x + 2x - 6\n"
                "步骤2: x^2 - 3x + 2x - 6 = x^2 - x - 6\n"
                "步骤3: (x+2)(x-3) = x^2 - x - 6 = 0",
                2,
            ),
            "boundary_omission": (
                "步骤1: (x+2)(x-3) = x^2 - 3x + 2x - 6\n"
                "步骤2: x^2 - 3x + 2x - 6 = x^2 - x - 6\n"
                "步骤3: (x+2)(x-3) = x^2 - x - 6 = 0",
                2,
            ),
            # K8 阈值边界：常数差异恰好 1e-9（边界命中）
            "constant_diff_boundary": (
                "步骤1: (x+2)(x-3) = x^2 - 3x + 2x - 6\n"
                "步骤2: x^2 - 3x + 2x - 6 = x^2 - x - 6\n"
                "步骤3: (x+2)(x-3) = x^2 - x - 6 + 1e-9",
                2,
            ),
        },
    ),
    # ---- 模板5：等式验证 ----
    ProblemTemplate(
        id="T05",
        category="verification",
        problem="验证 2(x+3) = 2x + 6",
        correct_solution=(
            "步骤1: 2(x+3) = 2x + 6\n"
            "步骤2: 2x + 6 = 2x + 6\n"
            "步骤3: 2(x+3) = 2x + 6 成立"
        ),
        final_assertion="2(x+3) = 2x + 6",
        dirty_solutions={
            "boundary_omission": (
                "步骤1: 2(x+3) = 2x + 6\n"
                "步骤2: 2x + 6 = 2x + 6\n"
                "步骤3: 2(x+3) = 2x + 7",
                2,
            ),
            "induction_failure": (
                "步骤1: 2(x+3) = 2x + 6\n"
                "步骤2: 2x + 6 = 2x + 6\n"
                "步骤3: 2(x+3) = 2x + 8",
                2,
            ),
            "symbol_typo": (
                "步骤1: 2(x+3) = 2x + 6\n"
                "步骤2: 2x + 6 = 2x + 6\n"
                "步骤3: 2(x+3) = 2x + 9",
                2,
            ),
            # K8 阈值边界：变量差异反例搜索（验证类）
            "variable_diff_boundary": (
                "步骤1: 2(x+3) = 2x + 6\n"
                "步骤2: 2x + 6 = 2x + 6\n"
                "步骤3: 2(x+3) = 2x + 6 + 1e-9*x",
                2,
            ),
        },
    ),
    # ---- 模板6：二次方程求解（不同系数） ----
    ProblemTemplate(
        id="T06",
        category="quadratic",
        problem="解方程 x^2 - 4x + 3 = 0",
        correct_solution=(
            "步骤1: x^2 - 4x + 3 = 0\n"
            "步骤2: (x-1)(x-3) = 0\n"
            "步骤3: x = 1 或 x = 3"
        ),
        final_assertion="x = 1 or x = 3",
        dirty_solutions={
            "illegal_algebra": (
                "步骤1: x^2 - 4x + 3 = 0\n"
                "步骤2: (x-1)(x-3) = 0\n"
                "步骤3: x = 1 - 3 = -2",
                2,
            ),
            "divide_by_zero": (
                "步骤1: x^2 - 4x + 3 = 0\n"
                "步骤2: (x-1)(x-3) = 0\n"
                "步骤3: x = 1 或 x = 4",
                2,
            ),
            "dimension_mismatch": (
                "步骤1: x^2 - 4x + 3 = 0\n"
                "步骤2: (x-1)(x-3) = 0\n"
                "步骤3: x = 1 或 x = 4",
                2,
            ),
            # K8 阈值边界：常数差异恰好 1e-9（边界命中）
            "constant_diff_boundary": (
                "步骤1: x^2 - 4x + 3 = 0\n"
                "步骤2: (x-1)(x-3) = 0\n"
                "步骤3: x = 1 或 x = 3.000000001",
                2,
            ),
        },
    ),
]


# ---------------------------------------------------------------------------
# 生成器
# ---------------------------------------------------------------------------

@dataclass
class GeneratorConfig:
    """生成器配置。"""
    seed: int = 42
    generator_version: str = "1.0.0"
    clean_cases: int = 3
    # 各错误类型最低覆盖项数（与 error_types.json 一致）
    # 新增：constant_diff_boundary（K8 阈值边界）、variable_diff_boundary（反例搜索阈值边界）
    min_coverage: dict[str, int] = field(default_factory=lambda: {
        "illegal_algebra": 3,
        "divide_by_zero": 3,
        "dimension_mismatch": 2,
        "induction_failure": 2,
        "boundary_omission": 2,
        "symbol_typo": 3,
        "constant_diff_boundary": 2,  # K8: 常数差异阈值边界（1e-9）
        "variable_diff_boundary": 1,  # K8: 变量差异反例搜索阈值边界
    })


class BenchmarkGenerator:
    """合成基准用例生成器。"""

    def __init__(self, config: GeneratorConfig | None = None):
        self.config = config or GeneratorConfig()
        self._rng = random.Random(self.config.seed)
        self._case_id = 0

    def _next_id(self) -> str:
        self._case_id += 1
        return f"BENCH-{self._case_id:03d}"

    def generate_clean(self, template: ProblemTemplate) -> BenchmarkCase:
        """生成干净用例。"""
        return BenchmarkCase(
            id=self._next_id(),
            input={
                "problem": template.problem,
                "solution": template.correct_solution,
                "format": "text",
            },
            expect={
                "is_clean": True,
                "first_error_step": None,
                "error_type": None,
                "error_count": 0,
            },
            meta={
                "generator_version": self.config.generator_version,
                "seed": self.config.seed,
                "error_injected": False,
                "template_id": template.id,
                "category": template.category,
            },
        )

    def generate_dirty(
        self, template: ProblemTemplate, error_type: str
    ) -> BenchmarkCase:
        """生成含错用例。"""
        dirty_info = template.dirty_solutions.get(error_type)
        if dirty_info is None:
            raise ValueError(
                f"模板 {template.id} 无 {error_type} 的含错解答"
            )

        injected_solution, first_error_step = dirty_info

        return BenchmarkCase(
            id=self._next_id(),
            input={
                "problem": template.problem,
                "solution": injected_solution,
                "format": "text",
            },
            expect={
                "is_clean": False,
                "first_error_step": first_error_step,
                "error_type": error_type,
                "error_count": 1,
            },
            meta={
                "generator_version": self.config.generator_version,
                "seed": self.config.seed,
                "error_injected": True,
                "injection_method": f"{error_type}: pre-baked",
                "template_id": template.id,
                "category": template.category,
            },
        )

    def generate_all(self) -> list[BenchmarkCase]:
        """生成全部基准用例。

        策略：
        - 3 条干净解答（从 6 个模板中选 3 个）
        - 各错误类型按最低覆盖项数生成含错解答
        """
        cases: list[BenchmarkCase] = []

        # 干净用例：选 3 个不同模板
        clean_templates = self._rng.sample(TEMPLATES, self.config.clean_cases)
        for t in clean_templates:
            cases.append(self.generate_clean(t))

        # 含错用例：按最低覆盖项数
        for error_type, min_count in self.config.min_coverage.items():
            # 选 min_count 个不同模板来植入该错误
            available = [
                t for t in TEMPLATES
                if error_type in t.dirty_solutions and t not in clean_templates
            ]
            if len(available) < min_count:
                # 不够则复用所有有该错误类型的模板
                available = [
                    t for t in TEMPLATES
                    if error_type in t.dirty_solutions
                ]
            selected = self._rng.sample(available, min_count)
            for t in selected:
                cases.append(self.generate_dirty(t, error_type))

        return cases

    def check_coverage(self, cases: list[BenchmarkCase]) -> set[str]:
        """覆盖度守门（K9）：返回未覆盖的错误类型集合。

        分母反射自代码常量（min_coverage），不手写。
        """
        covered_types = {
            c.expect["error_type"] for c in cases if not c.expect["is_clean"]
        }
        missing = set(self.config.min_coverage.keys()) - covered_types
        return missing


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

def generate_benchmark(output_dir: str | None = None) -> list[BenchmarkCase]:
    """生成基准用例并可选写入目录。

    Args:
        output_dir: 若提供，将用例写入 {output_dir}/benchmarks/ 目录。

    Returns:
        生成的用例列表。
    """
    import os
    from pathlib import Path

    gen = BenchmarkGenerator()
    cases = gen.generate_all()

    # 覆盖度守门
    missing = gen.check_coverage(cases)
    if missing:
        raise CoverageError(
            f"以下错误类型无用例: {missing}。"
            f"最低覆盖项数: {gen.config.min_coverage}"
        )

    if output_dir:
        out_path = Path(output_dir)
        bench_dir = out_path / "benchmarks"
        bench_dir.mkdir(parents=True, exist_ok=True)

        # 写索引文件
        index = {"version": "1.0.0", "case_ids": [c.id for c in cases]}
        (bench_dir / "_index.json").write_text(
            json.dumps(index, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # 写各用例
        for case in cases:
            (bench_dir / f"{case.id}.json").write_text(
                case.to_json(), encoding="utf-8"
            )

    return cases


class CoverageError(Exception):
    """覆盖度不足异常。"""


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    cases = generate_benchmark()
    print(f"生成 {len(cases)} 条基准用例:")
    for c in cases:
        status = "clean" if c.expect["is_clean"] else c.expect["error_type"]
        print(f"  {c.id}: {status} (template={c.meta['template_id']})")

    # 覆盖度报告
    gen = BenchmarkGenerator()
    missing = gen.check_coverage(cases)
    if missing:
        print(f"\n⚠ 覆盖度不足: {missing}")
        sys.exit(1)
    else:
        print("\n✅ 覆盖度守门通过")
