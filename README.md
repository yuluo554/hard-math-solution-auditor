# HWS 难题解答步骤级审计与错误定位器

> 难题解答步骤级审计与错误定位器 —— 纯确定性、零模型依赖、可离线复跑。

## 项目状态

| 里程碑 | 状态 | DoD |
|---|---|---|
| M1 数据先行 | ✅ 完成 | 合成生成器、真值台账、预置快照、基准 Runner |
| M2 解析层 | ✅ 完成 | 步骤切分与归一化、unsymbolizable 分类 |
| M3 引擎层 | ✅ 完成 | 符号验证 / 首错锚定 / 独立重算 |
| M4 基准套件 | ✅ 完成 | 基准套件达标 + 探活全红 |
| M5 交付 | ✅ 完成 | CLI + 桌面报告、打包 exe |
| M6 发布 | ⬜ 待启动 | GitHub Release（三件套） |

## 快速开始

```bash
# 安装
pip install -e ".[dev]"

# 运行基准
hws-audit benchmark --run

# 审计单个解答
hws-audit audit --input solution.txt --assertion "x = 5"

# 冻结态自检
hws-audit selftest

# 全量测试
pytest tests/ -v
```

## 核心特性

- **步骤级审计**：逐步骤符号等价性验证，非整体答案对错
- **三级裁决语义**：ok / invalid / unverifiable，判定不虚高
- **首错锚定**：最小索引 + 污染 vs 独立失败分类
- **零假阳性优先**：干净解永不被标记为错误（K4）
- **真值库纪律**：只存 input + expect，不存 observed（K3）
- **覆盖度门控**：分母反射自代码常量，不手写（K9）
- **快照 sha256 归档**：离线可复跑（K10）

## 基准指标（M5 实测）

| 指标 | 实测值 | 门槛 |
|---|---|---|
| 误报率 | 0.00% | 0 优先 |
| 定位准确率 | 100.00% | ≥90% |
| 覆盖度 | 100%（9/9 类型达标） | 100% |
| 测试通过率 | 115/115 | 全绿 |

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

## 项目结构

```
src/hws_math_auditor/
├── __init__.py          # 包入口
├── __main__.py          # CLI 入口（薄模块）
├── cli.py               # CLI 命令集
├── config.py            # 单源配置（tolerance = 1e-9）
├── model.py             # 数据模型（Step, Verdict, FirstErrorResult）
├── parser/              # 模块① 步骤切分与归一化
│   ├── __init__.py
│   ├── splitter.py      # 步骤切分
│   └── normalizer.py    # 表达式归一化
├── verifier/            # 模块② 步骤级符号验证
├── locator/             # 模块③ 错误定位与首错锚定
├── recalc/              # 模块④ 独立重算
├── pipeline/            # 审计管线编排
└── benchmark/           # 模块⑤ 基准套件
    ├── generator.py     # 合成生成器
    ├── runner.py        # 基准 Runner
    └── snapshot.py      # 快照生成器
```

## 关键纪律（K 编号）

| K# | 口径 | 动了会打挂测试 |
|---|---|---|
| K1 | 三级语义：ok/invalid/unverifiable | 修改需同步 model/verdict.py |
| K2 | 首错锚定唯一性：最小序号 | 修改需同步 locator/first_error.py |
| K3 | 真值库只存 input+expect，不存 observed | 修改需同步 benchmark/ground_truth.py |
| K4 | 误报率 0 优先 | 修改需同步 benchmark/metrics.py |
| K5 | 不可符号化标 unsymbolizable | 修改需同步 parser/normalizer.py |
| K6 | 独立重算与符号路径独立 | 修改需同步 recalc/numeric_recalc.py |
| K7 | 模型开关默认关 | 修改需同步 config.py |
| K8 | 数值口径唯一定义点 1e-9 | 修改需同步 config.py |
| K9 | 覆盖度分母反射自代码常量 | 修改需同步 benchmark/generator.py |
| K10 | 快照 sha256 留档 | 修改需同步 data/snapshots/ |

## 本机环境坑

1. **PyInstaller 5.x 打 GUI 崩**：必须 ≥6
2. **PySide6 6.7+ 需 Python ≥3.9**：3.8 上限 6.6.3.1
3. **`py` 启动器无视 venv**：README 用 `python -m pip`
4. **Windows 子进程输出注入 CRLF**：落盘前 `.replace("\r\n","\n")`
5. **`Path.write_text(newline=)` 是 3.10+**：3.8 用 `open(..., newline="\n")`

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/ -v --tb=short

# 生成基准用例
python -m hws_math_auditor.benchmark.generator

# 运行基准
python -m hws_math_auditor.benchmark.runner

# 生成快照
python -m hws_math_auditor.benchmark.snapshot
```

## 许可证

MIT
