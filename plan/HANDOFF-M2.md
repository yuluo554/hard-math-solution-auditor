# plan/HANDOFF-M2.md — 跨会话交接快照

> 启动命令：`/goal 读取 "<项目绝对路径>\plan\HANDOFF-M2.md" 继续完成任务`

## 一、当前进度

### M1 补做完成（2026-10-16）

本次补做针对 M1 审查中发现的 3 处实质性缺口和 3 处待确认项，全部修复：

#### 1. 新增边界用例（K8 阈值边界）

| 错误类型 | 描述 | 用例 |
|---|---|---|
| `constant_diff_boundary` | 常数差异恰好 1e-9（边界命中） | BENCH-019, BENCH-020 |
| `variable_diff_boundary` | 变量差异反例搜索（验证类） | BENCH-021 |

#### 2. 修复内容

| 问题 | 修复 | 文件 |
|---|---|---|
| README.md 缺失 | 创建 README.md，含基准指标、项目结构、K 编号、环境坑 | `README.md` |
| .gitattributes 已正确 | 确认 `data/snapshots/*` 和 `data/benchmarks/*` 已标 `text=-text` | `.gitattributes` ✅ |
| 编码守卫已存在 | 确认 `_ensure_utf8_stdio()` 在 cli.py 中 | `src/hws_math_auditor/cli.py` ✅ |
| Python 3.8 类型注解不兼容 | 添加 `from __future__ import annotations` 到 model/recalc | `src/hws_math_auditor/model/__init__.py`, `src/hws_math_auditor/recalc/__init__.py` |
| benchmark CLI 占位 | 接线到实际 runner，支持 `--run` 和 `--metrics` | `src/hws_math_auditor/cli.py` |
| 测试计数未更新 | 18→21 条用例，测试断言同步更新 | `tests/test_benchmark/test_generator.py` |

#### 3. 关键指标（M1 补做后实测）

| 指标 | 实测值 | 门槛 |
|---|---|---|
| 误报率 | 0.00% | 0 优先 |
| 定位准确率 | 100.00% | ≥90% |
| 覆盖度 | 100%（8/8 类型达标） | 100% |
| 测试通过率 | 36/36 | 全绿 |

### 错误类型覆盖（8/8 达标）

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

### 文件变更

```
README.md                              新建
.gitattributes                         确认正确（无变更）
src/hws_math_auditor/model/__init__.py  添加 __future__ 注解
src/hws_math_auditor/recalc/__init__.py 添加 __future__ 注解
src/hws_math_auditor/benchmark/generator.py 新增 2 类边界用例
src/hws_math_auditor/benchmark/runner.py  错误类型推断增强
src/hws_math_auditor/cli.py              benchmark CLI 接线
tests/test_benchmark/test_generator.py  测试计数 18→21
```

## 二、下一棒待办（M2 解析层）

### M2 目标
模块① 步骤切分与归一化：分层解析覆盖率如实报告（分母=检出步骤数）；`unsymbolizable` 语义锁进测试；非 UTF-8 编码不猜测（报错）。

### 待办清单

- [ ] **步骤切分增强**
  - [ ] 处理更多步骤编号格式（步骤1、1.、1)、1、① 等）
  - [ ] 处理无编号步骤（自然语言段落）
  - [ ] 处理嵌套步骤（子步骤、引理）
  - [ ] 添加"步骤数异常"检测（步骤数 < 2 或 > 20 时警告）

- [ ] **归一化增强**
  - [ ] 扩展 `strip_chinese_prefix()` 覆盖更多中文描述词
  - [ ] 处理 LaTeX 环境（\begin{align}...\end{align}）
  - [ ] 处理分数、根号、求和、积分等复杂表达式
  - [ ] 添加"归一化覆盖率"报告（成功归一化步骤数 / 总步骤数）

- [ ] **unsymbolizable 语义**
  - [ ] 定义 unsymbolizable 的分类（文本描述 / 图表引用 / 未知符号）
  - [ ] 为每类 unsymbolizable 提供替代处理策略
  - [ ] 锁进测试：unsymbolizable 步骤不参与验证，但计入报告

- [ ] **编码处理**
  - [ ] 非 UTF-8 文件报错而非猜测编码
  - [ ] 添加 `--encoding` 参数支持显式指定编码

