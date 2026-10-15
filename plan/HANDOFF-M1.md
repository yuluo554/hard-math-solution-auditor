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

### 待完成（M1 数据先行）
- ⬜ 合成生成器（`src/hws_math_auditor/benchmark/generator.py`）
- ⬜ 真值台账（`data/benchmarks/`）
- ⬜ 预置模型输出快照（`data/snapshots/`）
- ⬜ 基准 runner（`src/hws_math_auditor/benchmark/runner.py`）
- ⬜ 演示样例（`data/samples/`）

## 二、下一棒待办

1. **实现合成生成器**：按 plan/03 设计，生成 15+ 条基准用例（含 3 条干净 + 12 条含错）
2. **实现基准 runner**：加载真值台账，运行引擎，计算指标
3. **创建预置快照**：按 data/README 格式，含模型名/版本/参数/sha256
4. **创建演示样例**：干净解答 + 含错解答各 1 份
5. **实现模型接入层**：openai_compat / llama_cpp / omni_infer（可插拔，默认关）
6. **实现 GUI**：PySide6 主窗口（审计输入/结果展示/设置页）

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

- [ ] plan/00 状态表已回写 ✅
- [ ] plan/02–06 已落盘 ✅
- [ ] 项目骨架可 import ✅
- [ ] 测试可收集（pytest --collect-only）
- [ ] 双解释器（3.8 + 3.12）测试全绿
- [ ] 合成生成器可复跑
- [ ] 基准 runner 可运行
- [ ] 预置快照 sha256 留档

## 六、关键命令速查

```bash
# 安装
pip install -e ".[dev]"

# 测试
pytest tests/ -v --tb=short

# 双解释器
py -3.8 -m pytest tests/ -v --tb=short
py -3.12 -m pytest tests/ -v --tb=short

# CLI 冒烟
hws-audit audit --input data/samples/clean.txt
hws-audit selftest

# 编码守卫
PYTHONUTF8=1 pytest tests/ -v
```
