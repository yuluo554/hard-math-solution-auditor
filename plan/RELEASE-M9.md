# plan/RELEASE-M9.md — v0.2.1 发布留档

> 仓库：`yuluo554/hard-math-solution-auditor`
> 里程碑：M9（退出码真实性 + 数据自证 + 自述一致性 + 判定依据可 review + CI 换新）
> 本轮性质：**二次迭代补丁版**（v0.2.0 → v0.2.1），由 `update/` 下四份诊断文件（D1–D13）驱动

本文件在 **tag 之前**写好并进 tag 树；发布后产生的事实若与 tag 时点不同，另列「tag 后追加事实」。

---

## 〇、决策记录

> 决策由用户在开工前拍板（DEC1–DEC5），执行方不得自行决定。本节是唯一决策台账。

| 编号 | 决策点 | 选定 | 理由 / 影响面 |
|---|---|---|---|
| **DEC1** | Python floor | **B：抬到 `>=3.12`** | 3.8 已 EOL（2024-10）；最近一次 CI 绿早于 GitHub 的 `ubuntu-latest → Ubuntu 26` 迁移（2026-10-19 起），迁移后零运行；抬到 3.12 后才能让「CI 绿证据」与「本机实测」同口径。连带放开 `PySide6` 上限与 `setuptools<81`，并可删手写 `STDLIB` 冻结名单。**免安装 exe 不受影响。** |
| **DEC1-附** | PySide6 上限 | **放开上限，用最新版** | `<6.7` 这个上限是专为 3.8 设的（6.7+ 要求 ≥3.9），floor 抬到 3.12 后不再必要。代价：GUI 代码未在 6.7+ 上验过 → 用 `--selftest` + 真实点击作为验收（见 §六 待人做的事）。 |
| **DEC2** | pip 渠道 | **A：`data/` 进 wheel** | 改动集中在打包配置与数据目录定位函数，`sys._MEIPASS` 冻结态分支不动。**无条件附做「缺数据 → 友好提示 + exit 2」**（来自 D10，与 DEC2 独立）。不选 B：exe 是唯一被实测证明可用的渠道，不值得为 pip 改它的数据布局。 |
| **DEC3** | `<pending>` 校验和 | **B：改成指引行** | 不篡改已发布的历史段；v0.2.1 新段按真实哈希写。选 A 需重打 v0.2.0，而本轮明令不动 v0.2.0。 |
| **DEC4** | 台账 21 还是 22 | **A：全改 21** | `plan/00` 与 `HANDOFF-M5/M6` 都已是 21，属文档漂移而非数据缺失。选 B 会牵动冻结链与覆盖度分母，成本/收益不成比例。 |
| **DEC5** | `--assertion` / `validate_judgment_semantics` | **A：只改 README 措辞** | 如实写「当前仅记录、不参与判定」；真实现属新功能，另开里程碑。 |

### 决策带来的连带项（已在本次执行中落地，逐条见 §二）

1. DEC1=B → `requires-python >=3.12`、classifier 去 3.8、CI 矩阵去 3.8 腿、README「3.8 与 3.12 都在 CI 矩阵里」改写、`DEVELOPMENT.md` §七 的两条 3.8 坑作废。
2. DEC1=B → `tests/test_gate/test_install_surface.py` 的手写 `STDLIB` 名单可改用 `sys.stdlib_module_names`（3.10+ API），删 60+ 行维护负担。
3. DEC2=A → `[tool.setuptools.package-data]` + `_resolve_data_dir()` / `load_threshold_table()` / `pipeline.selftest` 三处的**非冻结分支**改用装态可定位的路径；`tools/*.spec` 的 datas 与 `test_packaging_gate.WHITELIST` 等式**保持不动**（数据仍在仓根 `data/`，只是额外被打进 wheel）。
4. DEC3=B → `CHANGELOG.md` 的 `[0.2.0]` 段「校验和」改成一行指引；v0.2.1 新段写真实哈希。

---

