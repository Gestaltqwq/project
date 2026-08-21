# CLUENER2020 → Alpaca(100条) → Qwen2.5-1.5B LoRA 基础微调报告

## 1. 任务流程
1. **数据获取**：CLUENER2020（中文细粒度命名实体识别，10 类实体：地址/书名/公司/游戏/政府/电影/姓名/组织机构/职位/场景），原始数据下载至 `cluener_raw/`（train 10748 条 / test 1343 条）。
2. **Alpaca 格式转换**：`convert_cluener_alpaca.py` 从 train 集随机抽取 **100 条**（seed=42），生成 `LlamaFactory/data/cluener_alpaca_100.json`（instruction/input/output 三列），并注册到 `dataset_info.json`（键 `cluener_alpaca_100`）。
   - 指令：请从文本中识别所有命名实体并按类别列出，格式 "类别：实体1、实体2；类别2：实体3"
   - 10 类实体全部覆盖（公司 18 / 游戏 20 / 姓名 25 / 组织机构 21 / 地址 15 / 职位 13 / 政府 12 / 书名 11 / 电影 7 / 场景 7）
3. **基础训练**：Qwen2.5-1.5B-Instruct（本地 ModelScope 缓存，未下载新模型），LoRA 微调：
   - `manual_train.py`：LoRA r=8 / α=16 / lr=1e-4 / cosine+warmup / **20 epochs**（120 步）/ 有效 batch=16 / bf16 / cutoff 768 / eager attention
   - 训练损失：**0.638 → 0.082**（`training_loss.png`）
   - 产物：`LlamaFactory/saves/Qwen2.5-1.5B-Instruct/lora/cluener_100_20260821/`（adapter_model.safetensors 36MB + tokenizer + 训练日志）

## 2. 效果截图
- `screenshot_answers.png` —— 完整效果报告截图（`report_answers.html`，Edge 无头渲染）
- 展示 **7 个测试样本**（来自 CLUENER test 集，未参与训练）：用户提问 → 基础模型回答 → LoRA 微调后回答 → 标注答案
- 明显改进示例：
  - 示例3：基础模型漏掉「文汇路」，微调后正确识别 地址：文汇路
  - 示例4：基础模型漏掉「瓦拉多利德」，微调后正确识别
  - 示例6：基础模型将 Dota 误判为姓名，微调后正确识别 游戏：Dota
  - 示例5：游戏+公司双实体完全正确（微调前后均正确，微调后输出更规范）
  - 示例7：政府实体（美国证券交易委员会(SEC)）正确识别
- 局限（如实说明）：少量样本仍存在误标/漏标（如把普通名词当实体、个别长难句漏实体），属 100 条小样本基础训练的典型水平。

## 3. 推理与评估
- `infer_cluener.py`：对 test 集 16 条做抽取（`infer_results_base.json` 基础模型 / `infer_results_lora.json` 微调后）
- 微调后模型学会了「类别：实体」的结构化输出格式，多条样本找回微调前漏掉的实体。

## 4. 环境与踩坑记录（重要）
- 训练环境：`D:\code\2026\7_8月实训\8_20\venv_llama_clean`（torch 2.5.1+cu121 / transformers 5.8.0 / llamafactory 0.9.6.dev0），GPU RTX 4060 Laptop 8GB。
- **llamafactory CLI 直接训练在本机不稳定**：transformers 5.8.0 的 import 结构扫描线程偶发原生崩溃（Windows fatal exception: access violation，WER 记录 faulting module=python312.dll）；最终使用其底层同款 transformers Trainer 手动训练循环（`manual_train.py`）完成，产物为标准 PEFT LoRA 适配器，与 llamafactory 完全兼容（可用 llamafactory-cli chat / webui 加载）。
- **SDPA/flash 注意力反向内核在本机卡死**（GPU 驱动 nvlddmkm 153 事件），需用 `attn_implementation="eager"`。
- 本机 C 盘曾仅剩 5.5GB，已清理 pip 缓存+临时文件释放约 10GB；训练缓存建议指向 D 盘。
- `train_cluener_lora.yaml`：llamafactory 官方格式的训练配置（flash_attn: disabled / do_train: true / preprocessing_num_workers: 1），供 LlamaBoard/CLI 在稳定环境下使用。

## 5. 文件清单（本目录）
| 文件 | 说明 |
|---|---|
| `cluener_raw/` | CLUENER2020 原始数据（train/test） |
| `convert_cluener_alpaca.py` | CLUENER → Alpaca 转换脚本（100 条） |
| `LlamaFactory/data/cluener_alpaca_100.json` | Alpaca 格式数据集（已注册 dataset_info.json） |
| `manual_train.py` | 训练脚本（20 epochs，可复现） |
| `train_cluener_lora.yaml` | llamafactory 训练配置 |
| `LlamaFactory/saves/.../cluener_100_20260821/` | LoRA 适配器 + 训练日志 |
| `infer_cluener.py` | 推理脚本（基础/微调对比） |
| `infer_results_base.json` / `infer_results_lora.json` | 16 条测试样本推理结果 |
| `training_loss.png` | 训练损失曲线 |
| `report_answers.html` | 效果报告（可浏览器打开） |
| `screenshot_answers.png` | 报告截图（7 示例） |
