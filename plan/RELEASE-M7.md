# plan/RELEASE-M7.md — v0.1.1 发布留档

> 仓库：`yuluo554/hard-math-solution-auditor`
> 里程碑：M7（回访修复 + 补丁版本发布）
> 留档日期：2026-10-18

本文件在 **tag 之前**写好并进 tag 树；发布后才产生的事实列在 §五「tag 后追加事实」。

---

## 一、tag 时点事实

| 项 | 值 |
|---|---|
| 版本 | `v0.1.1` |
| 发布形态 | 源码仓库 + CLI/GUI 双 exe + 源码包 + `sha256sums.txt` + `demo.gif` |
| 变更范围 | 报告导出实现、首错编号口径、文档与测试；**不动验证/定位/重算算法** |
| 测试 | 176 passed（v0.1.0 为 164，新增 12 条报告导出测试） |

---

## 二、修复清单（回访缺陷 → 处置）

| # | 缺陷（v0.1.0 实况） | 级别 | 处置 |
|---|---|---|---|
| D1 | **tag `v0.1.0` 打在"未推送、M6 未完成"的提交**：tag 树 README 写"待首推"、plan/00 M6 行 ⬜、无 RELEASE-M6 文件 | 写题级 | v0.1.1 状态全部回填后再打 tag；本文件在 tag 前落盘 |
| D2 | **报告导出只写在 plan/05**，代码里只有 `setHtml`，无 `--report` | 出题级（㉔） | 新增 `report.py`（单一渲染源）+ CLI `--report/--report-formats` + GUI 导出按钮 + 12 条测试 |
| D3 | **首错编号口径矛盾**：报告写"首错步骤 2"，解释写"首错在第 3 步"（0 基 vs 1 基） | 写题级（⑨） | 对外统一 1 基，内部保留 `first_error_index0`；测试锁死 |
| D4 | **覆盖率渲染成 `3/0`**（键名用 `total` 而非 `total_steps`） | 写题级 | 修键名 + 测试断言渲染出 `3/3` |
| D5 | **台账 3 行"待 M5 验证 / 待 M1"残留** | 写题级（㉒） | 已实现项翻 ✅；扩展项标"不进判定路径" |
| D6 | **§三 承诺的技术报告 / 演示 GIF 不存在** | 出题级（㉔） | `docs/技术报告.md`、`docs/demo/demo.gif` 落仓；Release 附件含 demo.gif |
| D7 | **缺招牌动词表** | 出题级（⑳） | plan/00 §三之二 补 9 行 |
| D8 | **plan/04 无逐形态验收** | 出题级（⑩/㉕） | plan/04 §二之二 补形态四格 + 报告导出验收 6 项 |

---

## 三、验证（tag 时点）

```bash
python -m pytest tests/ -q                     # 176 passed
hws-audit selftest                             # 自检通过
hws-audit benchmark --run                      # 21/21，误报率 0.00%，定位准确率 100.00%
hws-audit audit --input data/samples/dirty_solution.txt --report audit-report
# → audit-report.{md,json,html} 三份；exit 1（检出错误，既定语义）
dist/hws-audit-cli-win64.exe selftest          # 0
dist/hws-audit-gui-win64.exe --selftest        # 0
```

**产物哈希（本机 Windows 构建，tag 时点）**：

| 文件 | 大小 | sha256 |
|---|---|---|
| `hws-audit-cli-win64.exe` | 31,129,450 B | `530cefa6c1b549d4dc833982bbe89325504a0e01e89a81d166ffe972b29b5a6f` |
| `hws-audit-gui-win64.exe` | 65,977,549 B | `919100ce19f48388520bb6a2c2fa801a038fa1b7a01b246fea1eb111e2e8b523` |
| `hws-audit-source-v0.1.1.zip` | 见 §五（由 tag 树 `git archive` 生成） | 见 §五 |

> GUI 由 69.2MB 降到 66.0MB（排除未使用的 Qt 组件）。

---

## 四、已知边界（未变）

- 符号化覆盖有限，`unsymbolizable` 如实登记，不判 ok；
- 模型开关默认关；数值结论永远来自确定性规则；
- 公开题库回归集为扩展项，首期不交付；
- PyInstaller 产物不承诺跨机字节一致（台账记本次上传件哈希）。

---

## 五、tag 后追加事实

> 本节内容产生于 tag 之后，与 §一「tag 时点事实」分开记录（preflight ㉒）。

- CI run：待回填
- Release 附件清单与 digest：待回填
- 真下载复核（中立目录 selftest / audit / --report）：待回填
