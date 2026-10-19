# Changelog

本项目的版本分两层：

- **代码版本**（本文件）：修 bug、加功能、改发布形态
- **规则集版本**：阈值表 `data/rules/*.json` 的版本与所依据的口径及其生效日期

> 阈值/判定语义发生变化时，主版本号 +1，并在发布说明中提示「历史报告需重跑」。

## [0.2.0] - 2026-10-19

### 新增

- **报告头打印版本**：Markdown / JSON / HTML 三种报告与 CLI 文本输出统一打印
  **工具版本**与**依据（阈值表）版本**。四种形态同源（`report_to_dict()`），
  **刻意不打印生成时间** —— 报告承诺「同输入同输出」，两次运行逐字节一致。
- **规则集复核元数据** `meta.review`：`data/rules/thresholds.json` 与
  `data/rules/error_types.json` 各自写入复核日 / 复核周期 / 下次复核到期 / 复核人 /
  `standards[]`（含 `currency` 与 `authority_url`）。阈值表中 `status != verified` 的
  规则逐条补 `not_used_by`（声明本版本不进引擎）。
- **守门测试** `tests/test_rules/test_clause_review.py`：9 个用例（元数据齐全 / 日期可解析且
  到期晚于复核日 / `authority_url` 非空且为 URL / 错误类型条目级 `min_coverage` 之和等于汇总 /
  未进引擎规则必须声明 `not_used_by` / 报告头可见工具版本与依据版本）。

### 变更

- `pyproject.toml`：`[project.urls]` 增加 `Changelog`。

### 修复

- 包内 `__version__` 与 `pyproject.toml` 的 `version` 对齐（此前 `__version__` 停在 `0.1.0`，
  而发布版本是 `0.1.1`；报告头一旦打印工具版本就会自相矛盾）。

### 规则集

- **无变更**。当前依据：阈值表 `1.0.0`（生效 2026-10-16，11 条中 9 verified / 2 pending）、
  错误类型覆盖度分母（8 类，`min_coverage` 之和 18 = `total_min_coverage`）。
- 本次只加复核元数据与报告头字段，**不改任何阈值、不改判定语义**。

### 是否需要重跑历史报告

**否。** 判定结论与 v0.1.1 一致；报告差异仅为头部新增两行版本信息。

### 校验和

```
<pending>  hws-audit-cli-win64.exe
<pending>  hws-audit-gui-win64.exe
<pending>  hws-audit-source-v0.2.0.zip
<pending>  demo.gif
```

## [0.1.1] - 2026-10-18

回访修复：报告导出（`report.py` 单一渲染源 + CLI `--report/--report-formats` + GUI 导出按钮）、
首错编号对外统一 1 基、覆盖率键名修复、技术报告与演示 GIF 落仓。179 → 176+12 用例。
留档见 [plan/RELEASE-M7.md](plan/RELEASE-M7.md)。

### 规则集

- 无变更。当前依据：阈值表 `1.0.0`（生效 2026-10-16）

## [0.1.0] - 2026-10-16

首个发布版本：步骤级审计 + 首错锚定 + 三级判定语义 + 独立重算交叉验证 + 22 份植入真值基准。

### 规则集

- 当前依据：阈值表 `1.0.0`（生效 2026-10-16，9 verified / 2 pending）
- 真值台账 `data/benchmarks/BENCH-001..022`、LLM 兜底快照 `data/snapshots/`（模型默认关）