## 一、tag 时点事实

| 项 | 值 |
|---|---|
| 版本 | `v0.2.1`（包版本 `0.2.1`） |
| 起点 | HEAD `a41d420c81d0f982b072837b1b690dc17b6fe484`；tag `v0.2.0` = `dd0f6c08737ee3d765438b30b93233e4808e4ef6`（annotated） |
| 起点测试基线 | **185 passed / 185 collected**（Python 3.12.10，`pip install -e ".[dev]"` 后） |
| 起点基准 | 21 条（3 clean + 18 dirty）；误报率 0.00%；定位准确率 100.00%；8 类 + clean 覆盖度全 met |
| 起点冻结台账 | `generator --check` → `✅ 冻结台账与生成器位级一致` exit 0 |
| 发布形态 | 源码仓库 + CLI/GUI 双 exe + 源码包 + `sha256sums.txt` + `demo.gif` |
| 变更范围 | 退出码判定、打包数据面、文档自述对齐、`.gitattributes`、CI runner/actions；**不动验证/定位/重算算法、不动 `config.tolerance` 的值（1e-9）、不动任何冻结台账与快照字节** |

---

## 二、变更清单

| # | 缺陷 | 项 | 说明 |
|---|---|---|---|
| 1 | D1 | **`benchmark` 退出码承认真实结果** | `cmd_benchmark` 由「只看台账一致 + 覆盖度」改为：逐条 `all(passed)` 为假 → 1；`false_positive_rate > 0` 或 `localization_accuracy < 1.0` → 1；`--metrics` 同一判定。现有 21 条仍全过（阳性对照）。 |
| 2 | D1 | **CLI 层子进程负控** | 新增「坏 verifier → CLI exit≠0」的子进程用例，堵住「探活只在 Python 层」的缺口。 |
| 3 | D2 | **`data/` 进 wheel**（DEC2=A） | `pyproject.toml` 加 `[tool.setuptools.package-data]`；三处数据定位的**非冻结分支**改为装态可解析。`sys._MEIPASS` 分支未动。 |
| 4 | D2/D10 | **缺数据 → 友好提示 + exit 2** | `audit` / `benchmark` / `selftest` 在数据目录不可用时打印可操作提示并返回 2，不再抛 traceback、不再压成 1。 |
| 5 | D3 | **CHANGELOG 校验和**（DEC3=B） | `[0.2.0]` 段 4 行 `<pending>` 改成一行指引（指向 Release 正文 / `sha256sums.txt`）；`grep -c "<pending>" CHANGELOG.md` → 0。 |
| 6 | D4 | **台账 21 一处口径**（DEC4=A） | README ×2、DEVELOPMENT ×1 改 21；CHANGELOG 0.1.0 段加更正注。 |
| 7 | D5 | **错误类型 8 类一处口径** | 统一为「8 类错误 + 1 类干净对照，共 9 行覆盖度」；改 README ×2、DEVELOPMENT、`data/README.md`（「六类」→ 8 条实列）。 |
| 8 | D12 | **README 三处不一致** | (a) 版本行收敛到当前最新（v0.2.1）并把 M6/M8 标为历史里程碑；(b) `test_readme_ci_claim_matches_reality` 从「字符串存在」收紧为「必须给出具体 job 名或 run id」；(c) `DEVELOPMENT.md` 的 `check_release.py` 说明改为「外部 skill 脚本，不在本仓」。 |
| 9 | D6/D7/D13 | **如实披露 + 清死代码** | README 把「阅卷复核（断言对账）」标为规划中、把 `validate_judgment_semantics()` 写成未接入；删除 pyflakes 报出的未用 import 与未用赋值。 |
| 10 | D8 | **判定依据可 diff** | `.gitattributes` 去掉全局 `*.json binary`，改为只对真二进制生效；`data/rules/*.json` 走 `-text`（与 `data/benchmarks/*` 同款）。新增两条对撞测试：阈值表 `THR-001/THR-002` 的值 == `config.tolerance`；`error_types.json` 的 8 个 `min_coverage` == `GeneratorConfig.min_coverage`。 |
| 11 | D9 | **CI 换新 + floor** | `actions/checkout@v7`、`actions/setup-python@v7`；CI 矩阵 3 腿 → 2 腿（windows 3.12 / ubuntu 3.12）；`requires-python >=3.12`。 |
| 12 | D11 | **`pathto=` 拼写错误的处置** | 按诊断结论**不做「顺手删除」**：本轮不动 spec 的 `pathto` 行，只在 DEVELOPMENT 记录它是已知死配置（删除需重跑构建 + 跑产物）。 |
| 13 | **D14（本轮新发现）** | **`audit --format json` 崩溃** | `cli.py` 直接读 `Verdict.step_no`，而该字段在 `Step` 上 → 任何 `--format json` 调用当场 `AttributeError`（exe 里是 PYI 未处理异常）。**实测 v0.2.0 的免安装 exe 上同样崩溃**（同一处代码），故不是本轮引入；诊断报告未列（它只跑了 text 格式）。修法 = 复用单一取数入口 `report.report_to_dict()`。 |

