# plan/HANDOFF-M3.md — 跨会话交接快照

> 启动命令：`/goal 读取 "<项目绝对路径>\plan\HANDOFF-M3.md" 继续完成任务`

## 一、当前进度

### M2 解析层完成（2026-10-16）

本次完成 M2 解析层全部待办，步骤切分与归一化能力显著增强。

#### 1. 步骤切分增强

| 功能 | 实现 | 状态 |
|---|---|---|
| 圆圈编号（①②③） | `STEP_PATTERN_CIRCLE` 正则 | ✅ |
| 阿拉伯数字编号（1. / 1、 / 1)） | `STEP_PATTERN_ARABIC` 正则 | ✅ |
| 混合编号 | 阿拉伯+圆圈优先级处理 | ✅ |
| 无编号段落 | `_split_by_paragraph()` 按空行切分 | ✅ |
| 步骤数异常检测 | <2 或 >20 触发段落切分 | ✅ |
| 多种格式 | 1. / 1、 / 1) / 1） / 1: / 1： | ✅ |

#### 2. 归一化增强

| 功能 | 实现 | 状态 |
|---|---|---|
| normalize_step() 占位修复 | 接入 `normalize_step_expr()` | ✅ |
| 中文前缀扩展 | 新增 15 个前缀（化简、计算、验证、令、设、代入等） | ✅ |
| LaTeX 环境处理 | `extract_latex_environments()` 支持 align/equation/gather/matrix/cases | ✅ |
| 不可符号化分类 | 4 类：unparseable_latex/unknown_symbol/unsupported_construct/sympify_error | ✅ |
| 覆盖率报告 | `compute_coverage()` 分母=检出步骤数，含原因分布 | ✅ |

#### 3. unsymbolizable 语义

| 原因 | 触发条件 | 处理策略 |
|---|---|---|
| `unparseable_latex` | LaTeX 转换失败 | 不参与验证，计入报告 |
| `unknown_symbol` | sympify 无法识别符号 | 不参与验证，计入报告 |
| `unsupported_construct` | 不支持的构造（如 matrix 环境） | 不参与验证，计入报告 |
| `sympify_error` | 其他 sympify 失败 | 不参与验证，计入报告 |

#### 4. 编码处理

| 功能 | 实现 | 状态 |
|---|---|---|
| 非 UTF-8 报错 | CLI 默认 utf-8，解码失败报错 | ✅ |
| `--encoding` 参数 | 支持显式指定编码（gbk/gb2312 等） | ✅ |
| 编码守卫 | `_ensure_utf8_stdio()` 确保 stdio 可打印中文 | ✅ |

#### 5. 关键指标（M2 实测）

| 指标 | 实测值 | 门槛 | 状态 |
|---|---|---|---|
| 步骤切分覆盖率 | 100%（63/63） | ≥95% | ✅ |
| 归一化成功率 | 98.41%（62/63） | ≥90% | ✅ |
| 误报率 | 0.00% | 0 优先 | ✅ |
| 定位准确率 | 100.00% | ≥90% | ✅ |
| 测试通过率 | 64/64 | 全绿 | ✅ |

### 文件变更

```
parser/__init__.py          步骤切分增强（圆圈编号/段落切分/异常检测）
parser/normalizer.py        归一化增强（中文前缀/LaTeX环境/分类）
cli.py                      --encoding 参数 + 编码报错
tests/test_parser/test_step_splitter.py  29 条测试（含边界用例）
tests/test_pipeline/test_audit.py        8 条测试（含编码测试）
data/rules/error_types.json  新增 constant_diff_boundary/variable_diff_boundary
```

## 二、下一棒待办（M3 知识与规则层）

### M3 目标
模块② 原文→条文块→机器可读阈值表；status 门控；零政策字面量门禁。

### 待办清单

