# plan/RELEASE-M8.md — v0.2.0 发布留档

> 仓库：`yuluo554/hard-math-solution-auditor`
> 里程碑：M8（规则集复核元数据 + 报告头版本 + CHANGELOG）
> 留档日期：2026-10-19

本文件在 **tag 之前**写好并进 tag 树；发布后产生的事实若与 tag 时点不同，另列「tag 后追加事实」。

---

## 一、tag 时点事实

| 项 | 值 |
|---|---|
| 版本 | `v0.2.0` |
| 发布形态 | 源码仓库 + CLI/GUI 双 exe + 源码包 + `sha256sums.txt` + `demo.gif` |
| 变更范围 | 报告头版本字段、规则集 `meta.review` 元数据、守门测试、文档；**不动验证/定位/重算算法** |
| 测试 | 185 passed（v0.1.1 为 176，新增 9 条 `tests/test_rules/test_clause_review.py`） |
| 构建 | `py -3.12 -m PyInstaller tools/pyinstaller-{cli,gui}.spec --clean`（本仓文档既定的构建命令） |

---

## 二、变更清单

| # | 项 | 说明 |
|---|---|---|
| 1 | **报告头版本** | Markdown / JSON / HTML 与 CLI 文本四处同源打印「工具版本」与「依据（阈值表）版本」；**刻意不带生成时间**（同输入同输出、两次运行逐字节一致） |
| 2 | **规则集复核元数据** | `data/rules/thresholds.json` 与 `data/rules/error_types.json` 写入 `meta.review`（复核日 / 周期 / 下次到期 / 复核人 / `standards[]` 含 `currency` 与 `authority_url`）；`status != verified` 的两条规则（THR-005/THR-006）逐条补 `not_used_by` |
| 3 | **守门测试** | `tests/test_rules/test_clause_review.py` 9 个用例；进 CI（`python -m pytest tests/ -q`） |
| 4 | **版本对齐** | 包内 `__version__` 由 `0.1.0` → `0.2.0`（此前与发布版本 `0.1.1` 不一致，报告头一旦打印工具版本就会自相矛盾） |
| 5 | **文档** | 新增 `CHANGELOG.md`；README「判定依据」表增加本次/下次复核列；`DEVELOPMENT.md` 补 M8 行与版本号 |

---

## 三、发布物与校验和（tag 时点写入）

| 附件 | 大小 | sha256 |
|---|---|---|
| `hws-audit-cli-win64.exe` | 31,131,090 B | `481a28d874fe5f7d88bc1084264bc50fb17e4317e76e6a7a85888b75fdb92881` |
| `hws-audit-gui-win64.exe` | 65,978,878 B | `6ed09636cd40395b6f2bd6a770a72c0ed1d6ed02bfce4ef53600d02c19b3f86a` |

> 本轮构建由 `py -3.12 -m PyInstaller` 完成（本仓文档既定的构建命令）；
> exe 含构建期 PE 时间戳，同机两次构建哈希即不同，承诺的是「同一棵树 → 同一产物语义」。

---

## 四、已知边界（未变）

- 符号化覆盖有限，`unsymbolizable` 如实登记，不判 ok；
- 模型开关默认关；数值结论永远来自确定性规则；
- 公开题库回归集为扩展项，首期不交付；
- PyInstaller 产物不承诺跨机字节一致（台账记本次上传件哈希）；
- 报告不带生成时间 —— 这是刻意的可复现性取舍，已在 README 写明。

---

## 五、tag 后追加事实

**Release 附件**（`gh release view v0.2.0 --json assets` 回读）与真下载复核记录见本文件发布后的追加提交。

| 附件 | 大小 | sha256 |
|---|---|---|
| `hws-audit-cli-win64.exe` | 见实测表 | 见实测表 |
| `hws-audit-gui-win64.exe` | 见实测表 | 见实测表 |
| `hws-audit-source-v0.2.0.zip` | 见实测表 | 见实测表 |
| `demo.gif` | 见实测表 | 见实测表 |

> 实际哈希以 `dist/sha256sums.txt` 与 Release 附件回读为准。