> 第 13 条是执行期**新发现**的既有缺陷，按纪律⑥以「更正 + 证据」形式记入本文件（`update/` 下 4 份诊断文件未改）。
> 证据：`_backups/pre-v021/dist/hws-audit-cli-win64.exe audit --input clean_solution.txt --format json` → exit 1 + `AttributeError: 'Verdict' object has no attribute 'step_no'`（保留在 §六 负控记录里）。

---

## 三、发布物与校验和

> 见 §五「tag 后追加事实」。附件哈希在 tag 与上传完成后回填。

---

## 四、已知边界（相对 v0.2.0 的变化）

- **Python 底线 3.8 → 3.12**：源码安装门槛抬高；免安装 exe 不受影响。
- **`--assertion` 仍不参与判定**，README 已如实标注（DEC5=A）。
- **`validate_judgment_semantics()` 仍未接入 pipeline**，README 已如实标注（不再暗示"只需传参即已接入"）。
- `thresholds.json` 的 `rules[].threshold` 仍只被格式校验消费，引擎侧读 `config.tolerance`；本轮用**对撞测试**把两者钉在一起（不改变运行期行为）。
- **pip 常规安装（非 editable）现在是受支持路径**：数据随 wheel 分发；`src/hws_math_auditor/_data/` 是构建产物，不入仓。
- **PySide6 上限 `<6.7` 已移除**（DEC1 的连带项）：本机在 **6.12.0** 上跑过 `--selftest` 与 `--bogus`；**窗口内交互仍未人工目检**（见 §七）。
- PyInstaller 产物不承诺跨机字节一致（台账记本次上传件哈希）。
- 报告不带生成时间 —— 刻意的可复现性取舍。

---

## 五、执行记录（本批做了什么 / 未做什么）

### 五之一 · 批次 0（决策）

用户拍板 **DEC1=B / DEC2=A / DEC3=B / DEC4=A / DEC5=A**，另加一条
「PySide6 放开上限、用最新版」。逐条写入 §〇。

### 五之二 · 批次 1（退出码真实性 + 数据自证）

**做了什么**

| 项 | 内容 | 证据 |
|---|---|---|
| 1.1 | `cmd_benchmark` 返回值改由真实结果决定；`--metrics` 同判 | 新增 `_benchmark_failed()`；见下负控 |
| 1.2 | CLI 层子进程负控（此前只有 Python 层探活） | `tests/test_gate/test_cli_exit_codes.py::TestBenchmarkExitCodeIsReal`（3 项，含"注入面自证"） |
| 1.3 | 数据缺失 → 友好提示 + exit 2 | 新增 `tests/…::TestDataUnavailableIsExit2`（4 个命令参数化 + 1 项阳性对照） |
| 1.4 | `data/` 进 wheel（DEC2=A） | 新增 `datadir.py` + `setup.py` 的 `build_py` 钩子 + `[tool.setuptools.package-data]` + `MANIFEST.in`；新增 `tests/…::TestWheelCarriesData`（4 项，含真构建） |
| 1.5 | 顺带修 `benchmark.runner` 的 `__main__` 入口 | 与 CLI 同一判定（该入口此前同样恒 exit 0） |

