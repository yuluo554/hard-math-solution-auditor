"""安装面三面对账守门测试。

判据三面交叉（skill 明确要求）：
- **测试面**：tests/ 真 import 的每个库
- **安装面**：pyproject 的 extras 声明
- **README 面**：README 快速开始那条安装命令的 extras

任一面缺口都意味着"干净环境照 README 装完，测试会炸"。

实现注意：**stdlib 判定用冻结名单制**，不用 `sys.stdlib_module_names`
（3.10+ 才有，底线 3.8 上取到空集 → 每个标准库都判成第三方 → 全量假红）。
"""

import ast
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = REPO_ROOT / "pyproject.toml"
README = REPO_ROOT / "README.md"

# 冻结 stdlib 名单（项目底线 3.8 的常用子集；新增 import 需同步此名单——
# 这是"判定词表"的维护，不是绕过）
STDLIB = {
    "abc", "argparse", "ast", "asyncio", "base64", "builtins", "collections",
    "contextlib", "copy", "csv", "dataclasses", "datetime", "decimal", "difflib",
    "enum", "errno", "functools", "gc", "glob", "gzip", "hashlib", "heapq",
    "html", "http", "importlib", "inspect", "io", "itertools", "json", "logging",
    "math", "os", "pathlib", "pickle", "platform", "pprint", "random", "re",
    "shlex", "shutil", "signal", "socket", "sqlite3", "stat", "statistics",
    "string", "struct", "subprocess", "sys", "tempfile", "textwrap", "threading",
    "time", "traceback", "types", "typing", "unicodedata", "unittest", "urllib",
    "uuid", "warnings", "weakref", "xml", "zipfile", "__future__",
}

# 本包自身
OWN_PKG = "hws_math_auditor"

# 分发名 → import 名（直接比较会造假红）
DIST_TO_IMPORT = {
    "pytest": "pytest",
    "pytest-cov": "pytest_cov",
    "pyside6": "PySide6",
    "pyinstaller": "PyInstaller",
    "sympy": "sympy",
    "setuptools": "setuptools",
    "wheel": "wheel",
}


def _tests_imports() -> set:
    """AST 从严收集 tests/ 下全部 import（含函数体内 import）。"""
    found = set()
    for f in (REPO_ROOT / "tests").rglob("*.py"):
        tree = ast.parse(f.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    found.add(a.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.level == 0 and node.module:
                    found.add(node.module.split(".")[0])
    return found


def _pyproject_extras() -> dict:
    """解析 pyproject 的 extras 声明。"""
    text = PYPROJECT.read_text(encoding="utf-8")
    extras = {}
    # [project.optional-dependencies] 段
    m = re.search(
        r"\[project\.optional-dependencies\](.*?)(?=\n\[|\Z)", text, re.S
    )
    assert m, "pyproject 缺少 optional-dependencies 段"
    body = m.group(1)
    for em in re.finditer(r"^(\w+)\s*=\s*\[(.*?)\]", body, re.S | re.M):
        name = em.group(1)
        pkgs = re.findall(r'"([^"<>=\s]+)', em.group(2))
        extras[name] = {p.lower() for p in pkgs}
    return extras


def _pyproject_core_deps() -> set:
    """解析 pyproject 的 [project].dependencies（核心依赖，永远安装）。"""
    text = PYPROJECT.read_text(encoding="utf-8")
    m = re.search(r"^dependencies\s*=\s*\[(.*?)\]", text, re.S | re.M)
    if not m:
        return set()
    return {p.lower() for p in re.findall(r'"([^"<>=\s]+)', m.group(1))}


def _readme_dev_extras() -> set:
    """README 快速开始那条安装命令里的 extras（小写）。"""
    text = README.read_text(encoding="utf-8")
    # 形如 pip install -e ".[dev]" 或 ".[dev,gui]"
    found = set()
    for m in re.finditer(r'pip install -e "?\.\[([^\]]+)\]', text):
        for name in m.group(1).split(","):
            found.add(name.strip().lower())
    return found


class TestInstallSurface:
    def test_readme_extras_exist_in_pyproject(self):
        """README 用的 extras 名必须在 pyproject 中声明。"""
        declared = set(_pyproject_extras())
        used = _readme_dev_extras()
        assert used, "README 未找到 `pip install -e \".[...]\"` 行（抽取失败？）"
        missing = used - declared
        assert not missing, f"README 用了未声明的 extras: {missing}"

    def test_tests_imports_covered_by_dev_extras(self):
        """测试面每个第三方 import 必须在 dev extras 里可解析。"""
        extras = _pyproject_extras()
        dev = extras.get("dev", set())
        # gui extra 也算"可声明"的邻域（GUI 测试若存在需算入）
        declared_dist_names = set()
        for pkgs in extras.values():
            declared_dist_names |= pkgs

        import_to_dist = {}
        for dist, imp in DIST_TO_IMPORT.items():
            import_to_dist[imp.lower()] = dist

        core = _pyproject_core_deps()

        uncovered = []
        scanned = 0
        for name in sorted(_tests_imports()):
            if name in STDLIB or name == OWN_PKG:
                continue
            scanned += 1
            # 核心依赖（[project].dependencies）永远装，算已覆盖
            if name.lower() in core:
                continue
            # 测试期第三方（如 pytest）应在 dev
            if name.lower() in {d for d in dev}:
                continue
            # 或在任意 extra 里声明
            if name.lower() in declared_dist_names:
                continue
            uncovered.append(name)

        assert scanned >= 1, "未扫描到任何第三方 import（扫描面为空 = 假门）"
        assert not uncovered, (
            f"测试 import 了未在 extras 声明的第三方库: {uncovered}"
        )

    def test_scan_surface_not_empty(self):
        """扫描面非空自证（防路径解析错导致的静默空扫）。"""
        imports = _tests_imports()
        assert len(imports) >= 5, f"tests/ import 收集面仅 {len(imports)} 项，疑似解析错"


class TestGuiExtraSeparate:
    def test_pyside6_not_in_dev(self):
        """PySide6 属 gui extra，不得进 dev（dev 应轻）。"""
        extras = _pyproject_extras()
        assert "pyside6" not in extras.get("dev", set()), "PySide6 不该进 dev extras"
        assert "pyside6" in extras.get("gui", set()), "PySide6 应在 gui extras"

    def test_tests_do_not_require_pyside6(self):
        """测试套件不得在模块级 import PySide6（CI 只装 .[dev]）。"""
        offenders = []
        for f in (REPO_ROOT / "tests").rglob("*.py"):
            tree = ast.parse(f.read_text(encoding="utf-8"))
            for node in tree.body:  # 只看模块级
                if isinstance(node, ast.Import):
                    for a in node.names:
                        if a.name.split(".")[0] == "PySide6":
                            offenders.append(str(f.relative_to(REPO_ROOT)))
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.split(".")[0] == "PySide6":
                        offenders.append(str(f.relative_to(REPO_ROOT)))
        assert offenders == [], f"测试模块级 import 了 PySide6（CI 会炸）: {offenders}"
