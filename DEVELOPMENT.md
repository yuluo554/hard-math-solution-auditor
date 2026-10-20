# DEVELOPMENT — hard-math-solution-auditor 开发细节索引

> 本文件**只做索引与现状摘要**，不复制 `plan/` 下的内容（避免双份维护）。
> 里程碑 M0–M7 与 DoD 的**唯一状态表**在 [plan/00-README总览.md](plan/00-README总览.md)；
> 算法与口径在 [plan/02-算法与口径说明.md](plan/02-算法与口径说明.md)；
> 架构与 K 口径清单（唯一一份）在 [plan/06-架构与技术选型.md](plan/06-架构与技术选型.md)。
> 面向用户的说明、判定依据与已知限制在 [README.md](README.md)。

---

## 一、M0–M7 里程碑与 DoD（索引）

| 里程碑 | 本文档指向 |
| --- | --- |
| M0 计划与骨架 / M1 数据先行 / M2 解析层 | [plan/00-README总览.md](plan/00-README总览.md)（唯一状态表） |
| M3 知识与规则层 / M4 LLM 兜底层 / M5 内置基准 | [plan/00-README总览.md](plan/00-README总览.md)、[plan/03-基准套件设计.md](plan/03-基准套件设计.md) |
| M6 交付与发布（v0.1.0） | [plan/RELEASE-M6.md](plan/RELEASE-M6.md) |
| M7 回访修复（v0.1.1） | [plan/RELEASE-M7.md](plan/RELEASE-M7.md) |
| M8 元数据与报告头（v0.2.0） | [CHANGELOG.md](CHANGELOG.md)（规则集 `meta.review` + 报告头版本） |
| M9 补丁：退出码/打包/自述（v0.2.1） | [plan/RELEASE-M9.md](plan/RELEASE-M9.md) |

DoD 明细与逐项证据在 [plan/04-测试与验收.md](plan/04-测试与验收.md)；
M6/M7 的 push/run 对账分别在两份 RELEASE 文件的第五节。

## 二、按需查哪份文档

| 想了解 | 看这里 |
| --- | --- |
| 题目定义与交付物清单 | [plan/01-题目详细定义.md](plan/01-题目详细定义.md) |
| 步骤归一化、三级语义、首错锚定、独立重算 | [plan/02-算法与口径说明.md](plan/02-算法与口径说明.md) |
| 基准套件设计（8 类错误类型 + 1 类干净对照、覆盖度门控） | [plan/03-基准套件设计.md](plan/03-基准套件设计.md) |
| 测试分层与验收口径 | [plan/04-测试与验收.md](plan/04-测试与验收.md) |
| 交付形态、双 exe 构建、发布流程 | [plan/05-发布与交付.md](plan/05-发布与交付.md) |
| 分层架构、目录、K1–K18 口径清单 | [plan/06-架构与技术选型.md](plan/06-架构与技术选型.md) |
| 阶段交接（M0→M6 逐棒唯一入口） | [plan/HANDOFF-M1.md](plan/HANDOFF-M1.md) … [plan/HANDOFF-M6.md](plan/HANDOFF-M6.md) |
| 数据来源、渠道与 status 台账 | [data/README.md](data/README.md) |
| 技术报告（材料固化） | [docs/技术报告.md](docs/技术报告.md) |

## 三、架构分层（摘要，细节见 plan/06）

```
src/hws_math_auditor/
├── __main__.py / cli.py    CLI 入口与命令集（audit / benchmark / selftest）
├── config.py               单源配置（tolerance = 1e-9，K8 唯一定义点）
├── parser/                 ① 步骤切分与归一化（unsymbolizable 4 类原因）
├── verifier/               ② 步骤级符号验证（三级语义 ok / invalid / unverifiable）
├── locator/                ③ 首错锚定（最小索引 + 污染 vs 独立失败）
├── recalc/                 ④ 独立重算（与符号路径实现独立）
├── rules/                  ⑤ 阈值表 + status 门控 + 零政策字面量门禁
├── llm/                    ⑥ LLM 兜底（默认关，数值结论守门）
├── pipeline.py             编排层（audit / selftest）
├── gui/                    桌面报告形态（只消费 pipeline，零判定）
├── report.py               报告渲染单源（MD / JSON / HTML）
└── benchmark/              ⑦ 合成生成器（--check 位级一致）+ Runner（含探活）+ 快照
```

`data/` 只存输入与期望（真值纪律 K3：不存 observed）；`data/snapshots/` 是可复跑快照。

