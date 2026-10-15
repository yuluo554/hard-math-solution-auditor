# data/README.md — 依据查证与数据纪律

仓库 `HWS-hard-math-solution-auditor`（难题解答步骤级审计与错误定位器）。基准日：**2026-10-15**。

## 一、依据查证记录（三态）

| # | 依据 | 三态 | 渠道与说明 |
|---|---|---|---|
| 1 | openPangu-2.0-Flash 模型规格 | ✅已核对 | 官方模型卡（hf-mirror 镜像直连）：MoE，92B 总参数 / ~6B 每 token 激活，原生 512K（524,288）上下文，~34T tokens 训练；后训练 = SFT + 多专项 RL + OPD 在线蒸馏；Muon 优化器 |
| 2 | openPangu-2.0-Flash 架构细节 | ✅已核对 | 官方模型卡 + `bespokeontology/openPangu-2.0-Flash-CUDA-ROCm` README（GitHub API 直连）：MLA（q_lora_rank 1024 / kv_lora_rank 512，48 头 1 KV 头）+ DSA 稀疏全局层与 SWA 滑窗层 1:2 分层混合（DSA 取 top-2048）；4 流 mHC；3 层 MTP 自投机解码；128 attention sinks/层；词表 151,552；trunk 46 层。**压缩 MLA KV 满 512K 仅约 12GB** |
| 3 | openPangu-2.0-Flash 官方基准 | ✅已核对 | 官方模型卡（Thinking / Non-Thinking）：**AIME 2026 93.3 / 86.5（挂 Python 后 98.1）**；**HMMT Feb 2025 91.5 / 67.1（w/Python 96.9）**；IMO-AnswerBench 76.5 / 62.3（w/Python 80.8）；GPQA-Diamond 83.7 / 79.8；LiveCodeBench V6 85.1 / 50.9；SWE-bench Verified 63.1 / 57.6；TAU2-Bench 88.0 / 74.0；BBEH 62.5 / 51.5 |
| 4 | `<think>` 思维链可解析 | ✅已核对 | `mrexodia/llama.cpp-openPangu-2.0-Flash` README（GitHub API 直连）：fork 增加 "Chat support: tool calling and `<think>` reasoning parsing for the openPangu template" |
| 5 | **SymPy**（符号验证引擎，核心底座） | ✅已获取 | `https://api.github.com/repos/sympy/sympy` 直连 200；纯 Python、无外部服务依赖，可随 exe 内嵌 |
| 6 | **OEIS JSON API**（数列断言核验） | ✅已获取 | `https://oeis.org/search?q=1,1,2,3,5,8&fmt=json` HTTP 200，结构化 JSON 可解析；b-file `https://oeis.org/A000045/b000045.txt` HTTP 200，纯文本 "n value" 两列 |
| 7 | 公开题库（可选回归集） | ⬜待核对 | `yifanzhang-pro/BlueMO`(9★)、`dtunai/miniF2F-code`(3★)、`marcusm117/ProofNet-Verified`(1★)——**许可需逐库核对**；不可用则退回纯合成题 |
| 8 | openPangu 部署路径 | ✅/⬜ | `mrexodia/llama.cpp-openPangu-2.0-Flash`（GGUF，CPU/CUDA）✅；`bespokeontology/openPangu-2.0-Flash-CUDA-ROCm` ✅；omni-infer（昇腾，gitcode 仓库）⬜ 待核对 |
| 9 | 模型许可 | ⬜待核对 | OPENPANGU MODEL LICENSE AGREEMENT VERSION 2.0（模型卡所载）；入库时核对"不随仓分发权重"措辞，作为本工具"只连端点不带权重"设计的合规依据 |
| 10 | 开源空白论据（硬） | ✅已核对 | GitHub repo 检索（基准日 2026-10-15）：`llm math error localization` **0**；`math paper error detection` **0**；`aime benchmark harness` **0**；`llm self consistency math voting` **0**；`openpangu-2.0` **4**（2.0-Flash 相关仅两个推理引擎仓库，零应用层） |
| 11 | 开源空白论据（软，辅助） | ⬜软论据 | `math-evaluation-harness` 280★（纯评测 harness）、`math-prm-openai-2023` 9★、`symkit-mcp` 12★、`unitgate` 9★（量纲检查）、`Proofgrade` 0★；**均非"步骤级验证+错误定位+公开基准"闭环**。检索式与基准日如上，可回溯 |

## 二、数据源可获取性记录

| 源 | 可获取性 | 获取方式 | 用途 |
|---|---|---|---|
| SymPy | ✅ 已获取 | pip 包（离线内嵌） | 步骤级符号验证（核心引擎） |
| OEIS JSON / b-file | ✅ 已获取 | HTTP GET，无密钥无登录 | 数列类断言核验（扩展项） |
| openPangu-2.0-Flash 端点 | ✅ 可达（用户自备） | OpenAI 兼容端点 / llama.cpp server | 模型在环（显式开关，默认关） |
| 模型权重 | ⛔ 不分发 | — | **本工具不随包分发权重**（合规与体积双理由） |
| 公开题库 | ⬜ 待核对 | 逐库 license 核对后可选下载 | 可选回归集 |
| arXiv / 论文全文 | ⛔ 不适用 | — | 本题不涉及论文分发 |

## 三、合成数据纪律

本仓库**主力数据为合成数据**（自产生成器），非外部抓取。

1. **合成竞赛级题 + 解答生成器**：程序化生成题目（已知正确答案）与解题过程，并**植入已知错误步**。
2. **植入错误类型白名单**（真值台账登记的六类，覆盖度口径即按此列）：
   - `illegal_algebra`（非法代数变形）
   - `divide_by_zero`（除以零 / 除数为零未讨论）
   - `dimension_mismatch`（量纲不一致）
   - `induction_failure`（归纳法失效：基例/归纳步缺失或错误）
   - `boundary_omission`（边界条件漏判）
   - `symbol_typo`（符号错抄 / 变量混淆）
3. **真值台账**：每条样本登记 `input`（题+解答）与 `expect`（错误位置序号 + 错误类型 + 是否干净），**不存 `observed`**（观测运行时实算，防"比对冻结字典"的假门）。
4. **假数据白名单**（用于生成器中的占位/假标识，防与真实数据混淆）：
   - 假 DOI 前缀：`10.9999/`（保留段，不指向真实 DOI）
   - 假 arXiv 号段：`9999.99999` 及 `arXiv:9999.99999`
   - 假 ORCID：`0000-0000-0000-0000` 及 `0000-000X-XXXX-XXXX`
   - 假作者名：`A. Example` / `B. Sample` / `Test Author`
   - 假机构：`Example University` / `样例大学`
5. **预置模型输出快照**：快照含模型名、版本、生成参数（温度/采样/上下文）、原始输出、sha256；**随仓只存快照与真值台账**。快照仅用于离线复跑基准，不含任何个人隐私内容。
6. **只增不改**：`data/snapshots/**` 入仓后标 `.gitattributes` `-text` 防 EOL 改写字节；两期对比用不同文件。

## 四、编码纪律

解答文本与快照一律按 **UTF-8** 读写，**不做编码猜测**（贪心/试探式解码会把 GBK 字节静默解成乱码公式，产出"自洽但错"的审计结果——比报错危险得多）。非 UTF-8 一律报错并提示"请另存为 UTF-8"。
