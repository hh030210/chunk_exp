# QASPER 配置（进行中）

- 原始输入：`/home/humq/chunk_code/data/external/qasper/v0.3/test_release_extracted_v1/qasper-test-v0.3.json`
- SHA-256：`6e29ad410e6e39aa1936017fb965b30a20eb2e7751997f55b97c9d281aa884e5`
- split：官方 test 全部 416 篇论文、1451 个问题
- 规范化：只使用 full_text；保留 section_name 与 paragraphs 的原始字符串，以两个换行符按原始顺序连接；空标题省略；paragraph 索引从零开始。
- B0 tokenizer：`Qwen/Qwen3.5-9B` revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a` 的 tokenizer.json；分别运行 256、512、1024 tokens，overlap=0；确定性切分，seed 不适用。
- 处理代码：`src/qasper_prepare.py` 和 `src/fixed_chunks.py`；MoC 英文回退修复与失败文档恢复脚本见 Git commits `48cc4cf`、`638b664`。
- B0 三种长度均已完成。B1–B4 均已完成并通过全文跨度核验，块数记录见下。
- B1：标题/段落、句子及 token 递归切分，目标 512；输出 4636 块，全文跨度核验通过。
- B2：Qwen3-Embedding-0.6B revision `97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3`，阈值 `0.37613460421562195`，由 QASPER validation 的 57943 个相邻句对 25% 分位确定；5634 块，全文跨度核验通过。
- B3：Qwen3.5-9B revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`；使用每句前最多 512 token 上下文计算负对数似然，局部最小值阈值 0，合并目标 512，长度上限 1024；4412 块，全文跨度核验通过。
- B4：同一 Qwen3.5-9B revision；提示词固定为“Summarize the main topics and key information of the following document in at most 256 tokens.”，长文档每 4096 tokens 分层摘要，最多生成 256 tokens；句子与摘要的余弦相似度文内平均值为动态阈值；4545 块，全文跨度核验通过。
- B5：使用作者 MoC router 与四个 experts（权重 revision 见 `moc_weights.sha256`）。作者 Qwen2.5-7B 抽取器仅在 experts 的 JSON 无效或模式无法映射源文本时恢复分段；抽取器以 4-bit 加载，恢复片段按顺序映射到源文本，边界来自原文。对齐方式/分数记入 `.alignment.jsonl`，无法恢复的文档写入 `.failures.jsonl`，不会静默略过。QASPER 全量 416 篇 B5 仍在服务器运行；截至 2026-11-10 15:14 的服务器快照，已同步 88 篇完整检查点共 3,943 块，逐篇通过全文连续覆盖、精确跨度、源文逐字匹配和源哈希核验，见 `QASPER/partial/`。论文 `1610.03807` 仍是 1 篇活动中的部分结果（18 块，覆盖未完成）；失败日志当前记录 9 篇论文：`1610.03955`、`1703.10152`、`1803.09000`、`1805.04833`、`1907.10676`、`1909.00437`、`1909.12079`、`1911.11899`、`2003.07459`。修复脚本 `src/repair_qasper_moc_failures.sh` 已排队，只重跑失败论文；`src/finalize_qasper_moc.py` 将在连续覆盖、源哈希和跨度核验通过后生成正式 `B5_MoC.jsonl`，原始失败日志保留为修复前审计。代码提交见 `48cc4cf`、`638b664`、`f0854a0`、`d115168`、`0aa0873`、`01cae91`、`1eacecd`。
