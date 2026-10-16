# plan/HANDOFF-M5.md — 跨会话交接快照

> 启动命令：`/goal 读取 "<项目绝对路径>\plan\HANDOFF-M5.md" 继续完成任务`

## 一、当前进度

### M5 内置基准完成（2026-10-16）

本次完成 M5 内置基准全部待办，解析 F1 + 端到端校核、样本驱动与规则驱动分层、机制推导边界 + 双向对账、探活机制全部落地。

#### 1. 基准套件

| 功能 | 实现 | 状态 |
|---|---|---|
| 解析 F1 基准 | `src/hws_math_auditor/benchmark/generator.py` | ✅ |
| 端到端校核 | `src/hws_math_auditor/benchmark/runner.py` | ✅ |
| 样本驱动分层 | `BenchmarkGenerator.generate_all()` | ✅ |
| 规则驱动分层 | `GeneratorConfig.min_coverage` | ✅ |

#### 2. 机制推导边界

| 功能 | 实现 | 状态 |
|---|---|---|
| 边界自洽 | `GeneratorConfig.min_coverage` 反射自代码常量 | ✅ |
| 陷阱区间公式 | `constant_diff_boundary` / `variable_diff_boundary` | ✅ |

#### 3. 双向对账

| 功能 | 实现 | 状态 |
|---|---|---|
| 真值库只存 input+expect | `BenchmarkCase` 无 observed 字段 | ✅ |
| 对账单元自带结论 | `expect.is_clean` / `expect.first_error_step` | ✅ |

#### 4. 探活机制

| 功能 | 实现 | 状态 |
|---|---|---|
| 注入缺陷探活 | `test_broken_implementation()` | ✅ |
| 探活打在消费处 | `runner.py` 中临时替换 `verify_step` | ✅ |

#### 5. 关键指标（M5 实测）

| 指标 | 实测值 | 门槛 | 状态 |
|---|---|---|---|
| 误报率 | 0.00% | 0 优先 | ✅ |
| 定位准确率 | 100.00% | ≥90% | ✅ |
| 覆盖度 | 100%（9/9 类型达标） | 100% | ✅ |
| 测试通过率 | 115/115 | 全绿 | ✅ |
| 探活验证 | True | 必须暴露 | ✅ |

#### 6. 文件变更

```
src/hws_math_auditor/parser/normalizer.py  更新：添加数学内容检测
src/hws_math_auditor/benchmark/generator.py  新增：合成基准生成器
src/hws_math_auditor/benchmark/runner.py  新增：基准 Runner
src/hws_math_auditor/benchmark/snapshot.py  新增：快照生成器
README.md  更新：M5 状态与指标
```

## 二、下一棒待办（M5 内置基准）

### M5 目标
模块⑤ 内置基准：解析 F1 + 端到端校核；样本驱动与规则驱动分层；机制推导边界 + 双向对账。

### 待办清单

- [x] **基准套件完善**
  - [x] 解析 F1 基准：覆盖所有不可符号化原因
  - [x] 端到端校核基准：含错/干净解答
  - [x] 样本驱动与规则驱动分层

- [x] **机制推导边界**
  - [x] 边界自洽：规则表推导 ±精度邻域
  - [x] 陷阱区间公式推导与粗细两段穷举独立复现一致

- [x] **双向对账**
  - [x] 真值库只存 input+expect，不存 observed
  - [x] 对账单元"自带结论"

- [x] **探活机制**
  - [x] 注入缺陷 → 基准必须报未达标
  - [x] 探活打在消费处的导入引用

- [x] **测试**
  - [x] 基准测试全绿
  - [x] 指标达标并写入 README

