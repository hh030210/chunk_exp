# CRUD-RAG 配置（进行中）

- 作者仓库 revision：`1aace383994e1f68efa12cf2a8e2dadfb4102ceb`。
- 评测数据：`data/CRUD_RAG/data/crud_split/split_merged.json`；SHA-256 `b199fb281ac526c1c8da7364cad7ea22b7f6fe1d4167e511edbdda8ad3bd943a`；`questanswer_1doc` 800 条，`questanswer_2docs` 797 条，不打乱。
- 文档语料：`data/CRUD_RAG/data/80000_docs`；按文件名排序，每行一条记录，移除行尾换行，其他字符保留，共 91964 行。来源未发现文档级原始 ID，派生 ID 为文件名和从零开始的行号；需复核作者实际文档粒度。
- 查询记录包含新闻文本而未发现源文档 ID；关联仅使用评测 news 字段正文在语料行内完整逐字匹配，并保留所有重复命中；1doc 有 8 条、2docs 有 697 条 query 至少关联一篇文档，未匹配部分仍需调查。匹配细节保存在 link_audit.jsonl。
- B0：Qwen3.5-9B tokenizer revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`；256/512/1024，无重叠。B1：段落、句子、token 递归切分，目标 512，上限 1024；确定性切分，seed 不适用。
- B2 排队使用 QASPER validation 文档校准的共享阈值，不使用 CRUD 评测 query 或答案；需在正式交付前确认跨数据集阈值是否可接受。
- B3 Meta-Chunking 与 B4 PIC 当前全量运行中，临时 JSONL 持续写入；B5 MoC 已配置在 QASPER B5 完成后接续启动。B5 使用作者 router/experts；对失效掩码输出或源文对齐错误启用作者 Qwen2.5-7B 抽取器（4-bit），并保留边界审计和失败清单。
- MoC 训练重叠审计：`Robot2050/Meta-chunker` revision `e3e2ded0c40bf626f4e1ce82b8459d4c46cfef60` 的 CRUD_MASK.jsonl 共 20000 条；以训练原文完整包含于语料记录为准，10723 条训练记录命中、涉及 10779 条语料记录。匹配明细 `moc_training_overlap.jsonl`，此为保守的精确匹配下限，不能排除改写或其他重叠。涉及 MoC 的 CRUD 结果标为探索性。
- 在当前可映射的 query 中，1doc 任务 8/800 有来源匹配，其中 0 条链接已确认重叠文档；2docs 任务 697/797 至少有来源匹配，其中 10 条链接已确认重叠文档。未匹配来源和文本改写不在这一下限内，不能解释为无重叠。
