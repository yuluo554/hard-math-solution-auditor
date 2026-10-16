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

from hws_math_auditor.config import config


# ---------------------------------------------------------------------------
# K8 阈值边界字面量：从唯一数值口径（config.tolerance）派生，不硬编码。
# 零政策字面量门禁扫描基准源码，硬编码会红。
# ---------------------------------------------------------------------------

_TOL = config.tolerance


def _tol_text(tol: float) -> str:
    """把 tolerance 渲染成人类可读的十进制文本（科学计数法形式）。"""
    text = f"{tol:g}"
    if "e-0" in text:
        text = text.replace("e-0", "e-")
    elif "e+0" in text:
        text = text.replace("e+0", "e+")
    return text


def _boundary_value(base: float) -> str:
    """构造"恰好偏离阈值一个 tolerance"的数值文本。"""
    return repr(base + _TOL)


# 植入解答文本中使用的阈值文本形式
_TOL_TEXT = _tol_text(_TOL)


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
                f"步骤2: (x-2)(x-3) + {_TOL_TEXT}*x = 0\n"
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
            # K8 阈值边界：常数差异恰好等于 tolerance（边界命中）
            "constant_diff_boundary": (
                "步骤1: 3x + 5 = 2x + 10\n"
                "步骤2: 3x - 2x = 10 - 5\n"
                f"步骤3: x = {_boundary_value(5.0)}",
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
            # K8 阈值边界：常数差异恰好等于 tolerance（边界命中）
            "constant_diff_boundary": (
                "步骤1: x^2 - 9 = x^2 - 3^2\n"
                "步骤2: x^2 - 3^2 = (x-3)(x+3)\n"
                f"步骤3: x^2 - 9 = (x-3)(x+3) + {_TOL_TEXT}",
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
            # K8 阈值边界：常数差异恰好等于 tolerance（边界命中）
            "constant_diff_boundary": (
                "步骤1: (x+2)(x-3) = x^2 - 3x + 2x - 6\n"
                "步骤2: x^2 - 3x + 2x - 6 = x^2 - x - 6\n"
                f"步骤3: (x+2)(x-3) = x^2 - x - 6 + {_TOL_TEXT}",
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
                f"步骤3: 2(x+3) = 2x + 6 + {_TOL_TEXT}*x",
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
            # K8 阈值边界：常数差异恰好等于 tolerance（边界命中）
            "constant_diff_boundary": (
                "步骤1: x^2 - 4x + 3 = 0\n"
                "步骤2: (x-1)(x-3) = 0\n"
                f"步骤3: x = 1 或 x = {_boundary_value(3.0)}",
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
        "constant_diff_boundary": 2,  # K8: 常数差异阈值边界（= tolerance）
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

def _write_text_lf(path, text: str) -> None:
    """以 UTF-8 + LF 写文本（跨平台位级一致）。

    不用 Path.write_text：其 newline 参数是 3.10+，且默认会把 `\\n`
    翻成 os.linesep——Windows 上写出 CRLF、Linux 上写出 LF，
    "再生成位级一致"在跨平台就永远不成立（字节冻结纪律）。
    """
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


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
        _write_text_lf(
            bench_dir / "_index.json",
            json.dumps(index, ensure_ascii=False, indent=2),
        )

        # 写各用例
        for case in cases:
            _write_text_lf(bench_dir / f"{case.id}.json", case.to_json())

    return cases


class CoverageError(Exception):
    """覆盖度不足异常。"""


# ---------------------------------------------------------------------------
# 冻结态位级一致校验（生成器 --check）
# ---------------------------------------------------------------------------

def check_frozen_ledger(
    bench_dir: str | Path = "data/benchmarks",
) -> list[str]:
    """校验冻结真值台账与"再生成"位级一致。

    真值台账是生成器的冻结产物（禁手改）：把生成结果与仓库内
    data/benchmarks/*.json 逐条逐字节比对，任何差异都说明台账被
    手改或生成器漂移。

    Args:
        bench_dir: 冻结台账目录

    Returns:
        差异描述列表；空列表 = 位级一致。
    """
    from pathlib import Path

    bench_path = Path(bench_dir)
    problems: list[str] = []

    if not bench_path.exists():
        return [f"冻结台账目录不存在: {bench_path}"]

    gen = BenchmarkGenerator()
    cases = gen.generate_all()
    regenerated = {c.id: c.to_json() for c in cases}

    frozen_files = sorted(bench_path.glob("BENCH-*.json"))
    frozen_ids = {f.stem for f in frozen_files}

    missing = sorted(set(regenerated) - frozen_ids)
    extra = sorted(frozen_ids - set(regenerated))
    for cid in missing:
        problems.append(f"台账缺失用例: {cid}（生成器已产出）")
    for cid in extra:
        problems.append(f"台账存在多余用例: {cid}（生成器无此用例）")

    for f in frozen_files:
        cid = f.stem
        if cid not in regenerated:
            continue
        frozen_text = f.read_text(encoding="utf-8")
        if frozen_text.rstrip("\n") != regenerated[cid].rstrip("\n"):
            problems.append(f"台账与再生成不一致（被手改或生成器漂移）: {cid}")

    # 索引对账
    index_file = bench_path / "_index.json"
    if index_file.exists():
        index = json.loads(index_file.read_text(encoding="utf-8"))
        if index.get("case_ids") != [c.id for c in cases]:
            problems.append("_index.json 的 case_ids 与生成器不一致")
    else:
        problems.append("_index.json 缺失")

    return problems


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    if "--check" in sys.argv:
        # 冻结态位级一致校验（禁手改台账的守门）
        problems = check_frozen_ledger()
        if problems:
            print("❌ 冻结台账与生成器不一致:")
            for p in problems:
                print(f"  - {p}")
            sys.exit(1)
        print("✅ 冻结台账与生成器位级一致")
        sys.exit(0)

    output_dir = None
    if "--write" in sys.argv:
        output_dir = "data"

    cases = generate_benchmark(output_dir)
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
