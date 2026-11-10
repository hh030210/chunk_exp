# 切片基线实验

本仓库保存首轮切片代码、数据版本记录和对比实验结果。实验定义见 [首轮必跑基线与实验参数](docs/首轮必跑基线与实验参数.md)。

实验在服务器 `humq@splabbiggpu`（`211.87.224.135:17622`）运行，服务器目录为 `/home/humq/chunk-baseline-experiments`。完整原始语料和运行中间文件留在服务器；每组实验完成后校验并同步其结果归档到本仓库。

## 当前状态（2026-11-10）

| 数据集 | 基线 | 状态 | 记录 |
|---|---|---|---|
| QASPER | B0–B4 | 已完成并完成基础跨度校验 | 完成结果见 `results/qasper_b2_completed.tar.gz` 与 `results/qasper_b3_b4_completed.tar.gz`；B0/B1 与过程记录在服务器 |
| QASPER | B5 MoC | 全量运行中 | 服务器快照已同步 88 篇完整检查点共 3,943 块；另有 1 篇仍为活动中的部分结果、9 篇待修复失败记录。已同步检查点均通过源文哈希、跨度和连续覆盖核验；见 `QASPER/partial/`，烟雾检查见 `QASPER/smoke/` |
| CRUD-RAG | B0–B2 | 已完成 | `results/crud_b2_completed.tar.gz` 与 `results/crud_handoff_partial.tar.gz` |
| CRUD-RAG | B3–B4 | 运行中 | B3 PPL 与 B4 PIC 正在服务器生成临时 JSONL |
| CRUD-RAG | B5 MoC | 排队待启动 | 等 QASPER 全量 MoC 后启动 |
| NQ | B0–B2、B4 | 运行中 | 全量语料约 590 万篇；临时输出持续增长 |
| NQ | B3 Meta-Chunking | GPU 队列中 | 等 GPU2 或 GPU3 任一张卡释放后启动 |
| NQ | B5 MoC | 排队待启动 | 等 CRUD-RAG MoC 完成后启动 |

GitHub 远端：`https://github.com/hh030210/chunk_exp`。当前仓库为公开仓库；实验完成后应逐数据集生成归档、验证行数/跨度/失败记录，再提交并同步到该远端。

## 目录

- `src/`：数据处理、切片与启动脚本
- `docs/`：实验方案
- `NQ/`、`CRUD-RAG/`、`QASPER/`：查询清单、语料映射及交付结果
- `results/`：校验后的结果归档、版本/哈希记录和运行报告

切片结果需保留 `source_doc_id`、规范化文本 Unicode 字符跨度、源文本哈希及结构来源索引。原始 query/gold 不得混入 chunk；不生成检索、QA 或评测指标。
