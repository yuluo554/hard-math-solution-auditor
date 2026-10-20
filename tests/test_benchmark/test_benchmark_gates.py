"""基准套件守门测试：探活 + 冻结台账位级一致 + 台账纪律。

三条铁律（缺一即退化成假门）：
1. **探活可证伪**：注入坏 verifier → 基准必须报未达标；
2. **冻结台账 = 生成器产物**：再生成位级一致，防手改台账；
3. **真值库只存 input+expect**：出现 observed 字段即红（K3）。
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from hws_math_auditor.benchmark.generator import (  # noqa: E402
    BenchmarkGenerator,
    check_frozen_ledger,
)
from hws_math_auditor.benchmark.runner import (  # noqa: E402
    load_ground_truth,
    probe_broken_implementation,
    run_benchmark,
)

BENCH_DIR = REPO_ROOT / "data" / "benchmarks"


class TestProbe:
    """探活：坏实现必须暴露（可证伪门）。"""

    def test_broken_verifier_is_exposed(self):
        """注入"永远返回 ok"的 verifier，基准必须报未达标。

        这条打的是**消费处**（runner 实际调用的 verify_step 引用），
        不是定义处——打定义处不生效。
        """
        exposed = probe_broken_implementation()
        assert exposed, (
            "坏实现未被暴露：基准在 verify_step 恒返回 ok 时仍全绿 = 假门"
        )

    def test_good_verifier_passes(self):
        """阳性对照：好实现下基准必须达标（否则探活无意义）。"""
        cases = load_ground_truth(BENCH_DIR)
        _, metrics = run_benchmark(cases)
        assert metrics.false_positive_rate == 0.0
        assert metrics.localization_accuracy == 1.0


class TestFrozenLedger:
    """冻结真值台账纪律。"""

    def test_ledger_matches_regeneration(self):
        """台账必须与再生成位级一致（禁手改守门）。"""
        problems = check_frozen_ledger(BENCH_DIR)
        assert problems == [], f"冻结台账漂移: {problems}"

    def test_ledger_drift_is_detected(self, tmp_path):
        """变异验证：手改台账必须被抓出。"""
        # 复制一份台账再改一条
        import shutil

        dst = tmp_path / "benchmarks"
        shutil.copytree(BENCH_DIR, dst)
        target = sorted(dst.glob("BENCH-*.json"))[0]
        data = json.loads(target.read_text(encoding="utf-8"))
        data["expect"]["is_clean"] = not data["expect"]["is_clean"]
        target.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        problems = check_frozen_ledger(dst)
        assert problems, "手改台账未被检出 = 假门"

    def test_ledger_missing_case_is_detected(self, tmp_path):
        """变异验证：台账缺条目必须被抓出。"""
        import shutil

        dst = tmp_path / "benchmarks"
        shutil.copytree(BENCH_DIR, dst)
        victim = sorted(dst.glob("BENCH-*.json"))[0]
        victim.unlink()

        problems = check_frozen_ledger(dst)
        assert any("缺失用例" in p for p in problems), f"缺条目未检出: {problems}"

    def test_ledger_count_matches_generator(self):
        """台账条目数必须等于生成器产出数（防"悄悄做小分母"）。"""
        gen = BenchmarkGenerator()
        cases = gen.generate_all()
        frozen = list(BENCH_DIR.glob("BENCH-*.json"))
        assert len(frozen) == len(cases), (
            f"台账 {len(frozen)} 条 vs 生成器 {len(cases)} 条不一致"
        )

    def test_no_observed_field_in_ledger(self):
        """K3：真值库只存 input+expect，不得出现 observed。"""
        for f in BENCH_DIR.glob("BENCH-*.json"):
            data = json.loads(f.read_text(encoding="utf-8"))
            assert "observed" not in data, f"{f.name} 含 observed 字段（违反 K3）"
            assert "observed" not in data.get("expect", {}), (
                f"{f.name}.expect 含 observed 字段（违反 K3）"
            )

    def test_index_matches_files(self):
        """_index.json 的 case_ids 必须与台账文件一一对应。"""
        index = json.loads((BENCH_DIR / "_index.json").read_text(encoding="utf-8"))
        files = sorted(f.stem for f in BENCH_DIR.glob("BENCH-*.json"))
        assert sorted(index["case_ids"]) == files, "索引与台账文件不一致"


class TestSnapshotIntegrity:
    """快照 sha256 自洽（K10）。"""

    def test_snapshot_sha256_matches_output(self):
        """快照 sha256 必须等于其 output 字段的实算哈希。"""
        import hashlib

        snap_dir = REPO_ROOT / "data" / "snapshots"
        files = sorted(snap_dir.glob("BENCH-*.json"))
        assert len(files) >= 21, f"快照仅 {len(files)} 条"

        for f in files:
            data = json.loads(f.read_text(encoding="utf-8"))
            payload = json.dumps(data["output"], ensure_ascii=False, indent=2)
            actual = hashlib.sha256(payload.encode("utf-8")).hexdigest()
            assert actual == data["sha256"], f"{f.name} sha256 与 output 不符（快照漂移）"

    def test_snapshot_ids_match_ledger(self):
        """快照 id 集合必须与台账 id 集合一致。"""
        snap_dir = REPO_ROOT / "data" / "snapshots"
        snap_ids = sorted(f.stem for f in snap_dir.glob("BENCH-*.json"))
        bench_ids = sorted(f.stem for f in BENCH_DIR.glob("BENCH-*.json"))
        assert snap_ids == bench_ids, "快照与台账 id 集合不一致"