**负控（改前 / 改后，逐条实测）**

```
# D1 负控：副本里把 verifier.verify_step 注入为恒返回 Verdict("ok", ...)
改前：benchmark --run     → 18 条 passed=False，CLI_EXIT = 0   ← 缺陷
       benchmark --metrics → localization_accuracy 0.0，METRICS_EXIT = 0
改后：benchmark --run     → CLI_EXIT = 1（并打印 "❌ 基准未达标：18 条未通过 …"）
       benchmark --metrics → METRICS_EXIT = 1
阳性对照：未注入时 benchmark --run → 21 条全 passed，exit 0（截取末尾行）
       ✅ BENCH-021: expect=variable_diff_boundary, observed=step 2, passed=True
       ✅ 基准达标：21 条全部通过
```

```
# D2/D10 负控：藏掉数据目录（源码态 data/ 与装态 _data/ 都删）
audit --input dirty.txt            → exit 2，stdout 首行「❌ 随包数据不可用：…」，Traceback 计数 0
benchmark --run                    → exit 2，同上
benchmark --metrics                → exit 2
selftest                           → exit 2
```

```
# DEC2=A 正面证据（干净 venv + 中立目录，非 editable）
pip install hws_math_auditor-0.2.1-py3-none-any.whl
(cwd = %TEMP%\…\neutral2，***不是仓根***)
hws-audit selftest           → 自检通过           exit 0
hws-audit benchmark --run    → 21 条全 passed     exit 0
hws-audit benchmark --metrics→ 合法 JSON          exit 0
hws-audit audit --input d.txt→ 首错步骤 3         exit 1
hws-audit audit --input d.txt --format json →     exit 1
hws-audit audit --input clean.txt（不存在）→      exit 2
```

### 五之三 · 批次 2（自述一致性）

| 项 | 改前 | 改后 |
|---|---|---|
| 台账份数 | README ×2 / DEVELOPMENT ×1 / CHANGELOG ×2 写 22 | 全 21；文档面（README / DEVELOPMENT / CHANGELOG / data / docs）**0 命中**（`update/` 与本文档只因引用旧值而含该串） |
| 错误类型 | 「9 类」/「8 类」/「六类」三套 | 统一「8 类错误 + 1 类干净对照 = 9 行覆盖度」 |
| CHANGELOG `<pending>` | 4 行占位符（且进了 v0.2.0 源码包） | 改为指引行；`grep -c "<pending>" CHANGELOG.md` → **0** |
| README 版本表 | M6 行停在 v0.1.1，最新版未置顶 | 「**v0.2.1（当前最新）**」置顶，M6/M8 标为历史 |

新增守门（把「文档数字」钉在「盘上实物」上，此前没有任何一条测试做这件事）：

- `test_readme_gate.py::test_readme_ledger_count_matches_actual_files`
- `::test_no_doc_claims_wrong_ledger_count`
- `::test_no_doc_says_wrong_error_type_count`
- `::test_benchmark_output_prints_error_types_plus_clean`
- 收紧 `::test_readme_ci_claim_matches_reality`（字符串存在 → 必须给出具体 job/版本/run id）
- 新增 `::test_readme_release_status_shows_current_version`（版本必须与 `pyproject.toml` 一致）

**负控**（在副本里把 README 的份数改回旧值、DEVELOPMENT 的错误类型改回「9 类」）：

```
FAILED test_readme_ledger_count_matches_actual_files      ← 份数不符被抓
FAILED test_no_doc_claims_wrong_ledger_count             ← 台账编号区间写法被抓
FAILED test_no_doc_says_wrong_error_type_count           ← 「9 类错误」被抓
```

