"""模块⑤：内置基准（零模型依赖，离线可复跑）。"""

from hws_math_auditor.benchmark.generator import (
    BenchmarkCase,
    BenchmarkGenerator,
    CoverageError,
    GeneratorConfig,
    generate_benchmark,
)
from hws_math_auditor.benchmark.runner import (
    BenchmarkResult,
    Metrics,
    run_benchmark,
)
from hws_math_auditor.benchmark.snapshot import (
    generate_all_snapshots,
    generate_snapshot,
)

__all__ = [
    "BenchmarkCase",
    "BenchmarkGenerator",
    "CoverageError",
    "GeneratorConfig",
    "generate_benchmark",
    "BenchmarkResult",
    "Metrics",
    "run_benchmark",
    "generate_snapshot",
    "generate_all_snapshots",
]
