"""零政策字面量门禁的回归测试。

守门三件事（缺一即退化成假门）：
1. **扫描面非空**——路径解析错导致的静默空扫绝不能判为通过；
2. **真能抓到**——往受扫目录注入政策字面量必须变红（变异验证）；
3. **豁免口径精确**——只有 config.py 与 tests/ 豁免，其余源码一律受管。
"""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from hws_math_auditor.rules import (  # noqa: E402
    check_zero_literal_gate,
    project_root,
    scan_for_policy_literals,
    _iter_scanned_files,
)


def test_project_root_is_repo_root():
    """project_root() 必须解析到仓库根（含 src/ 与 tests/）。

    这条防的是"路径少退一级"——曾出现过 base_path 落到 src/ 下，
    导致所有 SCAN_DIRS 都不存在、扫描静默返回 0 违规的假门。
    """
    root = project_root()
    assert (root / "src" / "hws_math_auditor").is_dir(), f"src 包目录不在 {root} 下"
    assert (root / "tests").is_dir(), f"tests 目录不在 {root} 下"


def test_scan_surface_is_not_empty():
    """扫描面必须非空——空扫描面绝不能冒充"无违规"。"""
    files = _iter_scanned_files(project_root())
    assert len(files) >= 20, f"扫描面仅 {len(files)} 个文件，疑似路径解析错误"


def test_gate_passes_on_real_repo():
    """真实仓库当前必须通过门禁（K8 单一定义点已落实）。"""
    passed, violations = check_zero_literal_gate()
    assert passed, f"门禁未通过: {violations}"


def test_gate_fails_on_empty_scan_surface(tmp_path):
    """变异验证：扫描面为空必须判**不通过**，而不是静默通过。"""
    passed, violations = check_zero_literal_gate(tmp_path)
    assert not passed, "空扫描面被误判为通过 = 假门"
    assert violations and "扫描面为空" in violations[0]["content"]


def test_gate_detects_injected_literal(tmp_path):
    """变异验证：向受扫目录注入政策字面量必须变红。"""
    pkg = tmp_path / "src" / "hws_math_auditor"
    pkg.mkdir(parents=True)
    # 用拼接构造被测字面量，避免测试自身源码携带政策数值
    literal = "1e" + "-9"
    (pkg / "offender.py").write_text(f"THRESHOLD = {literal}\n", encoding="utf-8")

    passed, violations = check_zero_literal_gate(tmp_path)
    assert not passed, "注入的政策字面量未被检出 = 假门"
    assert any("offender.py" in v["file"] for v in violations)


def test_config_py_is_exempt(tmp_path):
    """config.py 是 K8 唯一定义点，必须豁免。"""
    pkg = tmp_path / "src" / "hws_math_auditor"
    pkg.mkdir(parents=True)
    literal = "1e" + "-9"
    (pkg / "config.py").write_text(f"TOLERANCE = {literal}\n", encoding="utf-8")
    # 至少要有另一个非豁免文件，避免撞上"扫描面为空"分支
    (pkg / "other.py").write_text("x = 1\n", encoding="utf-8")

    violations = scan_for_policy_literals(tmp_path)
    assert not any("config.py" in v["file"] for v in violations), (
        "config.py 应豁免于政策字面量门禁"
    )


def test_tests_dir_is_exempt(tmp_path):
    """tests/ 目录豁免（测试夹具需内嵌字面量做变异验证）。"""
    tdir = tmp_path / "tests"
    tdir.mkdir(parents=True)
    literal = "1e" + "-9"
    (tdir / "test_x.py").write_text(f"assert {literal} == 0\n", encoding="utf-8")
    pkg = tmp_path / "src" / "hws_math_auditor"
    pkg.mkdir(parents=True)
    (pkg / "clean.py").write_text("x = 1\n", encoding="utf-8")

    violations = scan_for_policy_literals(tmp_path)
    assert not any(v["file"].startswith("tests") for v in violations)


def test_recalc_has_no_second_tolerance_definition():
    """K8：recalc 不得有第二份 tolerance 字面量定义（只能别名 config）。"""
    recalc_src = (REPO_ROOT / "src" / "hws_math_auditor" / "recalc" / "__init__.py").read_text(
        encoding="utf-8"
    )
    literal = "1e" + "-9"
    assert literal not in recalc_src, "recalc 出现第二份数值口径字面量（违反 K8）"
    assert "config.tolerance" in recalc_src, "recalc 应从 config.tolerance 取值"
