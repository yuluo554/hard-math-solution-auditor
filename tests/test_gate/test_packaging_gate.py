"""打包配置与内嵌数据白名单守门测试。

三条纪律：
1. **入包集合 == 白名单**（等式，不只查漏拷）——spec 的 datas 必须与
   声明的白名单一一对应，且不含禁入项；
2. **spec 不写死本机路径**——用 SPECPATH 反推项目根（否则换机/克隆即崩）；
3. **入口是绝对导入的薄模块且有 __main__**——相对导入会让 exe 一启动就
   ImportError，而**构建仍 exit 0**（静默失败）。
"""

import ast
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS = REPO_ROOT / "tools"

# 打包白名单（入包数据），与 plan/05 第三节一致
WHITELIST = {"snapshots", "benchmarks", "rules", "samples"}
# 禁入项
FORBIDDEN = {"_private", "dist", "build", "__pycache__"}


def _spec_text(name: str) -> str:
    return (TOOLS / name).read_text(encoding="utf-8")


@pytest.mark.parametrize("spec", ["pyinstaller-cli.spec", "pyinstaller-gui.spec"])
class TestSpec:
    def test_no_hardcoded_machine_path(self, spec):
        """spec 不得写死本机盘符路径（换机即崩）。"""
        text = _spec_text(spec)
        assert not re.search(r'Path\(\s*r?"[A-Za-z]:[\\/]', text), (
            f"{spec} 写死了本机绝对路径"
        )
        assert "SPECPATH" in text, f"{spec} 应从 SPECPATH 反推项目根"

    def test_datas_match_whitelist(self, spec):
        """入包数据集合必须 == 白名单（等式，不只查漏拷）。"""
        text = _spec_text(spec)
        # 抽取 ("data/<name>", "data/<name>") 形态的入包项
        found = set(re.findall(r'PROJECT_ROOT\s*/\s*"data"\s*/\s*"(\w+)"', text))
        assert found == WHITELIST, f"{spec} 入包数据 {found} != 白名单 {WHITELIST}"

    def test_no_forbidden_dir_packed(self, spec):
        """禁入目录不得出现在 datas 中。"""
        text = _spec_text(spec)
        for bad in FORBIDDEN:
            assert f'"data" / "{bad}"' not in text, f"{spec} 打包了禁入目录 {bad}"


