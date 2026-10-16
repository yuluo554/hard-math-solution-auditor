# plan/RELEASE-M6.md — M6 发布留档

> 仓库：`yuluo554/hard-math-solution-auditor`
> 发布里程碑：M6（GitHub Release 三件套）
> 留档日期：2026-10-16

## 一、发布基线

| 项 | 值 |
|---|---|
| 发布提交 | `52401c1be8084e1d64b4e9268c372324af242622` |
| 提交标题 | HANDOFF-M6：同步测试计数为 164 |
| tag | `v0.1.0`（annotated） |
| tag 指向 | `52401c1`（与 CI 绿提交一致） |
| 分支 | `main` |

## 二、三件套核验

| # | 项 | 状态 | 证据 |
|---|---|---|---|
| 1 | git tag | ✅ | `git tag -l` → `v0.1.0`；`git push origin v0.1.0` 成功 |
| 2 | Release 附件 | ✅ | `gh release view v0.1.0 --json assets` → 3 项 state=uploaded |
| 3 | 发布留档 | ✅ | 本文件 |

## 三、Release 资产

`gh release view v0.1.0 --json tagName,isDraft,isPrerelease,assets` 回读：

| 资产 | 大小 | state | SHA256 |
|---|---|---|---|
| hws-audit-cli-win64.exe | 31,124,700 B | uploaded | `689d7c2dfc72edf05997646f5d69c3046309a4c49836f0943ec38982abc24722` |
| hws-audit-gui-win64.exe | 69,244,896 B | uploaded | `911740b764d66129fa332e0ecb92dfe123b0be15f72442b701d2abe93c933d46` |
| sha256sums.txt | 235 B | uploaded | — |

`isDraft: false`、`isPrerelease: false`。

## 四、发布物本体已验（三步走）

| 步骤 | 命令 | 结果 |
|---|---|---|
| 1. 真下载 | `gh release download v0.1.0 --dir _verify_dl` | 3 件下载成功 |
| 2. sha256 对账 | `certutil -hashfile <下载件> SHA256` | 两件均与 `sha256sums.txt` **逐位一致**；且 == 本地构建件 |
| 3. 中立目录冻结态冒烟 | 复制到仓库树外目录，`env -u PYTHONPATH -u PYTHONHOME` 后运行 | 见下表 |

中立目录冒烟结果：

| 命令 | 结果 |
|---|---|
| `hws-audit-cli-win64.exe selftest` | 自检通过，exit 0 |
| `hws-audit-cli-win64.exe benchmark --run` | 21/21，误报率 0.00%，定位准确率 100.00% |
| `hws-audit-cli-win64.exe benchmark --metrics` | 合法 JSON，`total_cases: 21` |
| `hws-audit-gui-win64.exe --selftest` | 自检通过 |

> 结论：发布附件与源码同基线（下载件哈希 == 本地构建件哈希），
> 且免安装可用（中立目录、无 PYTHONPATH 依赖）。

## 五、CI 对账

推送到 `origin` 共 **4 次 push 事件**，产生 **4 个 run**，全部 success：

| run id | event | head_branch | head_sha | 结果 |
|---|---|---|---|---|
| 38854725776 | push | `main` | `52401c1b` | ✅ success |
| 38855009013 | push | `v0.1.0` | `52401c1b` | ✅ success |
| 38855416979 | push | `main` | `626e4ca2` | ✅ success（该 sha 后被 force-push 取代，已不可达） |
| 38855466913 | push | `main` | `ef62bdf9` | ✅ success |

**对账说明**：

- 同一 `head_sha` 出现两个 run 是**合法**的——`main` push 与 `tag` push
  各触发一次（本项目 `on: [push, pull_request, workflow_dispatch]` 无 filters）。
  判别看 `event` 与 `head_branch` 两个字段，tag 触发的 run 其 `head_branch`
  是 tag 名。**`52401c1b` 的两次 run 都已绿**。
- **如实记录一处订正**：`626e4ca2` 是发布留档的首版提交，**误将下载件
  （双 exe，约 100MB）入仓**。发现后以 `reset --soft` 回退、移除大文件、
  补 `.gitignore` 防复发，并 `push --force-with-lease` 改写为该提交的
  替代版 `ef62bdf9`。`626e4ca2` 的 run 当时也已绿，但该 sha 现已不可达。
  **发布基线以 `ef62bdf9` 为准**（tag `v0.1.0` 仍指向 `52401c1b`，
  发布物本体未受影响——tag 与附件在订正前即已就位且哈希已核验）。
