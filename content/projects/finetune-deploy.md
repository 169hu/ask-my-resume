---
title: 大模型微调与部署
path: finetune-deploy
order: 5
tech: [Python, PyTorch, PEFT/QLoRA, Transformers, Streamlit]
tag: 主打
online_demo: true
demo_url: https://464a9d28.r10.cpolar.top
metrics:
  - label: BLEU-4
    value: 0.824
    hint: 12 条留出集均值
  - label: 短句 BLEU-4
    value: 1.000
    hint: 8 条与训练分布接近
  - label: 长句 BLEU-4
    value: 0.472
    hint: 4 条需泛化（级义同）
  - label: 压显存
    value: QLoRA 4-bit
    hint: 低资源微调
highlight:
  - QLoRA 4-bit 微调 Qwen2-1.5B，留出集 BLEU-4 = 0.824
  - Bad Case 分析指出 BLEU 对同义改写误罚的局限
github: https://github.com/169hu/qwen-finetune
---
## 一句话
Qwen2-1.5B 中英翻译微调项目，基于 **QLoRA(4-bit) + LoRA** 做指令微调，完整走通"数据生成 → 训练 → BLEU 评估 → Bad Case 分析"链路。

## 背景
只做 RAG 调 API 不够，要证明自己"能把模型真正训出来并评估上线"。本项目选小模型 Qwen2-1.5B 做中译英微调，既控制成本又覆盖完整训练闭环。

## 难点
1. 显存有限，直接全参微调跑不动，如何在训出效果的同时压住资源？
2. 评估指标 BLEU 是否客观？翻译"换一种说法但意思对"时会不会被误罚？
3. 训出的模型如何量化验证真实泛化能力，而非在大训练集上自欺？

## 方案
- 用 **QLoRA(4-bit) 量化 + LoRA** 微调 `Qwen/Qwen2-1.5B-Instruct`，PEFT/QLoRA 把可训练参数压到极小、显著降显存。
- 用 DeepSeek API 生成 80 条真实中英翻译数据（`gen_data.py`），改进版在 80 条上 `--max-steps 300 --lr 5e-5` 训练。
- `main.py` 统一入口：`train`（标准/改进/冒烟）/ `eval`（BLEU-4）/ `plot`（loss 曲线)；`streamlit run app.py` 一行起演示。
- 评估在 **12 条留出集**（训练数据之外）上做，验证真实泛化。

## 结果与亮点
- 留出集平均 **BLEU-4 = 0.824**：短句（与训练分布接近）8 条 **1.000**、需泛化长句 4 条 **0.472**（达意但同义差异）。
- **Bad Case 分析**发现：长句 BLEU 偏低是"语义正确、用词不同"的同义改写（set off/set out、meet/catch up with），并非翻译错误——从而提出引入 chrF / COMET 或多样参考译文来消除误罚。
- 训练 loss 从 10.27 降至 8.10（冒烟 30 步，3200 完整训练由 `plot` 生成正式曲线）。

## 踩过的坑
- BLEU 只看字面 n-gram 重合，会误罚同义改写长句：补充 Bad Case 人工分析，结论改用更鲁棒语义指标评估。
- 全参微调会爆显存：改用 QLoRA 4-bit 低资源微调，效果与资源取得平衡。