"""规则集复核元数据守门（阶段三 任务 5）。

字段规范 = ``10-6-scaffold-formwork-checker`` v2.0.0 的实测形态（文件级 ``meta.review``：
``reviewed_on`` / ``cycle_months`` / ``next_review_due`` / ``reviewer`` / ``standards[]``，
每条含 ``currency`` 与 ``authority_url``）。

本仓的「规则集定义文件」是 ``data/rules/thresholds.json``（阈值表，K14 三态门控的载体）
与 ``data/rules/error_types.json``（错误类型与覆盖度分母）。

scaffold 的 5 条用例里，第 4/5 条是它特有的形态，本仓替换为同等强度的两条：

4. 错误类型覆盖度：条目级 ``min_coverage`` 之和必须等于 ``total_min_coverage``
   （清单类文件的「条目级与汇总一致」对应物）；
5. ``status != verified`` 的规则必须逐条声明 ``not_used_by``（对应「本版本不依赖」声明）。

另加一条：导出的报告头必须打印工具版本与依据版本（任务 5 的验收第 1 项）。

每条判据被破坏后必须报红 —— 负控记录见 plan/audits 的阶段三交接文档。
"""

import datetime
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
THRESHOLDS = REPO_ROOT / "data" / "rules" / "thresholds.json"
ERROR_TYPES = REPO_ROOT / "data" / "rules" / "error_types.json"

REQUIRED_REVIEW_KEYS = ("reviewed_on", "cycle_months", "next_review_due", "reviewer",
                        "standards")
REQUIRED_STANDARD_KEYS = ("standard", "issued", "effective", "currency",
                          "authority_url", "conclusion")

RULE_FILES = (THRESHOLDS, ERROR_TYPES)


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _review(path):
    return (_load(path).get("meta") or {}).get("review") or {}


def _date(text):
    return datetime.datetime.strptime(text, "%Y-%m-%d").date()


@pytest.mark.parametrize("path", RULE_FILES, ids=lambda p: p.name)
def test_rules_files_carry_review_metadata(path):
    review = _review(path)
    assert review, "%s 缺 meta.review（阶段三 任务 5 的字段规范）" % path.name
    for key in REQUIRED_REVIEW_KEYS:
        assert review.get(key) not in (None, "", []), "meta.review 缺字段：%s" % key
    assert isinstance(review.get("cycle_months"), int) and review["cycle_months"] > 0


@pytest.mark.parametrize("path", RULE_FILES, ids=lambda p: p.name)
def test_review_dates_are_parsable_and_next_due_after_reviewed_on(path):
    review = _review(path)
    reviewed = _date(review["reviewed_on"])
    due = _date(review["next_review_due"])
    assert due > reviewed, "next_review_due 必须晚于 reviewed_on"
    months = (due.year - reviewed.year) * 12 + (due.month - reviewed.month)
    assert abs(months - review["cycle_months"]) <= 1


@pytest.mark.parametrize("path", RULE_FILES, ids=lambda p: p.name)
def test_review_standards_carry_authority_url(path):
    standards = _review(path).get("standards") or []
    assert standards, "%s 的 meta.review.standards 为空 —— 复核没有出处" % path.name
    for item in standards:
        for key in REQUIRED_STANDARD_KEYS:
            assert (item.get(key) or "").strip(), (
                "%s 的标准 %r 缺 %s" % (path.name, item.get("standard"), key))
        for part in str(item["authority_url"]).split(";"):
            if part.strip():
                assert part.strip().startswith("http"), "authority_url 必须是可访问 URL"


def test_error_type_coverage_matches_total():
    """条目级 min_coverage 之和 == total_min_coverage（汇总与条目不得漂移）。"""
    payload = _load(ERROR_TYPES)
    items = payload.get("error_types") or []
    assert items, "error_types.json 没有条目"
    assert sum(item["min_coverage"] for item in items) == payload["total_min_coverage"]


def test_rules_without_engine_use_declare_not_used_by():
    """未进引擎（status != verified）的规则必须逐条声明 not_used_by。"""
    rules = _load(THRESHOLDS).get("rules") or []
    assert rules
    inactive = [rule for rule in rules if rule.get("status") != "verified"]
    assert inactive, "样例应至少有一条未进引擎的规则（THR-005 / THR-006）"
    for rule in inactive:
        assert rule.get("not_used_by"), (
            "规则 %s（status=%s）缺 not_used_by —— 未声明「本版本不依赖」" %
            (rule.get("id"), rule.get("status")))
    for rule in rules:
        if rule.get("status") == "verified":
            assert not rule.get("not_used_by"), (
                "verified 规则 %s 不该声明 not_used_by" % rule.get("id"))


def test_exported_report_header_shows_tool_and_ruleset_version(tmp_path):
    """报告头必须可见工具版本与依据版本（任务 5 验收第 1 项）。"""
    from hws_math_auditor import __version__
    from hws_math_auditor.model import AuditReport, FirstErrorResult, Step, Verdict
    from hws_math_auditor.report import render_markdown

    report = AuditReport(
        steps=[Step(step_no=1, raw_text="x = 1", source_line_start=1, source_line_end=1)],
        verdicts=[Verdict(status="ok", evidence="可符号化")],
        first_error=FirstErrorResult(first_error=None),
        recalc_result="一致",
        coverage={"total_steps": 1, "normalized": 1, "coverage": 1.0},
        tool_version=__version__,
        ruleset_version="1.0.0",
    )
    text = render_markdown(report)
    assert "工具版本" in text and __version__ in text
    assert "依据（阈值表）" in text and "1.0.0" in text
    assert "生成时间" not in text, "本仓报告刻意不带生成时间（同输入同输出）"