## 四、CI 矩阵

工作流：`.github/workflows/ci.yml`，两矩阵 —— `windows-latest` × py3.12、
`ubuntu-latest` × py3.12（`fail-fast: false`）。v0.2.1 起 `windows-latest × py3.8`
腿随 floor 抬到 3.12 而移除。job env 统一 `PYTHONUTF8=1`、
`PYTHONDONTWRITEBYTECODE=1`（本机习惯 `py -X utf8` 是 CI 盲区）。
步骤：`python -m pip install -e ".[dev]"` → `pytest`。

本机等价命令（用 `py`）：

```bash
py -3.12 -m pytest tests/ -v --tb=short
python -m hws_math_auditor.benchmark.generator --check     # 冻结台账位级一致
```

## 五、基准与冻结纪律

- 冻结台账 `data/benchmarks/BENCH-001..021` 由生成器产出，
  `python -m hws_math_auditor.benchmark.generator --check` 重生成并**位级比对**。
- 覆盖度分母反射自代码常量（K9），不手写；误报率 0 是硬门（K4）。
- 探活（可证伪）：坏实现必须被基准暴露，见 [plan/03-基准套件设计.md](plan/03-基准套件设计.md)。
- 重新生成（仅在改动生成器后）：
  `generator --write` → `benchmark.snapshot`。

## 六、构建双 exe 与发布对账

```bash
py -3.12 -m PyInstaller tools/pyinstaller-cli.spec --clean
py -3.12 -m PyInstaller tools/pyinstaller-gui.spec --clean
```

| 项 | 值 |
| --- | --- |
| 版本 | `v0.2.1`（包版本 `0.2.1`，`pyproject.toml`） |
| 发布留档 | [plan/RELEASE-M6.md](plan/RELEASE-M6.md)、[plan/RELEASE-M7.md](plan/RELEASE-M7.md)、[plan/RELEASE-M8.md](plan/RELEASE-M8.md)、[plan/RELEASE-M9.md](plan/RELEASE-M9.md) |
| 校验 | **外部 skill 脚本**（`check_release.py` 不在本仓，来自作者的发布 skill）；本仓可跑的等价判据见下 |

本仓内的发布前自检（不依赖外部脚本）：

```bash
python -m hws_math_auditor.benchmark.generator --check     # 冻结台账位级一致
python -m pytest tests/ -q                                 # 全量测试
python -m build && python -c "import zipfile,glob;n=zipfile.ZipFile(glob.glob('dist/*.whl')[0]).namelist();print('data entries:', sum('_data/' in x for x in n))"
```

> exe 含构建期 PE 时间戳，**同机两次构建哈希即不同**；承诺的是「同一棵树 → 同一产物语义」，
> 不是跨机器逐字节一致。`dist/` 与 `release/` 被 `.gitignore` 排除，哈希留档在 RELEASE 文件。

## 七、本机环境坑（改构建/界面相关代码前先读）

1. `PyInstaller` 必须 ≥6（5.x 打 GUI 崩）。
2. `PySide6` 自 v0.2.1 起不再设上限（`>=6.6.3.1`）；旧上限 `<6.7` 是 Python 3.8 的连带约束，
   floor 抬到 3.12 后已移除。**GUI 代码尚未在 6.7+ 上做人工目检**，升级前请先跑 `--selftest`。
3. `py` 启动器无视 venv，README 与构建脚本统一用 `python -m pip`。
4. Windows 子进程输出注入 CRLF：落盘前 `.replace("\r\n", "\n")`。
5. `Path.write_text(newline=)` 是 3.10+ API；`generator._write_text_lf` 仍用
   `open(..., newline="\n")` 以保持跨平台位级一致（floor 已 ≥3.12，此写法继续有效，无需改）。
6. `tools/*.spec` 第 15 行的 `pathto=` 是 `pathex=` 的拼写错误，被 PyInstaller 的
   `**_kwargs` 静默吞掉——**是死配置但无害**（PyInstaller 从脚本自身位置解析包）。
   不要"顺手修正"：改后必须重跑构建并**运行产物**，不是看构建日志。
7. 打包后数据路径不同：`sys._MEIPASS`，见 `datadir.is_frozen()` 与 spec 的 `datas`。
8. pip 常规安装的数据在 `<site-packages>/hws_math_auditor/_data/`（`setup.py` 的 `build_py`
   钩子从仓根 `data/` 拷入）；`src/hws_math_auditor/_data/` 是构建产物，已入 `.gitignore`。