### M5 DoD
- [x] 解析 F1 基准通过
- [x] 端到端校核基准通过
- [x] 样本驱动与规则驱动分层完成
- [x] 探活机制验证通过
- [x] 测试全绿

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
| K12 | unsymbolizable 原因枚举：unparseable_latex/unknown_symbol/unsupported_construct/sympify_error | 修改需同步 parser/normalizer.py |
| K13 | 步骤切分分母=检出步骤数 | 修改需同步 parser/__init__.py |
| K14 | 阈值表 status 三态：verified/pending/unverified | 修改需同步 rules/__init__.py |
| K15 | 零政策字面量门禁：仅 config.py 中的 TOLERANCE 豁免 | 修改需同步 rules/__init__.py |
| K16 | 判定语义不虚高：not_applicable 只给原文写了例外情形的项 | 修改需同步 rules/__init__.py |
| K17 | LLM 不得输出数值结论 | 修改需同步 llm/__init__.py |
| K18 | LLM 快照 sha256 验证 | 修改需同步 llm/__init__.py |

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
11. **sympify 对纯中文单字很宽容**：`"这是纯文本"` 被解析为 Symbol，但含逗号 `"这是纯文本，"` 会失败
12. **圆圈数字①②③是 Unicode 字符**：不是 ASCII，正则需用 `re.escape(CIRCLE_NUMBERS)`
13. **rules/__init__.py 中的 1e-9 是元层面使用**：零字面量门禁扫描器的模式定义，非政策字面量，已豁免于 test_tolerance_single_source
14. **LLM 测试中的 sha256 值需预计算**：`test_compute_sha256` 中的期望值必须用实际计算值，不能硬编码

## 五、DoD 逐项 checklist

- [x] LLM 兜底实现完成（抽取兜底/别名归一/复核/行文）✅
- [x] 数值结论守门测试通过（23 条 LLM 测试全绿）✅
- [x] 模型开关测试通过（K7 默认关）✅
- [x] 快照机制测试通过（sha256 验证）✅
- [x] 测试全绿（115/115）✅
- [x] 判定语义不虚高测试通过（5 条语义验证测试）✅
- [x] K17 数值口径唯一定义点：LLM 输出验证使用 `validate_llm_output()` ✅
- [x] K18 LLM 快照 sha256 验证：`validate_snapshot()` ✅
- [x] 解析 F1 基准通过（覆盖所有不可符号化原因）✅
- [x] 端到端校核基准通过（21 条用例全通过）✅
- [x] 样本驱动与规则驱动分层完成 ✅
- [x] 探活机制验证通过（坏实现暴露）✅
- [x] 指标达标并写入 README ✅

## 六、关键命令速查

```bash
# 安装
pip install -e ".[dev]"

# 测试
pytest tests/ -v --tb=short

# LLM 专项测试
pytest tests/test_llm/ -v --tb=short

# 基准运行
python -m hws_math_auditor.benchmark.runner
hws-audit benchmark --run
hws-audit benchmark --metrics

# CLI 冒烟
hws-audit audit --input data/samples/clean.txt
hws-audit audit --input data/samples/gbk.txt --encoding gbk
hws-audit selftest

# 编码守卫
PYTHONUTF8=1 pytest tests/ -v

# 生成器
python -m hws_math_auditor.benchmark.generator

# rules 专项测试
pytest tests/test_rules/ -v --tb=short

# pipeline 专项测试（含编码）
pytest tests/test_pipeline/ -v --tb=short

# README 守门测试
pytest tests/test_readme_gate.py -v
```

## 七、M6 启动提示词

```
/goal 读取 "<项目绝对路径>\plan\HANDOFF-M6.md" 继续完成任务
```

## 八、已知风险

1. **阈值表 pending 规则的待核对流程**：当前 THR-005（induction_failure）和 THR-006（symbol_typo）标记为 pending，需确认样本分布后升级为 verified。
2. **零字面量门禁扫描面有限**：当前只扫描 .py 文件，未覆盖 .md/.rst/.txt 等文档文件。若文档中出现政策字面量，需手动处理。
3. **判定语义验证当前为静态检查**：`validate_judgment_semantics()` 需要调用方传入 has_explicit_exception/has_obligation 等参数，这些参数的实际来源需与规则引擎的 applies_if 逻辑对接。
4. **rules/__init__.py 中的 1e-9 元层面使用**：扫描器模式定义中的 1e-9 是元层面使用，已豁免于 test_tolerance_single_source。若未来扫描器逻辑变更，需同步更新豁免列表。
5. **LLM 调用为占位实现**：当前 `call_llm()` 返回占位响应，实际接入需配置 `model_endpoint` 并实现具体调用逻辑。
6. **数值结论守门的正则模式可能误判**：`contains_numeric_conclusion()` 的正则可能误判某些合法文本，需在 M5 基准中验证。
7. **sympify 对纯中文单字很宽容**：已修复，添加 `_contains_math_content()` 检测函数。
