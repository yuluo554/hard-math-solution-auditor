"""报告导出验收（plan/05 §1.2 承诺：Markdown + JSON + HTML）

口径：
  - 三种格式来自**同一渲染源** `report_to_dict()`，不得各写一份取数逻辑；
  - HTML 零外链；
  - 首错步骤对外一律 1 基（内部 locator 是 0 基）；
  - `--report` 真的写文件，扩展名决定格式。
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from hws_math_auditor.model import AuditReport, FirstErrorResult, Step, Verdict
from hws_math_auditor.report import (
    FORMATS,
    render_html,
    render_json,
    render_markdown,
    report_to_dict,
    write_all,
    write_report,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def sample_report():
    steps = [
        Step(step_no=1, raw_text="x = 3", source_line_start=1, source_line_end=1,
             status="normalized"),
        Step(step_no=2, raw_text="2x = 6", source_line_start=2, source_line_end=2,
             status="normalized"),
        Step(step_no=3, raw_text="x = -3", source_line_start=3, source_line_end=3,
             status="normalized"),
    ]
    verdicts = [
        Verdict(status="ok", evidence="可符号化"),
        Verdict(status="ok", evidence="符号等价"),
        Verdict(status="invalid", evidence="数值反例", counterexample={"x": -3}),
    ]
    return AuditReport(
        steps=steps,
        verdicts=verdicts,
        first_error=FirstErrorResult(first_error=2, contaminated=[], independent_failures=[],
                                     explanation="首错在第 3 步"),
        recalc_result="无法独立重算",
        coverage={"total_steps": 3, "normalized": 3, "unsymbolizable": 0, "coverage": 1.0},
    )


class TestRenderers:
    def test_first_error_is_one_based_for_display(self, sample_report):
        data = report_to_dict(sample_report)
        assert data["first_error"] == 3, "对外展示必须 1 基（内部 locator 0 基）"
        assert data["first_error_index0"] == 2

    def test_no_error_renders_as_none(self, sample_report):
        sample_report.first_error = FirstErrorResult(first_error=None)
        assert report_to_dict(sample_report)["first_error"] is None
        assert "未检出错误" in render_markdown(sample_report)

    def test_three_formats_share_one_source(self, sample_report):
        data = report_to_dict(sample_report)
        assert len(data["verdicts"]) == 3
        md = render_markdown(sample_report)
        js = json.loads(render_json(sample_report))
        assert js["verdicts"] == data["verdicts"]
        for v in data["verdicts"]:
            assert str(v["step"]) in md, "Markdown 漏了步骤"
        assert "invalid" in md and "数值反例" in md

    def test_html_has_no_external_links(self, sample_report):
        html_text = render_html(sample_report)
        assert "http://" not in html_text and "https://" not in html_text, "HTML 必须 0 外链"
        assert "<table" in html_text and "invalid" in html_text

    def test_coverage_denominator_uses_total_steps(self, sample_report):
        md = render_markdown(sample_report)
        assert "3/3" in md, "覆盖率分母必须取 total_steps（v0.1.0 曾渲染成 3/0）"

    def test_write_report_switches_extension(self, sample_report, tmp_path):
        out = write_report(sample_report, tmp_path / "r", "json")
        assert out.suffix == ".json" and out.is_file()
        assert json.loads(out.read_text(encoding="utf-8"))["first_error"] == 3

    def test_write_all_emits_three_files(self, sample_report, tmp_path):
        written = write_all(sample_report, tmp_path / "audit")
        assert sorted(p.suffix for p in written) == [".html", ".json", ".md"]
        assert all(p.is_file() for p in written)

    def test_unknown_format_rejected(self, sample_report, tmp_path):
        with pytest.raises(ValueError):
            write_report(sample_report, tmp_path / "x", "pdf")


class TestCliReportFlag:
    def test_report_flag_writes_three_files(self, tmp_path):
        out = tmp_path / "audit"
        proc = subprocess.run(
            [sys.executable, "-m", "hws_math_auditor", "audit",
             "--input", str(REPO_ROOT / "data" / "samples" / "dirty_solution.txt"),
             "--report", str(out)],
            capture_output=True, text=True, encoding="utf-8", cwd=str(REPO_ROOT),
        )
        assert proc.returncode == 1, "含错解答应 exit 1（既定语义）"
        for fmt in FORMATS:
            assert (tmp_path / ("audit." + fmt)).is_file(), f"缺 {fmt} 报告"

    def test_report_format_subset(self, tmp_path):
        out = tmp_path / "only"
        proc = subprocess.run(
            [sys.executable, "-m", "hws_math_auditor", "audit",
             "--input", str(REPO_ROOT / "data" / "samples" / "clean_solution.txt"),
             "--report", str(out), "--report-formats", "md"],
            capture_output=True, text=True, encoding="utf-8", cwd=str(REPO_ROOT),
        )
        assert proc.returncode == 0
        assert (tmp_path / "only.md").is_file()
        assert not (tmp_path / "only.json").exists()


class TestGuiExportWiring:
    """GUI 导出按钮必须接线（v0.1.0 承诺了导出但代码里只有 setHtml）"""

    def test_export_button_connected(self):
        src = (REPO_ROOT / "src" / "hws_math_auditor" / "gui" / "__init__.py").read_text(
            encoding="utf-8")
        assert "self.export_btn.clicked.connect(self._export_report)" in src
        assert "write_all(" in src, "导出必须走 report.write_all（同一渲染源）"

    def test_plan_declares_export_formats(self):
        plan = (REPO_ROOT / "plan" / "05-发布与交付.md").read_text(encoding="utf-8")
        for token in ("Markdown", "JSON", "HTML"):
            assert token in plan, f"plan/05 未声明报告格式 {token}"
