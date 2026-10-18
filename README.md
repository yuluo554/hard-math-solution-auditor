# HWS 难题解答步骤级审计与错误定位器

> 难题解答步骤级审计与错误定位器 —— 纯确定性、零模型依赖、可离线复跑。

## 项目状态

| 里程碑 | 状态 | DoD |
|---|---|---|
| M1 数据先行 | ✅ 完成 | 合成生成器、真值台账、预置快照、基准 Runner |
| M2 解析层 | ✅ 完成 | 步骤切分与归一化、unsymbolizable 分类 |
| M3 知识与规则层 | ✅ 完成 | 阈值表、status 门控、零政策字面量门禁、判定语义不虚高 |
| M4 LLM 兜底层 | ✅ 完成 | 抽取兜底 / 别名归一 / 复核 / 行文 + 数值结论守门 + 模型开关默认关 |
| M5 内置基准 | ✅ 完成 | 基准套件达标 + 探活可证伪 + 冻结台账位级一致 |
| M6 交付（构建） | ✅ 完成 | CLI + GUI 双 exe 构建、冻结态自检、sha256 留档 |
| M6 发布（GitHub） | ✅ 完成 | tag `v0.1.0` + Release 三附件 + `plan/RELEASE-M6.md` 留档 |
| **M7 回访修复（v0.1.1）** | ✅ 完成 | 报告导出真实现（MD/JSON/HTML）+ 首错 1 基统一 + 技术报告与演示 GIF + `check_release.py` 0 FAIL |