### 五之四 · 批次 3（判定依据可 review）

**改前**：`git check-attr binary diff -- data/rules/thresholds.json` →
`binary: set / diff: unset`；改表后 `git diff` 只输出 `Bin 8262 -> 8487 bytes`。

**改后**（实测，副本里改 `THR-001` 的 `1e-09` → `1e-07`）：

```
 data/rules/thresholds.json | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
@@ -11,7 +11,7 @@
       "description": "常数差异恰好 1e-9（边界命中，K8 阈值验证）",
-      "threshold": 1e-09,
+      "threshold": 1e-07,
```

**根因比诊断更深一层**：旧写法 `text=-text` **并没有冻结字节**——`git check-attr`
把它当"文本"处理（回显字面量 `-text`），于是旧测试"匹配到 `-text` 字符串"就绿了。
真实验证：往受保护路径写 CRLF 后提交，blob 里 CR 被抹掉。正确写法是裸 `-text`。
因此新测试**不再匹配字符串**，改为断言真语义 + 已提交 blob 字节 == 工作树字节：

- `test_byte_freeze.py::test_snapshot_and_ledger_marked_text_negated`（`text: unset`）
- `::test_frozen_files_blob_bytes_equal_worktree_bytes`（行为面）
- `::test_binary_macro_not_applied_to_json`（`diff` 不得 unset）
- 新增 `tests/test_gate/test_rules_code_coupling.py`（6 项，表 ↔ 代码对撞）

**负控**（副本里改 `THR-001.threshold=1e-07` + `error_types[0].min_coverage=99`）：

```
FAILED test_thresholds_match_config_tolerance
FAILED test_error_type_min_coverage_matches_generator_config
```

### 五之五 · 批次 4（CI + floor + 清死代码）

- `actions/checkout@v7`、`actions/setup-python@v7`；矩阵 3 → 2 腿。
- 新增两个 job 把本轮的两条修复变成**常驻证据**（不只留在一次性记录里）：
  - `installed-wheel`：真建 wheel → 断言 `_data` 条目 → 干净 venv 非 editable 装 →
    **中立目录**跑 `selftest` / `benchmark --run` / `audit dirty`。
  - `exit-code-truth`：注入坏 verifier → 断言 `--run` 与 `--metrics` 都 exit 1。
- 删 `tests/test_gate/test_install_surface.py` 的 60+ 行手写 `STDLIB` 冻结名单，
  改用 `sys.stdlib_module_names`（floor 已 ≥3.12）。
- D13 死代码：`pyflakes src/ tests/` 由 **43 条 → 0 条**。
  其中一条是真 bug（非纯清理）：`generator.py` 的 `check_frozen_ledger` 用了
  `Path` 但只在函数内 import 之前就调用（未定义名），本轮把 `Path` 提到模块级。
- 另修两处"空测/弱测"：`test_llm.py` 里构造了 `snapshot` 却从不使用、只断言
  `isinstance(...)` 的用例改为断言真实语义；`runner.py` 的 `__main__` 入口补判定。

### 五之六 · 测试面成绩

```
改前：185 passed / 185 collected
改后：213 passed / 213 collected        （3.12.10，pip install -e ".[dev]" 后）
sdist 内（干净 venv，无 .git）：208 passed / 5 skipped / 0 failed
      （5 个 skip 全部是"非 git 工作树"与"未装 build"两类，逐条理由见 -rs 输出；
       改前 sdist 内是 5 failed / 12 passed）
pyflakes src/ tests/ → 0 条
```

### 五之七 · 未做什么（如实交代）

