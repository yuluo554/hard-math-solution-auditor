"""报告导出：Markdown / JSON / HTML 三格式（单一渲染源）

纪律（plan/05 §1.2 承诺"报告导出：Markdown + JSON + HTML"）：
  - 三种格式都从**同一个** `report_to_dict()` 渲染，不允许各写一份取数逻辑
    （否则三份报告会漂移，出现"JSON 说 3 步、HTML 说 4 步"这类缺陷）；
  - HTML **零外链**（无 CDN/字体/图片引用），断网可开；
  - 输出路径由调用方给，函数只负责写文件并返回实际路径。
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, Dict

from hws_math_auditor.model import AuditReport

FORMATS = ("md", "json", "html")


def report_to_dict(report: AuditReport) -> Dict[str, Any]:
    """唯一的取数入口：三种格式都从这里渲染。"""
    # 内部 first_error 是 0 基索引（locator 的 API 口径，测试依赖它）；
    # 对外展示一律 1 基 —— 否则报告写"首错步骤 2"而解释写"首错在第 3 步"（v0.1.0 实况）
    fe = report.first_error.first_error
    return {
        "first_error": None if fe is None else fe + 1,
        "first_error_index0": fe,
        "contaminated": list(report.first_error.contaminated),
        "independent_failures": list(report.first_error.independent_failures),
        "explanation": report.first_error.explanation,
        "recalc_result": report.recalc_result,
        "coverage": report.coverage,
        # 报告头（阶段三 任务 5）：工具版本与依据版本；无生成时间（同输入同输出）
        "tool_version": report.tool_version,
        "ruleset_version": report.ruleset_version,
        # 步骤号在 Step 上，Verdict 只有判定结果 —— 按位置配对（两者同序）
        "verdicts": [
            {
                "step": step.step_no,
                "status": v.status,
                "evidence": v.evidence,
                "counterexample": v.counterexample,
            }
            for step, v in zip(report.steps, report.verdicts)
        ],
    }


def render_json(report: AuditReport) -> str:
    return json.dumps(report_to_dict(report), ensure_ascii=False, indent=2)


def render_markdown(report: AuditReport) -> str:
    data = report_to_dict(report)
    fe = data["first_error"]
    lines = [
        "# 难题解答审计报告",
        "",
        f"- **工具版本**：{data['tool_version'] or '—'}",
        f"- **依据（阈值表）**：{data['ruleset_version'] or '—'}",
        f"- **首错步骤**：{fe if fe is not None else '无（未检出错误）'}",
        f"- **独立重算**：{data['recalc_result']}",
        f"- **覆盖率**：{data['coverage'].get('coverage', 0):.1%}"
        f"（{data['coverage'].get('normalized', 0)}/{data['coverage'].get('total_steps', 0)}）",
        "",
        "## 逐步骤判定",
        "",
        "| 步骤 | 状态 | 证据 | 反例 |",
        "|---|---|---|---|",
    ]
    for v in data["verdicts"]:
        ce = v["counterexample"]
        lines.append("| %s | %s | %s | %s |" % (
            v["step"], v["status"], _cell(v["evidence"]),
            _cell(json.dumps(ce, ensure_ascii=False)) if ce else "—"))
    if data["explanation"]:
        lines += ["", "## 解释", "", data["explanation"]]
    if data["contaminated"]:
        lines += ["", f"**受污染步骤**：{data['contaminated']}"]
    if data["independent_failures"]:
        lines += ["", f"**独立失效步骤**：{data['independent_failures']}"]
    return "\n".join(lines) + "\n"


def render_html(report: AuditReport) -> str:
    data = report_to_dict(report)
    fe = data["first_error"]
    rows = "\n".join(
        "<tr><td>%s</td><td class='%s'>%s</td><td>%s</td><td>%s</td></tr>" % (
            v["step"], v["status"], html.escape(v["status"]),
            html.escape(str(v["evidence"])),
            html.escape(json.dumps(v["counterexample"], ensure_ascii=False))
            if v["counterexample"] else "—")
        for v in data["verdicts"]
    )
    return """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>难题解答审计报告</title>
<style>
body{{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;max-width:960px;margin:2rem auto;padding:0 1rem;color:#1f2328}}
h1{{font-size:1.4rem;border-bottom:1px solid #d0d7de;padding-bottom:.4rem}}
table{{border-collapse:collapse;width:100%;margin-top:1rem}}
th,td{{border:1px solid #d0d7de;padding:.4rem .6rem;text-align:left;font-size:.9rem}}
th{{background:#f6f8fa}}
.ok{{color:#1a7f37}}.invalid{{color:#cf222e}}.unverifiable{{color:#9a6700}}
.summary{{display:flex;gap:2rem;margin:1rem 0}}
.summary div{{background:#f6f8fa;border-radius:6px;padding:.6rem 1rem}}
.note{{color:#57606a;font-size:.85rem;margin-top:1.5rem}}
</style></head><body>
<h1>难题解答审计报告</h1>
<p class="note">工具版本 {tool_version}；依据（阈值表）{ruleset_version}。<br>
不打印生成时间：本报告要求同输入同输出、两次运行逐字节一致。</p>
<div class="summary">
  <div><b>首错步骤</b><br>{fe}</div>
  <div><b>独立重算</b><br>{recalc}</div>
  <div><b>覆盖率</b><br>{coverage}</div>
</div>
<p>{explanation}</p>
<table><thead><tr><th>步骤</th><th>状态</th><th>证据</th><th>反例</th></tr></thead>
<tbody>
{rows}
</tbody></table>
<p class="note">判定语义：ok / invalid / unverifiable 三级；unverifiable 表示引擎能力外，
不等于正确。本报告为辅助定位，不构成对解答正确性的最终评判。</p>
</body></html>
""".format(
        fe=fe if fe is not None else "无（未检出错误）",
        recalc=html.escape(str(data["recalc_result"])),
        coverage="%.1f%%" % (data["coverage"].get("coverage", 0) * 100),
        explanation=html.escape(data["explanation"] or ""),
        rows=rows,
        tool_version=html.escape(str(data["tool_version"] or "—")),
        ruleset_version=html.escape(str(data["ruleset_version"] or "—")),
    )


def _cell(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


RENDERERS = {"md": render_markdown, "json": render_json, "html": render_html}


def write_report(report: AuditReport, output: Path, fmt: str) -> Path:
    """按格式写报告，返回实际路径（fmt 非法时抛 ValueError）。"""
    if fmt not in RENDERERS:
        raise ValueError("未知报告格式: %s（可选 %s）" % (fmt, "/".join(FORMATS)))
    output = Path(output)
    if output.suffix.lower().lstrip(".") != fmt:
        output = output.with_suffix("." + fmt)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(RENDERERS[fmt](report), encoding="utf-8")
    return output


def write_all(report: AuditReport, stem: Path) -> list:
    """一次写三种格式（GUI 的「导出报告」按钮用这个）。"""
    stem = Path(stem)
    return [write_report(report, stem.with_suffix("." + fmt), fmt) for fmt in FORMATS]
