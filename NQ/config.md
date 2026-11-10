# NQ 配置（进行中）

- 语料：KILT `kilt_knowledgesource.json` 固定快照，原始来源 `https://dl.fbaipublicfiles.com/KILT/kilt_knowledgesource.json`，SHA-256 `f966d6f09c4ff91656db5c56c384f136b0c495c7083c043586b8cb1033c389a5`，共 5,903,530 条记录；使用原始 `wikipedia_id`，`text` 各元素按原有顺序以两个换行符连接，其他字符保留。
- 查询：官方 `NQ-open.dev.jsonl`，仓库 revision `fb26a3073b1fe636c97302890a27b491d6530130`，SHA-256 `f15567f38099f3615f5b8a685c0aef449c11ad90d3da3735e8d1b98115b40616`，3610 条，能回查官方 example_id 时用该 ID，否则按文件行号从零开始派生 query ID，不打乱。
- 官方标注：`hjn1/natural_questions` revision `8a1c7b9720cfe1bb8dc603ae13d07c75ff47ebd5` 的 default validation parquet。使用原始问题和原始短答案集合精确匹配 NQ-open 文件，3503 条唯一匹配，107 条未匹配；原始 annotation ID、parquet 文件及行号保存在 raw_locator。
- 对匹配记录，以 annotation 中 URL 的 oldid 调用 MediaWiki revision API 查询稳定 page ID；映射文件 `data/NQ/revision_to_pageid.json` SHA-256 `c6a73210373ab2f2ae9e94ea0b20225e99874f67092251ce62226d783b62c078`。再校验 page ID 存在固定语料内；3476 条 query 成功关联，其余填空数组，不推测。
- B0 三种块长与 B1 正在全量运行，B2/B4 已启动；B3 Meta-Chunking 的 GPU 队列会在 GPU2 或 GPU3 任一张卡先释放后启动。B5 MoC 接续于 CRUD-RAG B5 且 NQ B2 完成后启动，使用作者 router/experts 与经源文验证的 Qwen2.5-7B 4-bit 抽取器回退。B0 块长 256/512/1024、无重叠；B1 目标 512、上限 1024；B2 使用 QASPER validation 固定阈值 0.37613460421562195，不使用 NQ 测试 query 或答案。
