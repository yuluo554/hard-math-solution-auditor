# Changelog

本项目的版本分两层：

- **代码版本**（本文件）：修 bug、加功能、改发布形态
- **规则集版本**：阈值表 `data/rules/*.json` 的版本与所依据的口径及其生效日期

> 阈值/判定语义发生变化时，主版本号 +1，并在发布说明中提示「历史报告需重跑」。

## [0.2.1] - 2026-10-21

补丁版。范围限定「退出码接真实结果 + 数据自证 + 自述对齐 + 判定依据可 diff + CI 换新」，
**不扩题库、不改判定算法、不实现断言对账**。

### 修复（最重要）

- **`benchmark` 的退出码承认真实结果**（此前恒 exit 0）：逐条 `passed` 全部为真、
  误报率 0、定位准确率 100% 三者同时成立才 exit 0；任一不成立 → **exit 1**。
  `--metrics` 与 `--run` 同一判定（此前 `--metrics` 直接 `return 0`）。
  此前即使把验证器换成"恒判 ok"（18 条含错用例全红、定位准确率 0%），
  CLI 仍报成功——`README` 的「1 = 基准未达标」与实现不符。
- **pip 渠道装完可用**：`data/` 随 wheel / sdist 分发（`setup.py` 的 `build_py` 钩子
  把仓根 `data/` 拷进包内 `_data/`，配 `[tool.setuptools.package-data]`）。
  此前 wheel 里 `data/` 命中 0，非 editable 安装后 `selftest` 报「自检失败」、
  `audit` 抛 `FileNotFoundError`。
- **数据缺失 → 友好提示 + 退出码 2**：`audit` / `benchmark` / `selftest` 在数据目录
  不可用时打印可操作提示并返回 2，不再抛 traceback，也不再与"解答含错"共用退出码 1。

### 变更

- **Python floor `>=3.8` → `>=3.12`**（3.8 已于 2024-10 EOL；最近一次 CI 绿早于
  GitHub 的 `ubuntu-latest → Ubuntu 26` 迁移）。连带：`PySide6` 去掉 `<6.7` 上限、
  `build` extra 不再钉 `setuptools<81`、`[build-system]` 抬到 `setuptools>=77`。
  **免安装 exe 不受影响。**
- `license` 改用 SPDX 表达式（PEP 639）+ `license-files`，移除已废弃的
  `License :: OSI Approved :: MIT License` classifier。
- `.gitattributes`：去掉全局 `*.json binary`（它让**所有** JSON 的 `git diff` 只输出
  `Bin N -> M bytes`），改为 `data/rules/*.json` 显式 `-text`。**判定依据文件现在能看到行级改动。**
- CI：`actions/checkout@v7` / `actions/setup-python@v7`；矩阵三腿 → 两腿
  （`windows-latest`/3.12 与 `ubuntu-latest`/3.12）。
- `tests/test_gate/test_install_surface.py` 改用 `sys.stdlib_module_names`（3.10+），
  删掉 60+ 行手写 `STDLIB` 冻结名单。

### 文档

- **台账份数统一为 21**（README ×2、DEVELOPMENT ×1；CHANGELOG 见下「更正」）。
- **错误类型统一为「8 类错误 + 1 类干净对照 = 9 行覆盖度」**（README ×2、DEVELOPMENT、
  `data/README.md` 的「六类」）。
- README 版本表收敛到**当前最新**（v0.2.1 置顶，M6/M8 标为历史里程碑）；
  CI 声明改为具体 job 名。
- README 如实披露两项能力缺口：`--assertion` **只被记录、不参与判定**；
  `validate_judgment_semantics()` **未被 `pipeline.audit()` 调用**、`judgment_semantics` 恒空。
- `DEVELOPMENT.md`：`check_release.py` 注明为**外部 skill 脚本（不在本仓）**并补本仓等价自检命令。

### 规则集

- **无变更**。当前依据：阈值表 `1.0.0`（生效 2026-10-16，11 条中 9 verified / 2 pending）、
  错误类型覆盖度分母（8 类，`min_coverage` 之和 18 = `total_min_coverage`）。
- 新增两条**对撞测试**把「表」与「代码常量」钉在一起：`THR-001`/`THR-002` 的 `threshold`
  必须等于 `config.tolerance`；`error_types.json` 的 8 个 `min_coverage` 必须逐项等于
  `GeneratorConfig.min_coverage`。（此前只保证 JSON 内部自洽，改表不改判定。）

### 是否需要重跑历史报告

**否。** 判定算法、阈值、冻结台账与快照均未改动；本次只改退出码、打包数据面与文档。

### 更正

- `[0.1.0]` / `[0.2.0]` 段的台账份数原**多算了一份**（写作 22），实际冻结台账自 v0.1.0 起
  即为 **21 份**（`data/benchmarks` 只有到 `BENCH-021`）。本次把历史段数字就地更正为 21，
  以免读者按错误份数预期调用；判定语义与数据均未变动。
- `[0.2.0]` 段的「校验和」小节原为 4 行"待填"占位符，且随 tag 进了源码包。
  真实哈希一直在 Release 正文与 `sha256sums.txt` 里；本次改为指引行（见下节）。

### 校验和

各附件的 sha256 见 **Release 正文**与随附件分发的 `sha256sums.txt`；
本仓不复述数值，避免"仓库内自述"与"发布物"两份口径漂移（v0.2.0 曾因"待填"占位符
进源码包而产生误导）。

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

见 v0.2.0 的 **Release 正文**与随附件分发的 `sha256sums.txt`
（`hws-audit-cli-win64.exe` / `hws-audit-gui-win64.exe` / `hws-audit-source-v0.2.0.zip` / `demo.gif`）。

## [0.1.1] - 2026-10-18

回访修复：报告导出（`report.py` 单一渲染源 + CLI `--report/--report-formats` + GUI 导出按钮）、
首错编号对外统一 1 基、覆盖率键名修复、技术报告与演示 GIF 落仓。179 → 176+12 用例。
留档见 [plan/RELEASE-M7.md](plan/RELEASE-M7.md)。

### 规则集

- 无变更。当前依据：阈值表 `1.0.0`（生效 2026-10-16）

## [0.1.0] - 2026-10-16

首个发布版本：步骤级审计 + 首错锚定 + 三级判定语义 + 独立重算交叉验证 + 21 份植入真值基准。

### 规则集

- 当前依据：阈值表 `1.0.0`（生效 2026-10-16，9 verified / 2 pending）
- 真值台账 `data/benchmarks/BENCH-001..021`、LLM 兜底快照 `data/snapshots/`（模型默认关）