# Visual-Native RAG 技术说明书

**版本**: v1.0 MVP  
**日期**: 2025-11-02  
**作者**: AI Agent + User

---

## 1. 系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                          前端层 (待开发)                         │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ 文档上传     │  │ 处理进度     │  │ 问答界面     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ↓ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────────┐
│                          API 层 (FastAPI)                        │
│                                                                  │
│  POST /api/upload          - 上传 PDF                           │
│  GET  /api/status/{job_id} - 查询处理状态                       │
│  POST /api/query           - 提交问题                           │
│  GET  /api/documents       - 文档列表                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        业务逻辑层                                │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ DocumentManager (文档管理)                                │  │
│  │  - 文档注册                                               │  │
│  │  - 状态跟踪                                               │  │
│  │  - 多文档索引                                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ ProcessingPipeline (处理流水线)                           │  │
│  │  - PDF 编码                                               │  │
│  │  - Summary 生成                                           │  │
│  │  - 缓存管理                                               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ QueryEngine (查询引擎)                                    │  │
│  │  - 三层检索                                               │  │
│  │  - 结果排序                                               │  │
│  │  - 上下文构建                                             │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        核心组件层                                │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ PDFEncoder   │  │ OCRClient    │  │ Retriever    │          │
│  │ (Memvid)     │  │ (DeepSeek)   │  │ (3-Layer)    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ OCRCache     │  │ EmbedModel   │  │ LLMClient    │          │
│  │ (本地缓存)   │  │ (可选)       │  │ (可选)       │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                          存储层                                  │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ 视频文件     │  │ 索引文件     │  │ Summary      │          │
│  │ (.mp4)       │  │ (.json)      │  │ (.json)      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │ OCR 缓存     │  │ Embedding    │                            │
│  │ (.json)      │  │ (.npy)       │                            │
│  └──────────────┘  └──────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 核心模块详解

### 2.1 PDF Encoder (`pdf_encoder.py`)

#### 功能
将 PDF 转换为视频格式，保留完整视觉信息。

#### 技术实现
```python
class PDFEncoder:
    def __init__(self, dpi=150, codec='libx265'):
        self.dpi = dpi
        self.codec = codec
    
    def encode(self, pdf_path, output_video, output_index):
        # 1. PDF → 图片帧
        frames = self._pdf_to_frames(pdf_path)
        
        # 2. 图片帧 → 视频
        self._frames_to_video(frames, output_video)
        
        # 3. 生成索引
        index = self._create_index(frames)
        self._save_index(index, output_index)
```

#### 关键参数
- **DPI**: 150（平衡质量与文件大小）
- **编码器**: H.265/HEVC（高压缩比）
- **帧率**: 1 FPS（静态图片）
- **压缩比**: ~50x

#### 性能
- **速度**: ~1.3 秒/页
- **输出**: 62 页 PDF (15 MB) → 视频 (300 KB)

---

### 2.2 OCR Client (`ocr_client.py`)

#### 功能
调用 DeepSeek OCR API 进行文本提取。

#### 技术实现
```python
class OCRClient:
    def __init__(self, api_url="http://43.139.167.250:8200"):
        self.api_url = api_url
    
    def ocr_image(self, image_path, prompt="<image>\n请提取文本"):
        # 1. 图片 → Base64
        image_base64 = self._encode_image(image_path)
        
        # 2. 构建请求
        payload = {
            "model": "deepseek-vl",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
        }
        
        # 3. 调用 API
        response = requests.post(f"{self.api_url}/v1/chat/completions", json=payload)
        
        # 4. 解析结果
        return response.json()['choices'][0]['message']['content']
```

#### Prompt 设计

**Compressed Summary Prompt**（推荐）:
```
<image>
请用极度简洁的方式提取核心信息：
- 保留所有数字、百分比、金额
- 实体名称用缩写
- 只保留关键词，去除连接词
- 用逗号分隔
```

**Full OCR Prompt**:
```
<image>
请详细提取这页的所有内容，包括：
- 标题和章节
- 正文内容
- 表格数据
- 图表说明
```

#### 性能
- **Summary 生成**: ~48 秒/页
- **Full OCR**: ~30 秒/页
- **压缩比**: ~1.5x（Summary）

---

### 2.3 Enhanced Encoder (`enhanced_encoder.py`)

#### 功能
集成 PDF 编码 + Summary 生成的完整流水线。

