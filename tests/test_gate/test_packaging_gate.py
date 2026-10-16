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
import sys
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