class TestEntryModules:
    def test_cli_entry_is_thin_absolute_import(self):
        """CLI 入口必须是绝对导入的薄模块（相对导入 → exe 启动即 ImportError）。"""
        entry = REPO_ROOT / "src" / "hws_math_auditor" / "__main__.py"
        tree = ast.parse(entry.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert node.level == 0, "入口模块含相对导入（exe 会 ImportError）"
        assert "__main__" in entry.read_text(encoding="utf-8")

    def test_gui_entry_is_thin_absolute_import(self):
        """GUI 入口同上，且必须存在（否则 exe 无入口）。"""
        entry = REPO_ROOT / "src" / "hws_math_auditor" / "gui" / "__main__.py"
        assert entry.exists(), "GUI 入口模块缺失"
        tree = ast.parse(entry.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert node.level == 0, "GUI 入口含相对导入（exe 会 ImportError）"
        assert "__main__" in entry.read_text(encoding="utf-8")

    def test_gui_entry_rejects_unknown_args(self):
        """窗口 exe 对未知参数必须报错 exit 2（静默忽略会挂进事件循环）。

        注意：**按文件路径加载入口模块**，不走 `import hws_math_auditor.gui`——
        后者会触发父包的模块级 `import PySide6`，而 PySide6 属 `gui` extra，
        CI 只装 `.[dev]` 会当场 ModuleNotFoundError。`--bogus` 分支在
        碰到 PySide6 之前就返回 2，所以按文件加载即可真验契约。
        """
        import importlib.util

        entry = REPO_ROOT / "src" / "hws_math_auditor" / "gui" / "__main__.py"
        spec = importlib.util.spec_from_file_location("_gui_main_under_test", entry)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        assert mod.main(["--bogus"]) == 2


class TestGuiNoJudgment:
    """GUI 只消费引擎、零判定逻辑（静态门禁三条齐上）。"""

    def test_gui_has_no_policy_literal(self):
        """GUI 不得内联政策数值字面量。"""
        src = (REPO_ROOT / "src" / "hws_math_auditor" / "gui" / "__init__.py").read_text(
            encoding="utf-8"
        )
        literal = "1e" + "-9"
        assert literal not in src, "GUI 内联了政策数值字面量"

    def test_gui_does_not_import_rules_layer(self):
        """GUI 不得 import 规则层（判定逻辑只属引擎）。"""
        src = (REPO_ROOT / "src" / "hws_math_auditor" / "gui" / "__init__.py").read_text(
            encoding="utf-8"
        )
        assert "hws_math_auditor.rules" not in src, "GUI 直接 import 了规则层"


class TestWheelCarriesData:
    """wheel 必须真的带数据（DEC2=A：pip 渠道"装完能用"）。

    2026-10-21 诊断 D2 的原始状态是 wheel 26 条目 / data 命中 0，
    非 editable 装完 `selftest` 报「自检失败」。这条把"数据随包"
    从一次性手工验证变成常驻判据。

    判据三面：**构建钩子存在** → **package-data 声明** → **实建 wheel 里有条目**。
    第三条要真构建（`python -m build`），标记 `slow` 让常规回归不受拖累。
    """

    def test_setup_py_has_build_hook_copying_data(self):
        """构建钩子必须把仓根 data/ 拷进包内（否则 package-data 收不到）。"""
        setup_py = REPO_ROOT / "setup.py"
        assert setup_py.exists(), "缺 setup.py（数据打进 wheel 的构建钩子所在）"
        text = setup_py.read_text(encoding="utf-8")
        for token in ("build_py", "copytree", "_data"):
            assert token in text, f"setup.py 缺 {token}（数据不会进 wheel）"
        # 钩子必须有"缺数据就中止构建"的守卫，不能静默产出空包
        assert "SystemExit" in text, "setup.py 缺缺数据守卫（会静默产出装完不可用的 wheel）"

    def test_pyproject_declares_package_data(self):
        """pyproject 必须声明 package-data（_data 四类文件）。"""
        text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        assert "[tool.setuptools.package-data]" in text, "缺 package-data 段"
        for sub in ("rules", "benchmarks", "snapshots", "samples"):
            assert f"_data/{sub}/" in text, f"package-data 未声明 _data/{sub}/"

    def test_manifest_in_ships_data_to_sdist(self):
        """sdist 必须含 data/ 与 tests/（wheel 由 sdist 重建，缺则构建中止）。"""
        manifest = REPO_ROOT / "MANIFEST.in"
        assert manifest.exists(), "缺 MANIFEST.in（sdist 不自足）"
        text = manifest.read_text(encoding="utf-8")
        assert "recursive-include data" in text, "MANIFEST.in 未收 data/"
        assert "recursive-include tests" in text, "MANIFEST.in 未收 tests/"

    @pytest.mark.slow
    def test_built_wheel_contains_data_entries(self, tmp_path):
        """实建 wheel：_data 条目数必须覆盖四类数据（真构建，慢）。"""
        import shutil
        import subprocess
        import sys
        import zipfile

        pytest.importorskip("build", reason="需要 `pip install build`（本仓把它当构建期工具）")

        # 复制一份源码树（不含构建产物），在 tmp 里构建，绝不污染仓库
        tree = tmp_path / "tree"
        shutil.copytree(
            REPO_ROOT,
            tree,
            ignore=shutil.ignore_patterns(
                ".git", "build", "dist", "release", "_backups", "update",
                "__pycache__", "_data", ".venv",
            ),
        )
        proc = subprocess.run(
            [sys.executable, "-m", "build", "--wheel", "--outdir", str(tmp_path / "out")],
            cwd=str(tree),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        assert proc.returncode == 0, f"构建失败：\n{proc.stdout}\n{proc.stderr}"

        wheels = list((tmp_path / "out").glob("*.whl"))
        assert wheels, "构建未产出 wheel"
        names = zipfile.ZipFile(wheels[0]).namelist()

        # 四类数据各至少 1 个条目；总量与仓内真源一致（不止"有"）
        for sub in ("rules", "benchmarks", "snapshots", "samples"):
            hits = [n for n in names if f"_data/{sub}/" in n]
            assert hits, f"wheel 内 _data/{sub}/ 为空（装完不可用）"

        expected = sum(
            1
            for sub in ("rules", "benchmarks", "snapshots", "samples")
            for p in (REPO_ROOT / "data" / sub).rglob("*")
            if p.is_file()
        )
        packed = sum(1 for n in names if "_data/" in n)
        assert packed == expected, (
            f"wheel 内 _data 条目 {packed} != 仓根 data/ 文件数 {expected}（数据面漂移）"
        )

