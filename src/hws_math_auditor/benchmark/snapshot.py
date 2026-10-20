"""预置模型输出快照生成器。

运行审计引擎，将结果存档为快照。
快照格式：model/版本/参数/input/output/sha256
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

from hws_math_auditor.benchmark.generator import generate_benchmark
from hws_math_auditor.pipeline import AuditRequest, audit


def generate_snapshot(
    case,
    model_name: str = "openPangu-2.0-Flash",
    model_version: str = "1.0",
    provider: str = "hf-mirror",
    temperature: float = 0.0,
    max_tokens: int = 4096,
    thinking_mode: bool = True,
) -> dict:
    """生成单条快照。

    Args:
        case: 基准用例
        model_name: 模型名称
        model_version: 模型版本
        provider: 提供商
        temperature: 生成温度
        max_tokens: 最大 token 数
        thinking_mode: 是否启用思维链

    Returns:
        快照字典
    """
    # 运行审计
    request = AuditRequest(
        solution_text=case.input["solution"],
        final_assertion=case.input.get("problem", ""),
    )
    result = audit(request)

    # 构建输出
    output = {
        "first_error_step": result.report.first_error.first_error if result.report else None,
        "verdicts": [
            {"status": v.status, "evidence": v.evidence}
            for v in result.report.verdicts
        ] if result.report else [],
        "recalc_result": result.report.recalc_result if result.report else "无法独立重算",
        "coverage": result.report.coverage if result.report else {},
    }

    output_text = json.dumps(output, ensure_ascii=False, indent=2)
    sha256 = hashlib.sha256(output_text.encode("utf-8")).hexdigest()

    snapshot = {
        "snapshot_id": case.id,
        "model": {
            "name": model_name,
            "version": model_version,
            "provider": provider,
        },
        "generation_params": {
            "temperature": temperature,
            "max_tokens": max_tokens,
            "thinking_mode": thinking_mode,
        },
        "input": {
            "problem": case.input["problem"],
            "solution": case.input["solution"],
        },
        "output": output,
        "sha256": sha256,
        "captured_date": datetime.now().strftime("%Y-%m-%d"),
    }

    return snapshot


def _write_text_lf(path, text: str) -> None:
    """以 UTF-8 + LF 写文本（跨平台位级一致，防 CRLF 污染快照字节）。"""
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def generate_all_snapshots(output_dir: str | None = None) -> list[dict]:
    """生成所有快照。

    Args:
        output_dir: 若提供，将快照写入 {output_dir}/snapshots/ 目录。

    Returns:
        快照列表。
    """
    cases = generate_benchmark()
    snapshots = []

    for case in cases:
        snapshot = generate_snapshot(case)
        snapshots.append(snapshot)

    if output_dir:
        out_path = Path(output_dir)
        snap_dir = out_path / "snapshots"
        snap_dir.mkdir(parents=True, exist_ok=True)

        # 写索引
        index = {
            "version": "1.0.0",
            "model": "openPangu-2.0-Flash",
            "snapshot_ids": [s["snapshot_id"] for s in snapshots],
        }
        _write_text_lf(
            snap_dir / "_index.json",
            json.dumps(index, ensure_ascii=False, indent=2),
        )

        # 写各快照
        for s in snapshots:
            _write_text_lf(
                snap_dir / f"{s['snapshot_id']}.json",
                json.dumps(s, ensure_ascii=False, indent=2),
            )

    return snapshots


if __name__ == "__main__":
    snapshots = generate_all_snapshots("data")
    print(f"生成 {len(snapshots)} 条快照:")
    for s in snapshots:
        print(f"  {s['snapshot_id']}: sha256={s['sha256'][:16]}...")