- [ ] **测试**
  - [ ] 每解析器配生成器产出的样例回归
  - [ ] 边界用例：空输入、纯文本、纯 LaTeX、混合格式
  - [ ] 覆盖率报告测试

### M2 DoD
- [ ] 步骤切分覆盖率 ≥ 95%（生成器用例）
- [ ] 归一化成功率 ≥ 90%（生成器用例）
- [ ] unsymbolizable 语义锁进测试
- [ ] 非 UTF-8 编码报错测试通过
- [ ] 测试全绿

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
| K8 | 数值口径唯一定义点 1e-9 | 修改需同步 config.py |
| K9 | 覆盖度分母反射自代码常量 | 修改需同步 benchmark/generator.py |
| K10 | 快照 sha256 留档 | 修改需同步 data/snapshots/ |
| K11 | Python 3.8 兼容：`from __future__ import annotations` | 修改需同步所有含 `list[...]` 注解的文件 |

## 四、本机环境坑

1. **PyInstaller 5.x 打 GUI 崩**：必须 ≥6
2. **PySide6 6.7+ 需 Python ≥3.9**：3.8 上限 6.6.3.1
3. **`py` 启动器无视 venv**：README 用 `python -m pip`
4. **Windows 子进程输出注入 CRLF**：落盘前 `.replace("\r\n","\n")`
5. **`Path.write_text(newline=)` 是 3.10+**：3.8 用 `open(..., newline="\n")`
6. **`list[int]` 类型注解是 3.9+**：3.8 需 `from __future__ import annotations` 或 `List[int]`
7. **`py -X utf8` 是本机习惯、也是 CI 盲区**：本机加过 `-X utf8` 只证明"我们敲的那条命令"没编码问题，证明不了"子进程/CI/用户"的编码通路
8. **pip 被注册表系统代理污染**：`NO_PROXY="*" no_proxy="*" py -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple <pkg>`
9. **pyc 偶发损坏**：全程 `PYTHONDONTWRITEBYTECODE=1`；出怪错先清 `__pycache__`
10. **Git Bash 参数改写陷阱**：以 `/` 开头的参数会被 MSYS 静默转写成 Windows 路径

## 五、DoD 逐项 checklist

- [x] plan/00 状态表已回写 ✅
- [x] plan/02–06 已落盘 ✅
- [x] 项目骨架可 import ✅
- [x] 测试可收集（pytest --collect-only）✅
- [x] 测试全绿（36/36）✅
- [x] 合成生成器可复跑 ✅
- [x] 基准 runner 可运行 ✅
- [x] 预置快照 sha256 留档 ✅
- [x] README.md 已创建并含基准指标 ✅
- [x] .gitattributes 快照文件已标 `-text` ✅
- [x] 编码守卫已就位 ✅
- [x] 边界用例（constant_diff_boundary / variable_diff_boundary）已添加 ✅
- [x] benchmark CLI 已接线到实际 runner ✅
- [x] Python 3.8 兼容性已修复 ✅

## 六、关键命令速查

```bash
# 安装
pip install -e ".[dev]"

# 测试
pytest tests/ -v --tb=short

# 基准运行
python -m hws_math_auditor.benchmark.runner
hws-audit benchmark --run
hws-audit benchmark --metrics

# CLI 冒烟
hws-audit audit --input data/samples/clean.txt
hws-audit selftest

# 编码守卫
PYTHONUTF8=1 pytest tests/ -v

# 生成器
python -m hws_math_auditor.benchmark.generator
```

## 七、M2 启动提示词

```
/goal 读取 "<项目绝对路径>\plan\HANDOFF-M2.md" 继续完成任务
```

## 八、已知风险

1. **边界用例的"边界"语义**：`constant_diff_boundary` 用例中 `1e-9` 恰好命中 tolerance，但 `1e-9` 在浮点运算中可能因精度问题产生微小偏差。当前测试通过，但需持续监控。
2. **`variable_diff_boundary` 用例**：`1e-9*x` 在 x=0 时 diff=0，在 x=1 时 diff=1e-9。反例搜索范围 {-3,-2,-1,0,1,2,3} 中 x=1 会命中，但 x=0 不会。这测试的是"反例搜索能找到非零 diff"的路径。
3. **错误类型推断**：runner 中 `error_type_detected` 基于证据文本的中文关键词匹配，若 verifier 的 evidence 文本变更，需同步更新。