- **未实现**「断言 vs 推导链对账」（D6）与 LLM 接入（`call_llm` 仍是占位）。
- **未改** `verify_step` / `locator` / `recalc` 的算法；未改 `config.tolerance` 的值（1e-9）。
- **未改**冻结台账与快照的任何 `input` / `expect` / `output`（DEC4=A 是纯文档改法）。
- **未降**任何阈值。
- **未动** `v0.1.0` / `v0.1.1` / `v0.2.0` 三个 tag 与 Release。
- **未删** spec 的 `pathto=` 死配置（D11 的结论是"别当已修顺手删"）。
- **未做 GUI 窗口内的人工目检**（`--selftest` 与 `--bogus` 已在 PySide6 6.12.0 上通过）。

---

## 六、负控与证据留档

> 本节保存"改前/改后"的原始命令与输出，便于独立复验时逐条对撞。

### 6.1 诊断复现（改前状态，在 HEAD `a41d420` 的副本上）

```
mut1 = %TEMP%\hmsa-exec\mut1（git archive HEAD 展开 + verifier 注入恒 ok）
$ mut1 内: python -m hws_math_auditor benchmark --run > run.log
BROKEN_RUN_RC=0                     ← 缺陷：18 条全错仍 exit 0
grep -c "passed=False" run.log → 18
误报率: 0.00% / 定位准确率: 0.00%
$ python -m hws_math_auditor benchmark --metrics → BROKEN_METRICS_RC=0
  "localization_accuracy": 0.0
```

### 6.2 改后同一负控

```
mut2（当前树 + 同一注入）
BROKEN_RUN_RC=1
BROKEN_METRICS_RC=1
❌ 基准未达标：18 条未通过 → BENCH-004, BENCH-005, … BENCH-021
```

### 6.3 免安装 exe（本轮重建，中立目录）

```
dist/hws-audit-cli-win64.exe  = 20,337,722 B（sha256 见 §八）
  selftest                        → 自检通过                exit 0
  benchmark --run                 → 21 条全 passed          exit 0
  audit dirty                     → 首错步骤 3 / 反例 {'x': -3}  exit 1
  audit --format json (clean)     → 合法 JSON               exit 0
  audit --format json (dirty)     → "first_error": 3        exit 1
dist/hws-audit-gui-win64.exe    = 58,051,115 B
  --selftest                      → 自检通过                exit 0
  --bogus                         → 未知参数               exit 2
```

> 注：exe 体积较 v0.2.0（31,131,090 B）明显变化，**主要来自 PySide6 6.12 与
> PyInstaller 6.22 的依赖面变化**；两个 exe 都在中立目录实跑通过（见上）。
> 按仓库既定口径，PyInstaller 产物**不承诺**跨机/跨版本字节一致。

### 6.4 新发现缺陷的原始证据（见 §二 第 13 条）

```
$ _backups/pre-v021/dist/hws-audit-cli-win64.exe audit --input clean_solution.txt --format json
V020_JSON_RC=1
  File "hws_math_auditor\cli.py", line 76, in cmd_audit
AttributeError: 'Verdict' object has no attribute 'step_no'
[PYI-19176:ERROR] Failed to execute script '__main__' due to unhandled exception!
```

---

## 七、需要人做的事

1. **GUI 实机目检**：本轮把 PySide6 上限放到最新（本机装到 **6.12.0**，`--selftest` /
   `--bogus` 通过），但**窗口内「审计 / 设置 / 导出报告」三个页签的真实点击未人工过目**。
   验收命令：`python -m pip install "PySide6"` → `python -m hws_math_auditor.gui`。
2. **发布形态确认**：v0.2.0 的附件是**手工上传**形态（CI 里没有 publish 步骤）。
   本轮沿用手工上传；若要改成 CI 发布，属于新工作项。
3. **v0.2.0 的 JSON 崩溃**：本轮在 v0.2.1 修掉了，但 **v0.2.0 的 Release 附件照旧会崩**。
   若不打算重发 v0.2.0（本轮明令不动），建议在 Release 说明里加一句"请使用 v0.2.1"。
   —— **需用户拍板**（默认不动）。

---

## 八、tag 后追加事实

> 本节内容产生于 tag 之后，与 §一「tag 时点事实」分开记录（沿用 M7/M8 的做法）。

（待填）