> **CI 状态**：三矩阵（windows 3.8 / windows 3.12 / ubuntu 3.12）**全绿**；
> M6 首推的 push/run 对账见 `plan/RELEASE-M6.md` 第五节，M7（v0.1.1）的 run 见 `plan/RELEASE-M7.md` 第五节。
>
> **当前版本**：**v0.1.1**（[Release](https://github.com/yuluo554/hard-math-solution-auditor/releases/tag/v0.1.1)）。

## 快速开始

```bash
# 安装
pip install -e ".[dev]"

# 冻结态自检（数据可达 + 台账未漂移 + 引擎自洽）
hws-audit selftest

# 运行基准
hws-audit benchmark --run

# 审计单个解答
hws-audit audit --input data/samples/clean_solution.txt
hws-audit audit --input data/samples/dirty_solution.txt --assertion "x = 2 or x = 3"

# 审计并导出三种格式报告（Markdown / JSON / HTML，同一渲染源，HTML 零外链）
hws-audit audit --input data/samples/dirty_solution.txt --report audit-report

# 全量测试
pytest tests/ -v
```

### 下载即用

Release 附件（Windows 64 位，免安装）：

| 附件 | 说明 |
|---|---|
| `hws-audit-cli-win64.exe` | 命令行版（含 `--report` 报告导出） |
| `hws-audit-gui-win64.exe` | 桌面版（审计 / 设置 / 导出报告） |
| `sha256sums.txt` | 哈希校验 |
| `hws-audit-source-<tag>.zip` | 源码包（`git archive` from tag 树） |
| `demo.gif` | 桌面版演示（选择文件 → 判定表 → 导出报告） |

```powershell
# 校验下载件
certutil -hashfile hws-audit-cli-win64.exe SHA256
# 与 sha256sums.txt 中的值逐位比对

# 免安装自检 + 冒烟
.\hws-audit-cli-win64.exe selftest
.\hws-audit-cli-win64.exe benchmark --run
```

## 退出码语义

| 码 | 含义 |
|---|---|
| 0 | 成功（干净解答 / 基准达标 / 自检通过） |
| 1 | 检出问题（解答含错 / 基准未达标 / 冻结台账漂移） |
| 2 | 用法与输入不可用（缺文件 / 未知编码 / 缺必需旗标） |

## 报告导出

```bash
# 三种格式一次写出（同一渲染源；HTML 零外链，断网可开）
hws-audit audit --input data/samples/dirty_solution.txt --report audit-report
# → audit-report.md / audit-report.json / audit-report.html

# 只出一种
hws-audit audit --input data/samples/dirty_solution.txt --report audit-report --report-formats md
```

桌面版对应按钮：**「导出报告（MD + JSON + HTML）」**（审计完成后可用）。

## 核心特性

- **步骤级审计**：逐步骤符号等价性验证，非整体答案对错
- **三级裁决语义**：ok / invalid / unverifiable，判定不虚高
- **首错锚定**：最小索引 + 污染 vs 独立失败分类
- **零假阳性优先**：干净解永不被标记为错误（K4）
- **真值库纪律**：只存 input + expect，不存 observed（K3）
- **冻结台账位级一致**：`generator --check` 校验台账未被手改
- **覆盖度门控**：分母反射自代码常量，不手写（K9）
- **快照 sha256 归档**：离线可复跑（K10）

## 基准指标（本机实测）

| 指标 | 实测值 | 门槛 |
|---|---|---|
| 误报率 | 0.00% | 0 优先 |
| 定位准确率 | 100.00% | ≥90% |
| 覆盖度 | 100%（9/9 类型达标） | 100% |
| 测试通过率 | 176/176 | 全绿（v0.1.1 新增 12 条报告导出测试） |
| 冻结台账位级一致 | 通过 | 通过 |
| 零政策字面量门禁 | 通过（扫描面 37 文件） | 通过 |
| 字节冻结（无 CR） | 通过 | 通过 |
| 探活可证伪 | 通过（坏实现被暴露） | 通过 |

### 错误类型覆盖

| 错误类型 | 最低覆盖 | 实测覆盖 | 状态 |
|---|---|---|---|
| illegal_algebra | 3 | 3 | ✅ |
| divide_by_zero | 3 | 3 | ✅ |
| dimension_mismatch | 2 | 2 | ✅ |
| induction_failure | 2 | 2 | ✅ |
| boundary_omission | 2 | 2 | ✅ |
| symbol_typo | 3 | 3 | ✅ |
| constant_diff_boundary | 2 | 2 | ✅ |
| variable_diff_boundary | 1 | 1 | ✅ |
| clean | 3 | 3 | ✅ |

## 交付物

构建产物（`dist/`，不入仓；发布时作为 Release 附件上传）：

| 文件 | 大小 | SHA256 |
|---|---|---|
| hws-audit-cli-win64.exe | 见 `dist/sha256sums.txt` | 见 `dist/sha256sums.txt` |
| hws-audit-gui-win64.exe | 见 `dist/sha256sums.txt` | 见 `dist/sha256sums.txt` |

> **说明**：exe 含构建期 PE 时间戳，**同机两次构建哈希即不同**——
> 承诺的是"同一棵树 → 同一产物语义"，不是"跨机逐字节一致"。
> `dist/` 被 `.gitignore` 排除；哈希留档在发布留档 `plan/RELEASE-M6.md`。

## 项目结构

```
src/hws_math_auditor/
├── __init__.py          # 包入口
├── __main__.py          # CLI 入口（薄模块，绝对导入）
├── cli.py               # CLI 命令集（audit / benchmark / selftest）
├── config.py            # 单源配置（tolerance = 1e-9，K8 唯一定义点）
├── model/__init__.py    # 数据模型（Step / Verdict / AuditReport）
├── parser/              # 模块① 步骤切分与归一化
│   ├── __init__.py
│   └── normalizer.py
├── verifier/__init__.py # 模块② 步骤级符号验证（三级语义）
├── locator/__init__.py  # 模块③ 首错锚定与污染分类
├── recalc/__init__.py   # 模块④ 独立重算（与符号路径实现独立）
├── rules/__init__.py    # 模块⑤ 阈值表 + status 门控 + 零字面量门禁
├── llm/__init__.py      # 模块⑥ LLM 兜底（默认关，数值结论守门）
├── pipeline.py          # 编排层（audit / selftest）
├── gui/                 # 桌面报告形态
│   ├── __init__.py      # 主窗口（只消费 pipeline，零判定）
│   └── __main__.py      # GUI 入口（未知参数 exit 2）
└── benchmark/           # 模块⑦ 内置基准套件
    ├── generator.py     # 合成生成器（含 --check 位级一致校验）
    ├── runner.py        # 基准 Runner（含探活）
    └── snapshot.py      # 快照生成器
```

## 关键纪律（K 编号）

> "动了会打挂测试"的既定口径。改任一条都要同步对应实现与测试。

| K# | 口径 | 动了会打挂测试 |
|---|---|---|
| K1 | 三级语义：ok / invalid / unverifiable | model、verifier |
| K2 | 首错锚定唯一性：最小序号 + 污染分类 | locator |
| K3 | 真值库只存 input + expect，不存 observed | benchmark/generator、benchmark/runner |
| K4 | 误报率 0 优先 | benchmark/runner |
| K5 | 不可符号化标 unsymbolizable | parser/normalizer |
| K6 | 独立重算与符号路径实现独立 | recalc |
| K7 | 模型开关默认关 | config、llm |
| K8 | 数值口径唯一定义点 = `config.tolerance` | config、recalc、verifier、benchmark/generator |
| K9 | 覆盖度分母反射自代码常量 | benchmark/generator |
| K10 | 快照 sha256 留档且与 output 自洽 | data/snapshots、benchmark/snapshot |
| K11 | Python 3.8 兼容：`from __future__ import annotations` | 所有含 `list[...]` 注解的文件 |
| K12 | unsymbolizable 原因枚举（4 类） | parser/normalizer |
| K13 | 步骤切分分母 = 检出步骤数 | parser |
| K14 | 阈值表 status 三态：verified / pending / unverified | rules、data/rules/thresholds.json |
| K15 | 零政策字面量门禁（仅 config.py 与 tests/ 豁免） | rules |
| K16 | 判定语义不虚高：not_applicable 只给原文写了例外情形的项 | rules |
| K17 | LLM 不得输出数值结论 | llm |
| K18 | LLM 快照 sha256 验证 | llm |

## 本机环境坑

1. **PyInstaller 5.x 打 GUI 崩**：必须 ≥6
2. **PySide6 6.7+ 需 Python ≥3.9**：3.8 上限 6.6.3.1
3. **`py` 启动器无视 venv**：README 用 `python -m pip`
4. **Windows 子进程输出注入 CRLF**：落盘前 `.replace("\r\n","\n")`
5. **`Path.write_text(newline=)` 是 3.10+**：3.8 用 `open(..., newline="\n")`
6. **`list[int]` 类型注解是 3.9+**：3.8 需 `from __future__ import annotations`
7. **sympify 对纯中文单字很宽容**：已修复，添加 `_contains_math_content()` 检测
8. **PyInstaller 打包后数据路径不同**：`sys._MEIPASS`，见 `cli._resolve_data_dir()`

## 已知限制（边界与非目标）

- **模型接入为可插拔开关，默认关**：不随包分发权重；`call_llm()` 当前为占位实现，
  实际接入需配置 `model_endpoint`。关闭开关时全功能（审计/基准/自检）可用。
- **公开题库回归集未接入**：许可需逐库核对，当前只用程序化合成题。
- **零字面量门禁扫描面**：只扫 `.py`，不覆盖 `.md` / `.rst` / `.txt`。
- **判定语义验证为静态检查**：`validate_judgment_semantics()` 需调用方传入
  `has_explicit_exception` / `has_obligation` 等参数。
- **阈值表 THR-005 / THR-006 为 pending**：待确认样本分布后升级为 verified。
- **GUI 未做交互式人工测试**：构建成功且 `--selftest` 通过，未实际点开窗口操作。

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/ -v --tb=short

# 冻结台账位级一致校验
python -m hws_math_auditor.benchmark.generator --check

# 重新生成基准台账与快照（改动生成器后才需要）
python -m hws_math_auditor.benchmark.generator --write
python -m hws_math_auditor.benchmark.snapshot

# 构建双 exe（需 Python ≥3.9 通道 + PyInstaller ≥6）
py -3.12 -m PyInstaller tools/pyinstaller-cli.spec --clean
py -3.12 -m PyInstaller tools/pyinstaller-gui.spec --clean
```

## 许可证

MIT，见 [LICENSE](LICENSE)。
