# 基于 Easy Dataset 的 ShareGPT 微调数据集（成都 Java 岗位招聘信息）

> 任务 2（CLUENER → Alpaca → LLaMA-Factory 基础训练）见 `cluener_task/README_cluener.md`，效果截图 `cluener_task/screenshot_answers.png`。

## 1. 任务说明
- 使用 **Easy Dataset**（本地桌面应用，v1.7.3，`D:\easydataset\Easy Dataset\Easy Dataset.exe`）从专业领域语料生成 **ShareGPT 格式**指令微调数据集。
- 语料为**非通用型专业领域材料**：30 份「成都 Java 岗位招聘信息」文档（`corpus/jobs_1.md ~ jobs_30.md`）。
- 生成的问题/答案全部锚定语料内容（公司、岗位、薪资、区域、任职要求等），**只有基于该语料微调后模型才能正确回答**。
- 数据量：**1043 条 QA 对（>1000）**。

## 2. 流程（Easy Dataset 全链路）
| 步骤 | 说明 | 结果 |
|---|---|---|
| 1. 文献导入 | 上传 30 份 .md 招聘文档（约 18KB/份） | UploadFiles = 30 |
| 2. 智能文献处理 | 章节感知递归分块（min 2500 / max 4000 字符） | Chunks = 120 |
| 3. 问题批量生成 | DeepSeek `deepseek-v4-flash`，按字符密度出题（约 240 字符/题） | 963 题（109/120 chunk 成功） |
| 4. 问题补生成 | 重试 11 个失败 chunk（8 个成功） | +80 题 → 1043 题 |
| 5. 答案智能构建 | 每个问题基于所属 chunk 内容生成答案（`answer-generation` 任务，并发 5） | 1043 条 QA 对（Datasets） |
| 6. 去重清理 | 修复一次并发导致的重复生成（908 条重复），按问题保留最新答案 | 1043 条唯一 |
| 7. 导出 | 从 Datasets 表导出标准 ShareGPT 结构（JSON + JSONL） | 本目录 2 个文件 |

模型配置：DeepSeek API（`deepseek-v4-flash`，temperature 0.4，maxTokens 8192），本地服务 `http://127.0.0.1:1717`。

## 3. 输出文件
- `sharegpt_easydataset_1043_pairs_20260821_010441.json`  —— ShareGPT 标准格式（数组）
- `sharegpt_easydataset_1043_pairs_20260821_010441.jsonl` —— 同内容 JSONL（每行一条）
- `corpus/` —— 原始语料（30 份招聘文档）
- `export_sharegpt.py` —— 导出脚本（可重新生成）
- `validate_sharegpt.py` —— 格式校验脚本
- `api_driver.py` —— Easy Dataset 本地 API 驱动（任务提交/轮询）

## 4. 格式示例
```json
[
  {
    "conversations": [
      { "from": "human", "value": "软通动力信息技术(集团)股份有限公司的Java/C/C++/Python/C#/Js/Ios岗位要求应聘者具备几年及以上嵌入式软件项目开发经验？" },
      { "from": "gpt", "value": "软通动力信息技术(集团)股份有限公司的Java/C/C++/Python/C#/Js/Ios岗位要求应聘者具备1年及以上嵌入式软件项目开发经验。" }
    ],
    "label": "其他"
  },
  ...
]
```

## 5. 质量说明
- 问题全部为语料内事实型问题（企业名称/岗位/薪资区间/工作区域/年限要求等），答案由模型基于对应 chunk 原文生成。
- 校验结果：1043 条，human→gpt 角色完整，无重复问题、无空答案、无格式错误。
- 可直接用于 LlamaFactory / LLaMA-Factory 等工具的 sharegpt 格式微调（`formatting: sharegpt`）。
