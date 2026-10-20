"""基准模块测试。"""

from hws_math_auditor.benchmark import (
    BenchmarkGenerator,
    run_benchmark,
)


class TestBenchmarkGenerator:
    """生成器测试。"""

    def test_generate_all_count(self):
        """生成 21 条用例（3 干净 + 18 含错）。"""
        gen = BenchmarkGenerator()
        cases = gen.generate_all()
        assert len(cases) == 21

    def test_clean_cases(self):
        """3 条干净解答。"""
        gen = BenchmarkGenerator()
        cases = gen.generate_all()
        clean = [c for c in cases if c.expect["is_clean"]]
        assert len(clean) == 3

    def test_dirty_cases(self):
        """18 条含错解答。"""
        gen = BenchmarkGenerator()
        cases = gen.generate_all()
        dirty = [c for c in cases if not c.expect["is_clean"]]
        assert len(dirty) == 18

    def test_coverage_gate(self):
        """覆盖度守门：所有错误类型均有用例。"""
        gen = BenchmarkGenerator()
        cases = gen.generate_all()
        missing = gen.check_coverage(cases)
        assert missing == set(), f"未覆盖的错误类型: {missing}"

    def test_min_coverage_per_type(self):
        """各错误类型最低覆盖项数。"""
        gen = BenchmarkGenerator()
        cases = gen.generate_all()

        for error_type, min_count in gen.config.min_coverage.items():
            count = sum(
                1 for c in cases
                if not c.expect["is_clean"] and c.expect["error_type"] == error_type
            )
            assert count >= min_count, (
                f"{error_type} 只有 {count} 条，最低需要 {min_count} 条"
            )


class TestBenchmarkRunner:
    """Runner 测试。"""

    def test_run_benchmark(self):
        """运行基准套件。"""
        gen = BenchmarkGenerator()
        cases = gen.generate_all()
        results, metrics = run_benchmark(cases)

        assert len(results) == len(cases)
        assert metrics.total_cases == len(cases)

    def test_false_positive_rate(self):
        """误报率应为 0。"""
        gen = BenchmarkGenerator()
        cases = gen.generate_all()
        _, metrics = run_benchmark(cases)
        assert metrics.false_positive_rate == 0.0

    def test_localization_accuracy(self):
        """定位准确率应为 100%。"""
        gen = BenchmarkGenerator()
        cases = gen.generate_all()
        _, metrics = run_benchmark(cases)
        assert metrics.localization_accuracy == 1.0

    def test_coverage_report(self):
        """覆盖度报告。"""
        gen = BenchmarkGenerator()
        cases = gen.generate_all()
        _, metrics = run_benchmark(cases)

        # metrics.coverage 本身就是覆盖度报告
        for et, info in metrics.coverage.items():
            assert info["met"], f"{et} 覆盖度未达标: {info}"


class TestGroundTruth:
    """真值台账测试。"""

    def test_benchmark_files_exist(self):
        """基准文件存在。"""
        from pathlib import Path
        bench_dir = Path("data/benchmarks")
        assert bench_dir.exists()

        files = list(bench_dir.glob("BENCH-*.json"))
        assert len(files) >= 18

    def test_benchmark_file_format(self):
        """基准文件格式正确。"""
        import json
        from pathlib import Path

        bench_dir = Path("data/benchmarks")
        for f in bench_dir.glob("BENCH-*.json"):
            data = json.loads(f.read_text(encoding="utf-8"))
            assert "id" in data
            assert "input" in data
            assert "expect" in data
            assert "meta" in data
            assert "problem" in data["input"]
            assert "solution" in data["input"]
            assert "is_clean" in data["expect"]


class TestSnapshots:
    """快照测试。"""

    def test_snapshots_exist(self):
        """快照文件存在。"""
        from pathlib import Path
        snap_dir = Path("data/snapshots")
        assert snap_dir.exists()

        files = list(snap_dir.glob("BENCH-*.json"))
        assert len(files) >= 18

    def test_snapshot_sha256(self):
        """快照含 sha256 留档。"""
        import json
        from pathlib import Path

        snap_dir = Path("data/snapshots")
        for f in snap_dir.glob("BENCH-*.json"):
            data = json.loads(f.read_text(encoding="utf-8"))
            assert "sha256" in data
            assert len(data["sha256"]) == 64

    def test_snapshot_model_info(self):
        """快照含模型信息。"""
        import json
        from pathlib import Path

        snap_dir = Path("data/snapshots")
        for f in snap_dir.glob("BENCH-*.json"):
            data = json.loads(f.read_text(encoding="utf-8"))
            assert "model" in data
            assert "name" in data["model"]
            assert "version" in data["model"]