#### 技术实现
```python
class EnhancedEncoder:
    def __init__(self):
        self.pdf_encoder = PDFEncoder()
        self.ocr_client = OCRClient()
        self.ocr_cache = OCRCache()
    
    def process_document(self, pdf_path, doc_id, doc_name):
        # Phase 1: PDF → 视频
        video_path = f"output/{doc_id}.mp4"
        index_path = f"output/{doc_id}_index.json"
        self.pdf_encoder.encode(pdf_path, video_path, index_path)
        
        # Phase 2: 生成 Summary
        summaries = self._generate_summaries(doc_id, doc_name, pdf_path)
        
        # Phase 3: 保存结果
        self._save_summaries(summaries, f"output/summaries.json")
        
        return {
            "video": video_path,
            "index": index_path,
            "summaries": summaries
        }
    
    def _generate_summaries(self, doc_id, doc_name, pdf_path):
        summaries = []
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            # 1. 渲染页面
            page = doc[page_num]
            pix = page.get_pixmap(dpi=150)
            img_path = f"temp_page_{page_num}.png"
            pix.save(img_path)
            
            # 2. 检查缓存
            cache_key = f"{doc_id}_{page_num}_summary"
            cached = self.ocr_cache.get(cache_key)
            
            if cached:
                text = cached
            else:
                # 3. 调用 OCR
                text = self.ocr_client.ocr_image(
                    img_path,
                    prompt=COMPRESSED_SUMMARY_PROMPT
                )
                # 4. 缓存结果
                self.ocr_cache.set(cache_key, text)
            
            # 5. 提取关键词
            keywords = self._extract_keywords(text)
            
            summaries.append({
                "page": page_num + 1,
                "text": text,
                "keywords": keywords
            })
        
        return summaries
```

---

### 2.4 Visual Retriever (`visual_retriever.py`)

#### 功能
三层检索架构，渐进式深度理解。

#### 技术实现
```python
class VisualRetriever:
    def __init__(self, summaries_path, ocr_client, ocr_cache):
        self.summaries = self._load_summaries(summaries_path)
        self.ocr_client = ocr_client
        self.ocr_cache = ocr_cache
    
    def retrieve(self, query, top_k=10, use_full_ocr=False):
        # Layer 1: Summary 检索
        relevant_pages = self._search_summaries(query, top_k)
        
        if not use_full_ocr:
            # 简单查询：直接返回 Summary
            return self._format_results(relevant_pages, mode="summary")
        
        # Layer 2: Full OCR
        full_context = self._get_full_ocr(relevant_pages)
        
        return self._format_results(full_context, mode="full")
    
    def _search_summaries(self, query, top_k):
        """关键词匹配检索"""
        query_keywords = set(jieba.cut(query))
        
        scores = []
        for summary in self.summaries:
            # 计算关键词重叠度
            summary_keywords = set(summary['keywords'])
            overlap = len(query_keywords & summary_keywords)
            
            # 计算文本相似度（简单版本）
            text_match = sum(1 for kw in query_keywords if kw in summary['text'])
            
            score = overlap * 2 + text_match
            scores.append((summary['page'], score, summary))
        
        # 排序并返回 Top-K
        scores.sort(key=lambda x: x[1], reverse=True)
        return [s[2] for s in scores[:top_k]]
    
    def _get_full_ocr(self, summaries):
        """获取完整 OCR 文本"""
        results = []
        
        for summary in summaries:
            page = summary['page']
            cache_key = f"{self.doc_id}_{page}_full"
            
            # 检查缓存
            cached = self.ocr_cache.get(cache_key)
            
            if cached:
                text = cached
            else:
                # 调用 Full OCR
                img_path = self._get_page_image(page)
                text = self.ocr_client.ocr_image(
                    img_path,
                    prompt=FULL_OCR_PROMPT
                )
                self.ocr_cache.set(cache_key, text)
            
            results.append({
                "page": page,
                "text": text
            })
        
        return results
```

#### 检索策略

**Layer 1: 关键词匹配**
- **算法**: TF-IDF 或简单关键词重叠
- **速度**: 0.1 秒
- **适用**: 简单查询（主题、概述）

**Layer 2: Full OCR**
- **触发**: 关键词匹配分数低，或用户明确要求
- **速度**: 2-5 秒（取决于页数）
- **适用**: 数据查询、跨页关联

**Layer 3: 精确提取**（可选）
- **触发**: 需要结构化输出（表格、列表）
- **方法**: 定制 Prompt
- **速度**: 1-2 秒/页

---

### 2.5 OCR Cache (`ocr_cache.py`)

#### 功能
缓存 OCR 结果，避免重复调用。

#### 技术实现
```python
class OCRCache:
    def __init__(self, cache_dir="ocr_cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_cache_key(self, doc_id, page, prompt):
        """生成缓存 Key"""
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
        return f"{doc_id}_{page}_{prompt_hash}"
    
    def get(self, cache_key):
        """获取缓存"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data['text']
        
        return None
    
    def set(self, cache_key, text):
        """设置缓存"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump({
                "text": text,
                "timestamp": time.time()
            }, f, ensure_ascii=False, indent=2)
```

#### 缓存策略
- **Key**: `{doc_id}_{page}_{prompt_hash}`
- **存储**: 本地 JSON 文件
- **过期**: 无过期（文档不变）
- **清理**: 手动清理或定期清理

#### 性能提升
- **首次查询**: 30 秒（Full OCR）
- **缓存命中**: 0.1 秒
- **提升**: **300x**

---

## 3. 数据流

### 3.1 文档处理流程

