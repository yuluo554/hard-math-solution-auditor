"""CLI 退出码语义守门测试。

退出码三语义（锁进测试，防"静默变更契约"）：
- 0 = 成功（干净解答 / 基准达标 / 自检通过）
- 1 = 检出问题（解答含错 / 基准未达标 / 台账漂移）
- 2 = 用法与输入不可用（缺文件 / 未知名 / 参数缺失）

另有冻结态自检的真实性守门：selftest 必须**真跑引擎**，
不能是 `return True` 占位（占位会让"自检通过"变成空话）。
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src"
SAMPLES = REPO_ROOT / "data" / "samples"

sys.path.insert(0, str(SRC))


def _run_cli(*argv, env_extra=None):
    """以子进程形态跑 CLI，取真实退出码。"""
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, "-m", "hws_math_auditor", *argv],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )


def _broken_verifier_env(tmp_path) -> dict:
    """构造一个把 verify_step 注入成恒 `ok` 的子进程环境。

    用 `sitecustomize.py`（`site` 模块在解释器启动时自动导入）而不是给生产代码
    加探针开关——**生产代码不得为测试开后门**。PYTHONPATH 只把这一层注入脚本
    放进 sys.path，包本体仍从安装面解析。
    """
    site_dir = Path(tmp_path) / "broken_site"
    site_dir.mkdir()
    (site_dir / "sitecustomize.py").write_text(
        "from hws_math_auditor import verifier\n"
        "from hws_math_auditor.model import Verdict\n"
        "\n"
        "def _broken_verify_step(prev_expr, curr_expr):\n"
        "    return Verdict('ok', 'injected: always ok', None)\n"
        "\n"
        "verifier.verify_step = _broken_verify_step\n",
        encoding="utf-8",
    )
    py_path = os.pathsep.join(
        [str(site_dir)] + ([os.environ["PYTHONPATH"]] if os.environ.get("PYTHONPATH") else [])
    )
    return {"PYTHONPATH": py_path}



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


class TestBenchmarkExitCodeIsReal:
    """基准退出码必须承认真实结果（D1）。

    阳性对照（好实现 exit 0）在 TestExitCodeSemantics 里；这里只补
    **负控**——把 verify_step 注入成恒 `ok` 后，CLI 必须 exit 1。
    没有这一条，"基准未达标 → 1" 就只是 README 上的一句话。
    """

    def test_broken_engine_benchmark_run_exits_nonzero(self, tmp_path):
        """坏实现 → benchmark --run 必须 exit≠0（当前 D1 是 exit 0）。"""
        env_extra = _broken_verifier_env(tmp_path)
        r = _run_cli("benchmark", "--run", env_extra=env_extra)
        assert r.returncode == 1, (
            f"注入恒 ok 的 verifier 后 benchmark --run 仍 exit {r.returncode}"
            f"（退出码不认结果 = D1 未修）\n{r.stdout}{r.stderr}"
        )
        # 结果必须真变红：18 条含错用例全部 failed
        assert "passed=False" in r.stdout, r.stdout

    def test_broken_engine_benchmark_metrics_exits_nonzero(self, tmp_path):
        """坏实现 → benchmark --metrics 必须 exit≠0（当前 D1 是 return 0）。"""
        env_extra = _broken_verifier_env(tmp_path)
        r = _run_cli("benchmark", "--metrics", env_extra=env_extra)
        assert r.returncode == 1, (
            f"注入恒 ok 的 verifier 后 benchmark --metrics 仍 exit {r.returncode}\n"
            f"{r.stdout}{r.stderr}"
        )
        metrics = json.loads(r.stdout)
        assert metrics["localization_accuracy"] < 1.0, metrics

    def test_injection_actually_reached_the_engine(self, tmp_path):
        """注入面自证：坏 verifier 必须真生效，否则上面两条是空测。

        判据 = 同一环境下含错解不再被检出（`audit` 由 exit 1 变 exit 0）。
        """
        env_extra = _broken_verifier_env(tmp_path)
        healthy = _run_cli("audit", "--input", str(SAMPLES / "dirty_solution.txt"))
        assert healthy.returncode == 1, "阳性对照失效：健康引擎未检出含错解"
        broken = _run_cli(
            "audit", "--input", str(SAMPLES / "dirty_solution.txt"), env_extra=env_extra
        )
        assert broken.returncode == 0, (
            f"注入未生效（含错解仍 exit {broken.returncode}）——负控是空测\n"
            f"{broken.stdout}{broken.stderr}"
        )


class TestDataUnavailableIsExit2:
    """数据缺失必须映射到退出码 2，且不得抛 traceback（D2/D10）。

    "缺数据"与"解答含错"是两件事：前者是环境不可用（2），后者是检出问题（1）。
    压成同一个码会让用户无法分辨，而 traceback 更是把用法错误伪装成崩溃。
    """

    def _run_without_data(self, tmp_path, *argv):
        """把包内的数据目录整体藏起来后跑 CLI。

        做法：复制一份源码树到 tmp，删掉 `data/`（源码态）与 `_data/`（装态），
        再以 `PYTHONPATH` 指向这份树 —— 生产代码不需要任何测试开关。
        """
        import shutil

        tree = tmp_path / "tree"
        shutil.copytree(
            SRC,
            tree / "src",
            ignore=shutil.ignore_patterns("__pycache__", "_data"),
        )
        env_extra = {
            "PYTHONPATH": os.pathsep.join(
                [str(tree / "src")]
                + ([os.environ["PYTHONPATH"]] if os.environ.get("PYTHONPATH") else [])
            )
        }
        return _run_cli(*argv, env_extra=env_extra)

    @pytest.mark.parametrize(
        "argv",
        [
            ("selftest",),
            ("benchmark", "--run"),
            ("benchmark", "--metrics"),
            ("audit", "--input", str(SAMPLES / "clean_solution.txt")),
        ],
        ids=["selftest", "benchmark-run", "benchmark-metrics", "audit"],
    )
    def test_missing_data_exits_2_without_traceback(self, tmp_path, argv):
        r = self._run_without_data(tmp_path, *argv)
        assert r.returncode == 2, (
            f"{argv[0]} 在数据缺失时 exit {r.returncode}（期望 2）\n{r.stdout}{r.stderr}"
        )
        assert "Traceback" not in r.stdout + r.stderr, (
            f"{argv[0]} 在数据缺失时抛了 traceback（应给友好提示）"
        )
        assert "随包数据不可用" in r.stdout, r.stdout

    def test_healthy_tree_still_exits_0(self, tmp_path):
        """阳性对照：同一套夹具、数据完整时必须 exit 0（证明差异来自数据不是夹具）。"""
        r = _run_cli("selftest")
        assert r.returncode == 0, r.stdout + r.stderr


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