- [ ] **阈值表构建**
  - [ ] 从原始政策文本提取阈值规则
  - [ ] 构建机器可读的阈值表（JSON/YAML）
  - [ ] 每条规则挂 status（verified/pending/unverified）

- [ ] **status 门控**
  - [ ] 只有 status=verified 的规则参与判定
  - [ ] pending 规则显式记录"待核对"
  - [ ] unverified 规则不进引擎

- [ ] **零政策字面量门禁**
  - [ ] 扫描引擎/基准/前端源码中的政策数值字面量
  - [ ] 豁免口径写死（仅允许 config.py 中的 TOLERANCE）
  - [ ] 门控测试：新增字面量必须触发

- [ ] **判定语义不虚高**
  - [ ] not_applicable 只给"原文写了例外情形"的项
  - [ ] 无适用项 → not_assessed（不输出 compliant）
  - [ ] 无条件义务缺失 = noncompliant

- [ ] **测试**
  - [ ] 阈值表格式验证
  - [ ] status 门控测试
  - [ ] 零字面量门禁测试
  - [ ] 判定语义不虚高测试

### M3 DoD
- [ ] 阈值表构建完成并验证
- [ ] status 门控测试通过
- [ ] 零政策字面量门禁测试通过
- [ ] 判定语义不虚高测试通过
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
| K12 | unsymbolizable 原因枚举：unparseable_latex/unknown_symbol/unsupported_construct/sympify_error | 修改需同步 parser/normalizer.py |
| K13 | 步骤切分分母=检出步骤数 | 修改需同步 parser/__init__.py |

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
11. **sympify 对纯中文单字很宽容**：`"这是纯文本"` 被解析为 Symbol，但含逗号 `"这是纯文本，"` 会失败。不可符号化检测依赖"含标点的中文"触发 sympify 失败
12. **圆圈数字①②③是 Unicode 字符**：不是 ASCII，正则需用 `re.escape(CIRCLE_NUMBERS)` 而非 `\d`

## 五、DoD 逐项 checklist

- [x] 步骤切分覆盖率 ≥ 95%（实测 100%，63/63）✅
- [x] 归一化成功率 ≥ 90%（实测 98.41%，62/63）✅
- [x] unsymbolizable 语义锁进测试（29 条 parser 测试）✅
- [x] 非 UTF-8 编码报错测试通过（5 条编码测试）✅
- [x] 测试全绿（64/64）✅
- [x] 基准运行全过（21/21）✅
- [x] 误报率 0.00% ✅
- [x] 定位准确率 100.00% ✅

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
hws-audit audit --input data/samples/gbk.txt --encoding gbk
hws-audit selftest

# 编码守卫
PYTHONUTF8=1 pytest tests/ -v

# 生成器
python -m hws_math_auditor.benchmark.generator

# parser 专项测试
pytest tests/test_parser/ -v --tb=short

# pipeline 专项测试（含编码）
pytest tests/test_pipeline/ -v --tb=short
```

## 七、M3 启动提示词

```
/goal 读取 "<项目绝对路径>\plan\HANDOFF-M3.md" 继续完成任务
```

## 八、已知风险

1. **sympify 对纯中文单字的宽容性**：`"这是纯文本"` 被解析为 Symbol（中文字符作为合法标识符），不会被标记为 unsymbolizable。这可能导致"纯中文描述"被误认为"可符号化"。当前策略：含标点的中文会触发 sympify 失败，纯中文单字视为可符号化（实际场景中纯中文单字极少）。
2. **LaTeX 环境提取不完整**：当前支持 align/equation/gather/matrix/pmatrix/bmatrix/cases，但不支持 alignat/array/aligned 等。若遇到不支持的环境，会标记为 unsymbolizable（unsupported_construct）。
3. **步骤数异常检测的阈值**：<2 或 >20 触发段落切分。阈值是经验值，若实际场景中步骤数分布不同，需调整 `MIN_STEPS_WARNING` 和 `MAX_STEPS_WARNING`。
