# Visual-Memvid: 视觉原生 RAG

> 基于 DeepSeek OCR + Memvid 的革命性文档检索系统

## 🎯 核心创新

传统 RAG 的问题：
- ❌ 依赖文本分块策略（表格被切断、公式被破坏）
- ❌ Embedding 计算和存储成本高
- ❌ 丢失原始布局信息

**Visual-Memvid 的方案**：
- ✅ PDF → 图片帧（保留完整布局）
- ✅ 轻量级元数据索引（无需 Embedding）
- ✅ DeepSeek OCR 实时理解（视觉原生）
- ✅ 自动查看前后页（类人阅读行为）

## 🏗️ 架构对比

### 传统 RAG
```
PDF → 文本提取 → 分块 → Embedding → 向量检索 → Rerank
```

### Visual-Memvid
```
PDF → 图片帧 → 轻量级索引 → 元数据定位 → DeepSeek OCR 理解
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动 DeepSeek OCR 服务

确保 DeepSeek OCR 服务运行在 `http://localhost:8200`

### 3. 构建知识库

```python
from visual_memvid import VisualMemvidEncoder

encoder = VisualMemvidEncoder()
encoder.add_pdf("your_document.pdf")
encoder.build_video("knowledge.mp4")
```

### 4. 检索和问答

```python
from visual_memvid import VisualMemvidRetriever

retriever = VisualMemvidRetriever("knowledge.mp4", "index.json")
results = retriever.search("第二季度的销售额是多少？", context_window=1)

for result in results:
    print(f"📄 第 {result['page_num']} 页 ({result['page_type']}):")
    print(result['content'])
```

## 📦 项目结构

```
visual-memvid/
├── visual_memvid/
│   ├── __init__.py
│   ├── pdf_encoder.py          # PDF → 图片帧
│   ├── lightweight_index.py    # 轻量级元数据索引
│   ├── ocr_client.py           # DeepSeek OCR 客户端
│   ├── visual_retriever.py     # 视觉检索器（含前后页）
│   └── hybrid_strategy.py      # 混合检索策略
├── examples/
│   └── demo.py                 # 端到端示例
├── tests/
│   └── test_visual_rag.py      # 测试
└── requirements.txt
```

## 🎨 特性

### 1. 类人阅读行为

自动查看前后页，模拟人类翻书习惯：

```python
# 查询定位到第 15 页
# 自动查看：第 14 页（前）、第 15 页（核心）、第 16 页（后）
results = retriever.search("销售额", context_window=1)
```

### 2. 混合检索策略

- 简单查询 → 关键词匹配（快速）
- 复杂查询 → 大模型推理（准确）

```python
# 简单查询：关键词匹配（~5ms）
retriever.search("第二季度")

# 复杂查询：大模型推理（~500ms）
retriever.search("对比 Q1 和 Q2 的增长率")
```

### 3. 批量 OCR 优化

利用 DeepSeek OCR 批量接口，性能提升 2-3x：

```python
# 串行：3 页 × 2.7s = 8.1s
# 批量：3 页 ≈ 3-4s
```

## 📊 性能对比

| 维度 | 传统 RAG | Visual-Memvid |
|------|---------|---------------|
| 存储成本 | 8.6MB | 3MB (2.9x) |
| 索引构建 | 慢（Embedding） | 快（关键词提取） |
| 检索延迟 | ~50ms | ~5ms (元数据) + 2.7s (OCR) |
| 表格处理 | ❌ 被切断 | ✅ 完整保留 |
| 布局保留 | ❌ 丢失 | ✅ 完整保留 |

## 🔧 配置

```python
# config.py
CONFIG = {
    "pdf": {
        "dpi": 150,  # 渲染分辨率
    },
    "video": {
        "codec": "h265",  # 编解码器
        "fps": 30,
    },
    "ocr": {
        "endpoint": "http://localhost:8200",
        "batch_size": 5,
    },
    "retrieval": {
        "context_window": 1,  # 前后页窗口
        "top_k": 3,
    }
}
```

## 📝 License

MIT License

## 🙏 致谢

- [Memvid](https://github.com/Olow304/memvid) - 视频编码核心
- [DeepSeek OCR](https://github.com/deepseek-ai/DeepSeek-OCR) - OCR 引擎