```
用户上传 PDF
    ↓
┌─────────────────────────────────────────┐
│ Step 1: PDF 编码                         │
│  - PDF → 图片帧 (150 DPI)               │
│  - 图片帧 → 视频 (H.265)                │
│  - 生成索引 (JSON)                       │
│  - 耗时: ~78 秒 (62 页)                 │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Step 2: Summary 生成                     │
│  - 遍历每一页                            │
│  - 调用 DeepSeek OCR (Compressed)       │
│  - 提取关键词                            │
│  - 缓存结果                              │
│  - 耗时: ~50 分钟 (62 页)               │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Step 3: 索引构建 (可选)                  │
│  - 生成 Embeddings                      │
│  - 构建倒排索引                          │
│  - 耗时: ~5 分钟                        │
└─────────────────────────────────────────┘
    ↓
文档就绪，可以查询
```

### 3.2 查询处理流程

```
用户提问
    ↓
┌─────────────────────────────────────────┐
│ Step 1: 查询分析                         │
│  - 提取关键词                            │
│  - 判断查询复杂度                        │
│  - 耗时: < 0.01 秒                      │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Step 2: Summary 检索 (Layer 1)          │
│  - 关键词匹配                            │
│  - 返回 Top-K 页面                      │
│  - 耗时: ~0.1 秒                        │
└─────────────────────────────────────────┘
    ↓
    判断是否需要 Full OCR
    ↓                    ↓
  简单查询            复杂查询
    ↓                    ↓
返回 Summary      ┌─────────────────────────────────────────┐
                  │ Step 3: Full OCR (Layer 2)              │
                  │  - 加载相关页面                          │
                  │  - 调用 DeepSeek OCR (Full)             │
                  │  - 检查缓存                              │
                  │  - 耗时: ~2-5 秒                        │
                  └─────────────────────────────────────────┘
                      ↓
                  返回完整上下文
```

---

## 4. 配置说明

### 4.1 系统配置 (`config.py`)

```python
CONFIG = {
    "ocr": {
        "api_url": "http://43.139.167.250:8200",
        "model": "deepseek-vl",
        "timeout": 60,
    },
    "summary": {
        "prompt": """<image>
请用极度简洁的方式提取核心信息：
- 保留所有数字、百分比、金额
- 实体名称用缩写
- 只保留关键词，去除连接词
- 用逗号分隔
""",
        "enabled": True,
    },
    "video": {
        "dpi": 150,
        "codec": "libx265",
        "fps": 1,
    },
    "cache": {
        "enabled": True,
        "dir": "ocr_cache",
    },
}
```

---

## 5. 部署说明

### 5.1 环境要求
- **Python**: 3.10+
- **GPU**: RTX 5060 Ti (16GB) 或更高
- **内存**: 32GB+
- **存储**: 500GB+ SSD

### 5.2 依赖安装
```bash
pip install -r requirements.txt
```

### 5.3 DeepSeek OCR 部署
参考 `DeepSeek-OCR-API-调用规则.md`

---

## 6. 性能优化建议

### 6.1 Summary 生成加速
- **批量处理**: 一次处理多页（GPU 并行）
- **异步任务**: 使用 Celery 异步生成
- **分布式**: 多 GPU 并行处理

### 6.2 检索优化
- **Embedding 检索**: 集成本地 Embedding 模型
- **倒排索引**: 构建关键词倒排索引
- **缓存预热**: 预先生成常见查询的 Full OCR

### 6.3 存储优化
- **视频压缩**: 使用 AV1 编码器（更高压缩比）
- **缓存清理**: 定期清理低频缓存
- **分布式存储**: 使用对象存储（S3/OSS）

---

## 7. 监控与日志

### 7.1 关键指标
- **处理速度**: 页/秒
- **查询延迟**: P50, P95, P99
- **缓存命中率**: %
- **GPU 利用率**: %

### 7.2 日志格式
```json
{
  "timestamp": "2025-11-02T10:30:00Z",
  "level": "INFO",
  "module": "enhanced_encoder",
  "action": "generate_summary",
  "doc_id": "knowledge",
  "page": 19,
  "duration": 48.5,
  "cache_hit": false
}
```

---

## 8. 故障排查

### 8.1 常见问题

**问题 1: Summary 为空**
- **原因**: Prompt 格式问题（多行、编号）
- **解决**: 使用单行简洁 Prompt

**问题 2: OCR 超时**
- **原因**: 图片过大或网络问题
- **解决**: 降低 DPI 或增加 timeout

**问题 3: 视频编码失败**
- **原因**: FFmpeg 未安装或编码器不支持
- **解决**: 安装 FFmpeg，使用 libx264

---

## 9. 未来扩展

### 9.1 多文档管理
- **分布式架构**: 每个文档独立处理
- **智能路由**: Router Agent 选择相关文档
- **联合检索**: 跨文档关联查询

### 9.2 高级功能
- **表格提取**: 结构化表格数据
- **图表理解**: 图表数据提取
- **多模态融合**: 文本 + 图像 + 表格

### 9.3 性能提升
- **Vision Token API**: 如果 DeepSeek 开放 API
- **本地 LLM**: 集成本地 LLM（Llama 3）
- **GPU 集群**: 多 GPU 并行处理

