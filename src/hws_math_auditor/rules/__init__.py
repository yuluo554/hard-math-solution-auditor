"""模块③：知识与规则层（M3）。

职责：
- 加载机器可读阈值表
- status 门控：只有 verified 规则参与判定
- 零政策字面量门禁：扫描引擎/基准/前端源码中的政策数值字面量
- 判定语义不虚高：not_applicable 只给原文写了例外情形的项
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from hws_math_auditor.config import config


# ---------------------------------------------------------------------------
# 数据类
# ---------------------------------------------------------------------------

@dataclass
class ThresholdRule:
    """阈值规则。"""

    id: str
    code: str
    name: str
    description: str
    threshold: float
    operator: str  # greater_than_or_equal / less_than_or_equal / equal
    applies_if: str
    status: str  # verified / pending / unverified
    verified_by: Optional[str] = None
    verified_date: Optional[str] = None
    scope: str = "calc"  # calc / quota / check
    source: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "ThresholdRule":
        return cls(
            id=data["id"],
            code=data["code"],
            name=data["name"],
            description=data["description"],
            threshold=data["threshold"],
            operator=data["operator"],
            applies_if=data.get("applies_if", "any"),
            status=data.get("status", "pending"),
            verified_by=data.get("verified_by"),
            verified_date=data.get("verified_date"),
            scope=data.get("scope", "calc"),
            source=data.get("source"),
        )

    def is_active(self) -> bool:
        """规则是否参与判定（status=verified）。"""
        return self.status == "verified"


@dataclass
class ThresholdTable:
    """阈值表。"""

    version: str
    description: str
    rules: list[ThresholdRule] = field(default_factory=list)
    literal_exemptions: list[dict] = field(default_factory=list)
    judgment_semantics: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "ThresholdTable":
        rules = [ThresholdRule.from_dict(r) for r in data.get("rules", [])]
        return cls(
            version=data["version"],
            description=data.get("description", ""),
            rules=rules,
            literal_exemptions=data.get("literal_exemptions", []),
            judgment_semantics=data.get("judgment_semantics", {}),
        )

    def get_verified_rules(self, scope: Optional[str] = None) -> list[ThresholdRule]:
        """获取所有 verified 规则（按作用域过滤）。"""
        verified = [r for r in self.rules if r.is_active()]
        if scope:
            verified = [r for r in verified if r.scope == scope]
        return verified

    def get_pending_rules(self) -> list[ThresholdRule]:
        """获取所有 pending 规则（显式记录待核对）。"""
        return [r for r in self.rules if r.status == "pending"]

    def get_unverified_rules(self) -> list[ThresholdRule]:
        """获取所有 unverified 规则（不进引擎）。"""
        return [r for r in self.rules if r.status == "unverified"]


# ---------------------------------------------------------------------------
# 加载阈值表
# ---------------------------------------------------------------------------

def load_threshold_table(table_path: Optional[Path] = None) -> ThresholdTable:
    """加载阈值表。

    Args:
        table_path: 阈值表路径，默认 data/rules/thresholds.json

    Returns:
        ThresholdTable 实例
    """
    if table_path is None:
        # 在 PyInstaller 打包环境中，数据文件位于 sys._MEIPASS
        # 否则使用源码态的项目根路径
        import sys
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            table_path = Path(sys._MEIPASS) / "data" / "rules" / "thresholds.json"
        else:
            # __file__ = src/hws_math_auditor/rules/__init__.py
            # parents[3] = project root
            table_path = Path(__file__).parents[3] / "data" / "rules" / "thresholds.json"

    if not table_path.exists():
        raise FileNotFoundError(f"阈值表不存在: {table_path}")

    data = json.loads(table_path.read_text(encoding="utf-8"))
    return ThresholdTable.from_dict(data)


# ---------------------------------------------------------------------------
# 阈值表格式验证
# ---------------------------------------------------------------------------

def validate_threshold_table(table: ThresholdTable) -> list[str]:
    """验证阈值表格式。

    Returns:
        错误列表，空列表表示验证通过
    """
    errors = []

    # 检查必需字段
    if not table.version:
        errors.append("缺少 version 字段")

    # 检查规则
    rule_ids = set()
    for i, rule in enumerate(table.rules):
        # 必需字段
        if not rule.id:
            errors.append(f"规则 {i}: 缺少 id")
        if rule.id in rule_ids:
            errors.append(f"规则 {rule.id}: id 重复")
        rule_ids.add(rule.id)

        if not rule.code:
            errors.append(f"规则 {rule.id}: 缺少 code")

        if rule.status not in ("verified", "pending", "unverified"):
            errors.append(f"规则 {rule.id}: 非法 status '{rule.status}'")

        if rule.operator not in ("greater_than_or_equal", "less_than_or_equal", "equal"):
            errors.append(f"规则 {rule.id}: 非法 operator '{rule.operator}'")

        if rule.scope not in ("calc", "quota", "check"):
            errors.append(f"规则 {rule.id}: 非法 scope '{rule.scope}'")

        # verified 规则必须有 verified_by
        if rule.status == "verified" and not rule.verified_by:
            errors.append(f"规则 {rule.id}: verified 规则缺少 verified_by")

    return errors


# ---------------------------------------------------------------------------
# 零政策字面量门禁
# ---------------------------------------------------------------------------

# 豁免口径（写死）：
#   1) K8 唯一定义点所在文件（config.py）——它是数值口径的唯一来源；
#   2) tests/ 目录——测试夹具为做变异验证会故意内嵌字面量。
# 其余任何 .py 里出现政策数值字面量即违规。
EXEMPT_PATH_PREFIXES = ("tests",)
EXEMPT_FILE_SUFFIXES = ("hws_math_auditor/config.py",)

# 需要扫描的源码目录（相对项目根）
SCAN_DIRS = [
    "src/hws_math_auditor",
    "tests",
]

# 豁免文件（完全豁免）
EXEMPT_FILES = [
    "data/rules/thresholds.json",  # 阈值表本身
    "data/rules/error_types.json",  # 错误类型定义
]


def project_root() -> Path:
    """解析项目根目录。

    源码态：__file__ = <root>/src/hws_math_auditor/rules/__init__.py → parents[3]
    冻结态（PyInstaller）：数据与源码在 sys._MEIPASS 下，无仓库根概念，
    此时回落到 _MEIPASS 上一级（解压目录即"根"）。
    """
    import sys

    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).parents[3]


def _iter_scanned_files(base_path: Path) -> list[Path]:
    """列出扫描面内的全部 .py 文件（豁免文件除外）。

    单独抽出便于"扫描面非空"自证——空扫描（路径解析错）绝不能冒充通过。
    """
    files: list[Path] = []
    for scan_dir in SCAN_DIRS:
        scan_path = base_path / scan_dir
        if not scan_path.exists():
            continue
        for py_file in sorted(scan_path.rglob("*.py")):
            if str(py_file.relative_to(base_path)) in EXEMPT_FILES:
                continue
            files.append(py_file)
    return files


def scan_for_policy_literals(
    base_path: Optional[Path] = None,
) -> list[dict]:
    """扫描源码中的政策数值字面量。

    政策数值字面量 = 非豁免文件中的硬编码政策阈值。

    Args:
        base_path: 项目根路径，默认自动解析（见 project_root()）

    Returns:
        发现的违规字面量列表
    """
    if base_path is None:
        base_path = project_root()

    violations = []

    # 政策数值字面量模式（科学计数法 / 长小数）。
    # 模式串自身不含任何政策数值——用字符类拼装，避免扫描器源码自带命中串。
    _sci = "1e" + "-" + r"\d+"
    _dec = "0" + r"\." + r"\d{9,}"
    _dec2 = r"\d+\." + r"\d{9,}"
    _sci2 = r"\b1e" + r"\d+"
    literal_pattern = re.compile(
        "(?:" + r"\b(?:" + _sci + "|" + _dec + "|" + _dec2 + "|" + _sci2 + "))"
    )

    for py_file in _iter_scanned_files(base_path):
        rel_path = py_file.relative_to(base_path)
        rel_posix = rel_path.as_posix()

        try:
            content = py_file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        for match in literal_pattern.finditer(content):
            line_num = content[: match.start()].count("\n") + 1
            line_content = content.split("\n")[line_num - 1].strip()

            if _is_exempt_path(rel_posix):
                continue

            violations.append(
                {
                    "file": str(rel_path),
                    "line": line_num,
                    "literal": match.group(),
                    "content": line_content,
                }
            )

    return violations


def _is_exempt_path(rel_posix: str) -> bool:
    """路径豁免判定（口径写死，见 EXEMPT_* 常量）。"""
    if any(rel_posix.startswith(p + "/") or rel_posix == p for p in EXEMPT_PATH_PREFIXES):
        return True
    return any(rel_posix.endswith(s) for s in EXEMPT_FILE_SUFFIXES)


def check_zero_literal_gate(
    base_path: Optional[Path] = None,
) -> tuple[bool, list[dict]]:
    """零政策字面量门禁检查。

    Args:
        base_path: 项目根路径

    Returns:
        (是否通过, 违规列表)

    扫描面为空时**不通过**（返回空扫描哨兵违规）——路径解析错导致的
    静默空扫必须暴露，否则门禁退化成"永远绿"的假门。
    """
    if base_path is None:
        base_path = project_root()

    scanned = _iter_scanned_files(base_path)
    if not scanned:
        return False, [
            {
                "file": "<scan-surface>",
                "line": 0,
                "literal": "",
                "content": (
                    f"扫描面为空：{base_path} 下未找到任何待扫描 .py 文件，"
                    f"门禁不可判为通过（base_path 解析错误？）"
                ),
            }
        ]

    violations = scan_for_policy_literals(base_path)
    passed = len(violations) == 0
    return passed, violations


# ---------------------------------------------------------------------------
# 判定语义不虚高
# ---------------------------------------------------------------------------

def validate_judgment_semantics(
    verdict_status: str,
    evidence: str,
    has_explicit_exception: bool,
    has_obligation: bool,
) -> dict:
    """验证判定语义不虚高。

    规则：
    - not_applicable 只给"原文写了例外情形"的项
    - 无适用项 → not_assessed（不输出 compliant）
    - 无条件义务缺失 = noncompliant

    Args:
        verdict_status: 判定状态
        evidence: 判定证据
        has_explicit_exception: 原文是否写了例外情形
        has_obligation: 是否存在无条件义务

    Returns:
        验证结果
    """
    issues = []

    # 规则 1：not_applicable 只给原文写了例外情形的项
    if verdict_status == "not_applicable" and not has_explicit_exception:
        issues.append(
            "not_applicable 用于'原文未写例外情形'的项，"
            "应改为 not_assessed 或 noncompliant"
        )

    # 规则 2：无适用项 → not_assessed（不输出 compliant）
    if verdict_status == "compliant" and not has_obligation:
        issues.append(
            "无适用项却输出 compliant，应改为 not_assessed"
        )

    # 规则 3：无条件义务缺失 = noncompliant
    if not has_obligation and verdict_status != "noncompliant":
        issues.append(
            "无条件义务缺失，应判定为 noncompliant"
        )

    return {
        "valid": len(issues) == 0,
        "issues": issues,
    }


# ---------------------------------------------------------------------------
# 阈值比较
# ---------------------------------------------------------------------------

def check_threshold(
    value: float,
    rule: ThresholdRule,
) -> bool:
    """检查值是否满足阈值规则。

    Args:
        value: 待检查值
        rule: 阈值规则

    Returns:
        是否满足
    """
    if rule.operator == "greater_than_or_equal":
        return value >= rule.threshold
    elif rule.operator == "less_than_or_equal":
        return value <= rule.threshold
    elif rule.operator == "equal":
        return abs(value - rule.threshold) < config.tolerance
    else:
        raise ValueError(f"未知操作符: {rule.operator}")


# ---------------------------------------------------------------------------
# 全局阈值表实例
# ---------------------------------------------------------------------------

_threshold_table: Optional[ThresholdTable] = None


def get_threshold_table() -> ThresholdTable:
    """获取全局阈值表实例（懒加载）。"""
    global _threshold_table
    if _threshold_table is None:
        _threshold_table = load_threshold_table()
    return _threshold_table


def reset_threshold_table() -> None:
    """重置阈值表实例（用于测试）。"""
    global _threshold_table
    _threshold_table = None
