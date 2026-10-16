# plan/HANDOFF-M1.md — 跨会话交接快照

> 启动命令：`/goal 读取 "<项目绝对路径>\plan\HANDOFF-M1.md" 继续完成任务`

## 一、当前进度

### 已完成
- ✅ plan/00–06 全部定稿（v1）
- ✅ 项目骨架：`src/hws_math_auditor/` 完整模块结构
- ✅ pyproject.toml、.gitattributes、.gitignore
- ✅ 核心代码：parser / verifier / locator / recalc / pipeline / cli
- ✅ 测试骨架：tests/ 下各模块测试文件
- ✅ 数据规则：data/rules/error_types.json
- ✅ **合成生成器**：`src/hws_math_auditor/benchmark/generator.py`（18 条用例，覆盖 6 类错误）
- ✅ **真值台账**：`data/benchmarks/`（18 个 BENCH-*.json，只存 input+expect）
- ✅ **预置快照**：`data/snapshots/`（18 个 BENCH-*.json，含 sha256 留档）
- ✅ **基准 runner**：`src/hws_math_auditor/benchmark/runner.py`（加载/运行/指标）
- ✅ **快照生成器**：`src/hws_math_auditor/benchmark/snapshot.py`
- ✅ **基准测试**：`tests/test_benchmark/test_generator.py`（14 个测试，全绿）

### 待完成（M2 起）
- ⬜ 模块① 解析：步骤切分与归一化（已有基础，需继续完善）
- ⬜ 模块②③④ 引擎：符号验证 / 首错锚定 / 独立重算（已有基础，需继续完善）
- ⬜ 模型接入层：openai_compat / llama_cpp / omni_infer（可插拔，默认关）
- ⬜ GUI：PySide6 主窗口（审计输入/结果展示/设置页）
- ⬜ 打包：PyInstaller ≥6，免安装 exe

## 二、关键指标（M1 实测）

| 指标 | 实测值 | 门槛 |
|---|---|---|
| 误报率 | 0.00% | 0 优先 |
| 定位准确率 | 100.00% | ≥90% |
| 覆盖度 | 100%（6/6 类型达标） | 100% |
| 测试通过率 | 36/36 | 全绿 |

## 三、既定口径清单（K 编号）

| K# | 口径 | 动了会打挂测试 |
|---|---|---|
| K1 | 三级语义：ok/invalid/unverifiable | 修改需同步 model/verdict.py |
| K2 | 首错锚定唯一性：最小序号 | 修改需同步 locator/first_error.py |
| K3 | 真值库只存 input+expect，不存 observed | 修改需同步 benchmark/ground_truth.py |
| K4 | 误报率 0 优先 | 修改需同步 benchmark/metrics.py |
| K5 | 不可符号化标 unsymbolizable | 修改需同步 parser/normalizer.py |
| K6 | 独立重算与符号路径独立 | 修改需同步 recalc/numeric_recalc.py |
| K7 | 模型开关默认关 | 修改需同步 config.py |
| K8 | 数值口径唯一定义点 1e-9 | 修改需同步 recalc/numeric_recalc.py |
| K9 | 覆盖度分母反射自代码常量 | 修改需同步 benchmark/generator.py |
| K10 | 快照 sha256 留档 | 修改需同步 data/snapshots/ |

## 四、本机环境坑

1. **PyInstaller 5.x 打 GUI 崩**：必须 ≥6
2. **PySide6 6.7+ 需 Python ≥3.9**：3.8 上限 6.6.3.1
3. **`py` 启动器无视 venv**：README 用 `python -m pip`
4. **Windows 子进程输出注入 CRLF**：落盘前 `.replace("\r\n","\n")`
5. **`Path.write_text(newline=)` 是 3.10+**：3.8 用 `open(..., newline="\n")`

## 五、DoD 逐项 checklist

- [x] plan/00 状态表已回写 ✅
- [x] plan/02–06 已落盘 ✅
- [x] 项目骨架可 import ✅
- [x] 测试可收集（pytest --collect-only）✅
- [x] 测试全绿（36/36）✅
- [x] 合成生成器可复跑 ✅
- [x] 基准 runner 可运行 ✅
- [x] 预置快照 sha256 留档 ✅

## 六、关键命令速查

```bash
# 安装
pip install -e ".[dev]"

# 测试
pytest tests/ -v --tb=short

# 基准运行
python -m hws_math_auditor.benchmark.generator
python -m hws_math_auditor.benchmark.runner

# 快照生成
python -m hws_math_auditor.benchmark.snapshot

# CLI 冒烟
hws-audit audit --input data/samples/clean.txt
hws-audit selftest

# 编码守卫
PYTHONUTF8=1 pytest tests/ -v
```
