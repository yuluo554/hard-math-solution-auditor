"""CLI 退出码语义守门测试。

退出码三语义（锁进测试，防"静默变更契约"）：
- 0 = 成功（干净解答 / 基准达标 / 自检通过）
- 1 = 检出问题（解答含错 / 基准未达标 / 台账漂移）
- 2 = 用法与输入不可用（缺文件 / 未知名 / 参数缺失）

另有冻结态自检的真实性守门：selftest 必须**真跑引擎**，
不能是 `return True` 占位（占位会让"自检通过"变成空话）。
"""

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src"
SAMPLES = REPO_ROOT / "data" / "samples"

sys.path.insert(0, str(SRC))


def _run_cli(*argv):
    """以子进程形态跑 CLI，取真实退出码。"""
    return subprocess.run(
        [sys.executable, "-m", "hws_math_auditor", *argv],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


class TestExitCodeSemantics:
    def test_selftest_exit_0(self):
        """自检通过 → 0。"""
        r = _run_cli("selftest")
        assert r.returncode == 0, r.stdout + r.stderr

    def test_benchmark_run_exit_0(self):
        """基准达标 → 0。"""
        r = _run_cli("benchmark", "--run")
        assert r.returncode == 0, r.stdout + r.stderr

    def test_benchmark_metrics_exit_0(self):
        """指标输出 → 0，且是合法 JSON。"""
        import json

        r = _run_cli("benchmark", "--metrics")
        assert r.returncode == 0, r.stdout + r.stderr
        data = json.loads(r.stdout)
        assert data["total_cases"] == 21
        assert data["false_positive_rate"] == 0.0

    def test_benchmark_no_flag_exit_2(self):
        """缺必需旗标 → 2（用法错误）。"""
        r = _run_cli("benchmark")
        assert r.returncode == 2, r.stdout + r.stderr

    def test_audit_clean_exit_0(self):
        """干净解答 → 0。"""
        r = _run_cli("audit", "--input", str(SAMPLES / "clean_solution.txt"))
        assert r.returncode == 0, r.stdout + r.stderr

    def test_audit_dirty_exit_1(self):
        """含错解答 → 1（检出错误）。"""
        r = _run_cli("audit", "--input", str(SAMPLES / "dirty_solution.txt"))
        assert r.returncode == 1, r.stdout + r.stderr

    def test_audit_missing_file_exit_2(self):
        """文件不存在 → 2（输入不可用）。"""
        r = _run_cli("audit", "--input", "no/such/file.txt")
        assert r.returncode == 2, r.stdout + r.stderr

    def test_audit_unknown_encoding_exit_2(self):
        """未知编码名 → 2（输入不可用，不猜测）。"""
        r = _run_cli(
            "audit",
            "--input",
            str(SAMPLES / "clean_solution.txt"),
            "--encoding",
            "no-such-codec",
        )
        assert r.returncode == 2, r.stdout + r.stderr


class TestSelftestIsReal:
    """自检必须真跑引擎，不能是占位实现。"""

    def test_selftest_detects_broken_engine(self, monkeypatch):
        """变异验证：引擎坏了（恒判 ok）→ selftest 必须失败。

        若 selftest 是 `return True` 占位，这条会红。
        """
        from hws_math_auditor import pipeline, verifier
        from hws_math_auditor.model import Verdict

        def broken_verify_step(prev, curr):
            return Verdict("ok", "broken: always ok", None)

        monkeypatch.setattr(verifier, "verify_step", broken_verify_step)
        # pipeline 内部按名调用 verify_all → verify_step，需同时打 verify_all 消费点
        monkeypatch.setattr(
            pipeline, "verify_all", lambda steps: [Verdict("ok", "broken", None)] * len(steps)
        )

        assert pipeline.selftest() is False, (
            "引擎被替换为恒判 ok 后 selftest 仍通过 = 占位自检（假门）"
        )

    def test_selftest_passes_on_healthy_engine(self):
        """阳性对照：健康引擎下 selftest 必须通过。"""
        from hws_math_auditor import pipeline

        assert pipeline.selftest() is True