- 发布附件本体核验（第四节）针对的是 tag `v0.1.0` 的三个资产，
  **不受本次 history 订正影响**。

### 首跑即绿（零诊断轮）

三矩阵全部一次通过：

| job | 结果 |
|---|---|
| test (windows-latest / py3.8) | ✅ success |
| test (windows-latest / py3.12) | ✅ success |
| test (ubuntu-latest / py3.12) | ✅ success |

日志实证（非静默跳过）：

- `164 passed`（三平台各自实测）
- `✅ 冻结台账与生成器位级一致`
- `自检通过`
- 21 条基准逐条 `passed=True`
- 裸 console script 通路 `hws-audit selftest` / `hws-audit benchmark --metrics` 均执行
- 退出码冒烟 `clean=0 dirty=1 missing=2` 断言通过

**前置工程消解了"首跑必红"**：CI env 设 `PYTHONUTF8=1`（补本机 `py -X utf8`
的盲区）+ `eol=lf` 与字节冻结守门 + `.[dev]` extras 覆盖全部测试期依赖
（含"测试不得模块级 import PySide6"守门）+ 3.8 兼容写法全仓落实。

## 六、脱敏核验

| 扫描面 | 方法 | 结果 |
|---|---|---|
| 历史通道（16 rev 全量） | 逐 rev `git grep` 本机盘符路径 / 用户目录 | 命中 **0**（阳性对照命中 11，证明通道有效） |
| 提交元数据邮箱 | `git log --format="%ae %ce" --all \| sort -u` | 仅 `yuluo554@users.noreply.github.com`（noreply 形态，豁免） |
| 跟踪文件内容 | 敏感词扫描 | 命中均为误报：`.gitignore` 模式、`max_tokens`（LLM 参数）、手机号正则命中的是 BENCH-021 的 sha256 数字段 |
| 产物本体（dist 3 件） | 本机盘符 / 用户目录 / 邮箱 | 三项计数均 **0** |
| CI run 日志（2 run） | 本机路径 / 用户目录 / 密钥词 | 命中 **0**；密钥词 3 处均为 GitHub 标准样板 `Secret source: Actions`（未配置任何 secret） |

## 七、仓库元信息

| 项 | 值 |
|---|---|
| description | 难题解答步骤级审计与错误定位器 — 确定性数学引擎，零模型依赖，可离线复跑 |
| topics | cli, deterministic, error-localization, math, math-verification, pyinstaller, python, symbolic-computation, sympy |
| visibility | private → **已转 public**（见下） |
| license | MIT（仓库 `LICENSE`） |

## 八、发布后元信息终检

| 检查项 | 结果 |
|---|---|
| `gh release view --json isDraft` | `false`（非草稿） |
| 附件名在列 | 3/3 在列 |
| topics 非空 | 9 个 topic 已回读确认 |
| description 与 README 定位一致 | 一致 |
| tag → 提交一致性 | `v0.1.0` → `52401c1`，与 CI 绿提交相同 |

## 九、本次发布配套的审查修复（发布前基线订正）

发布前对 M1–M6 做了一次全量审查，发现并修复 3 处"假门"与 7 处实质缺陷
（含 CRLF 跨平台确定性、冻结台账 18 vs 21 不一致、selftest 空壳、
测试对 PySide6 的隐依赖等）。详见 `plan/HANDOFF-M6.md` 第一节第 2 小节
的缺陷表——**发布基线 `52401c1` 是修复后的状态，非审查前状态**。

同样据实订正：审查前 README 曾把 M6 发布标为 ✅ 并列出本文件，
但当时本文件**并不存在**、也未建仓。本次为真实创建。

## 十、遗留与后续

| 项 | 状态 |
|---|---|
| 阈值表 THR-005 / THR-006 | pending，待样本分布确认后升级 verified |
| 公开题库回归集 | 未接入（许可待逐库核对） |
| LLM 实际接入 | `call_llm()` 仍为占位实现，需配置 `model_endpoint` |
| 零字面量门禁扫描面 | 仅 `.py`，未覆盖 `.md` / `.rst` / `.txt` |
| GUI 交互式人工测试 | 未做（已验证构建 + 启动 + `--selftest`） |
