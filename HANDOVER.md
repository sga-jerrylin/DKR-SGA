# 🔄 DKR 1.0 项目交接文档

**交接时间**: 2025-11-08 20:30  
**项目**: DKR 1.0 (Deep Knowledge Retrieval) - Agent-First 文档检索系统  
**工作区**: `e:\memvid-deepseekocr`

---

## 🚨 紧急问题：FFmpeg 编码失败

### 问题描述

用户上传 PDF 文档时，视频编码失败，错误信息：

```
[libx265 @ 0000018157b45380] Error setting preset/tune slower/stillimage.
[libx265 @ 0000018157b45380] Possible tunes: psnr ssim grain zerolatency fastdecode animation
```

### 根本原因

**`stillimage` 不是 FFmpeg `-tune` 参数支持的值！**

- ❌ **错误用法**: `-tune stillimage`（FFmpeg 的 `-tune` 参数不支持）
- ✅ **正确用法**: `-x265-params tune=stillimage`（x265 编码器内部参数）

### 需要修复的文件

#### 1. `visual_memvid/pdf_encoder.py` (第 302-311 行)

**当前错误代码**:
```python
if ffmpeg_codec == 'libx265':
    tune = codec_config.get("tune", "stillimage")
    extra_params = codec_config.get("extra_params", "keyint=1:no-scenecut:strong-intra-smoothing")
    
    x265_params = f"{extra_params}:threads={thread_count}"
    cmd.extend(['-tune', tune])  # ❌ 错误：FFmpeg 不支持 -tune stillimage
    cmd.extend(['-x265-params', x265_params])
```

**修复方案**:
```python
if ffmpeg_codec == 'libx265':
    tune = codec_config.get("tune", "stillimage")
    extra_params = codec_config.get("extra_params", "keyint=1:no-scenecut:strong-intra-smoothing")
    
    # ✅ 正确：将 tune 合并到 x265-params 中
    x265_params = f"tune={tune}:{extra_params}:threads={thread_count}"
    cmd.extend(['-x265-params', x265_params])
    # 不要使用 -tune 参数！
```

#### 2. `visual_memvid/config.py` (第 20 行)

**当前配置**:
```python
"tune": "stillimage",  # 这个配置本身没问题，但使用方式错误
```

**说明**: 配置文件不需要修改，只需要修改 `pdf_encoder.py` 中的使用方式。

### 修复步骤

1. 打开 `visual_memvid/pdf_encoder.py`
2. 找到第 302-311 行的 H.265 编码参数设置
3. 将 `tune` 参数从 `-tune` 移到 `-x265-params` 中
4. 删除 `cmd.extend(['-tune', tune])` 这一行
5. 修改 `x265_params` 为 `f"tune={tune}:{extra_params}:threads={thread_count}"`
6. 同样修复第 312-315 行的 H.264 部分（如果需要）
7. 重启后端服务
8. 测试上传 PDF 文档

---

## 📚 项目背景

### 项目概述

**DKR 1.0** 是一个 Agent-First 的文档检索系统，核心特点：

1. **视觉记忆**: 将 PDF 转换为高清视频存储（参考 Memvid 项目）
2. **两阶段检索**: 
   - Stage 1: 搜索 Summary 快速定位相关页面
   - Stage 2: 如果 Summary 不足，进行全页 OCR
3. **AI Agent 驱动**: 使用 LangGraph 构建智能检索 Agent

### 4 层检索架构

- **Layer 0**: Library Overview (~500 tokens) - 文档库概览
- **Layer 1**: Category Documents (~3000 tokens) - 分类文档列表
- **Layer 2**: Document Pages with Summary (~6000 tokens) - 页面 Summary
- **Layer 3**: Full OCR (~5000 tokens) - 完整页面 OCR

### 技术栈

**后端**:
- FastAPI, LangGraph, LangChain, Pydantic, Uvicorn
- Python 3.13 on Windows (PowerShell)

**前端**:
- Vue 3, TypeScript, Element Plus, Pinia, Vite
- 运行在 `http://localhost:3001`

**视频处理**:
- OpenCV, PyMuPDF, FFmpeg
- H.265 (HEVC) 编码

**AI 模型**:
- **DeepSeek Chat**: `https://api.deepseek.com` (model: `deepseek-chat`)
- **DeepSeek OCR**: `http://111.230.37.43:5010` (3B model)
- **Gemini 2.5 Flash Lite**: Via OpenRouter `google/gemini-2.5-flash-lite-preview-09-2025`
- **OpenRouter API Key**: `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`

---

## 📂 文件结构

```
backend/data/
├── documents/              # PDF 原文件
├── videos/                 # MP4 视频
├── summaries/              # Summary JSON
├── indexes/                # 索引文件
├── library_index.json      # 文档库总索引
├── temp/                   # 临时文件
└── cache/                  # OCR 缓存
```

---

## 🔧 当前配置（视频编码）

### `visual_memvid/config.py`

```python
"pdf": {
    "dpi": 200,  # 渲染分辨率（200 DPI 平衡清晰度和文件大小）
    "color_space": "RGB",
},

"video": {
    "codec": "h265",
    "fps": 30,
    "crf": 23,  # 质量参数（23 是高质量和文件大小的最佳平衡点）
    "preset": "slower",
    "file_type": "mkv",
    "tune": "stillimage",  # x265 内部参数
    "extra_params": "keyint=1:no-scenecut:strong-intra-smoothing",
},

"ocr": {
    "base_size": 4096,
    "image_size": 2048,
}
```

### 配置演进历史

| 阶段 | DPI | CRF | 分辨率 | 问题 |
|------|-----|-----|--------|------|
| 初始 | 150 | 28 | 1920×1080（强制缩放） | 视频模糊 |
| 极限 | 600 | 15 | 4960×7016（原始） | 文件太大 |
| **当前** | **200** | **23** | **3307×4677（原始）** | **平衡** |

**关键决策**:
- 200 DPI 对于 OCR 识别足够清晰（10pt+ 文字）
- CRF 23 是业界标准的高质量设置
- 移除了强制缩放，保持原始分辨率
- 预期文件大小：原 PDF 的 1/3 到 1/5

---

## 📝 最近工作历史

### Phase 1: PDF 处理优化
- 移除了冗余的表格检测逻辑（`page.find_tables()` 太慢）
- 原因：Summary 已包含表格/公式/图像信息，无需重复检测

### Phase 2: OCR Summary 质量改进
- 从 DeepSeek OCR 3B 切换到 Gemini 2.5 Flash Lite（prompt following 更好）
- 实现了 "Rich Summary JSON" 格式，包含完整的数据提取
- 添加了 `chart_info` 和 `image_info` 字段
- 移除了字数和数据项数量限制，确保数据完整性

### Phase 3: 文件结构重组
- 统一了数据目录结构到 `backend/data/`
- 清理了旧文件、测试脚本和重复目录
- 删除了所有 `__pycache__` 目录（Python 缓存导致旧代码运行）

### Phase 4: CORS 和响应验证修复
- 添加 `http://localhost:3001` 到 CORS 配置
- 修复 `list_documents()` 方法，添加 `category` 字段

### Phase 5: 视频质量优化
- **问题发现**: 视频被强制缩放到 1920×1080，损失 90% 像素
- **修复**: 移除强制缩放，保持原始分辨率
- **平衡配置**: 从 600 DPI 降到 200 DPI，从 CRF 15 提升到 23
- **参考 Memvid**: 学习了 H.265 静态图像优化参数

### Phase 6: QR 码策略讨论
- 分析了 Memvid 的 QR 码压缩策略
- **结论**: QR 码适合纯文本，但 DKR 1.0 需要保留视觉信息
- **建议**: 优化当前的两阶段检索策略，而不是采用 QR 码

---

## ✅ 待办事项

### 🔴 紧急（必须完成）

1. **修复 FFmpeg 编码错误**
   - 文件: `visual_memvid/pdf_encoder.py` (第 302-311 行)
   - 任务: 将 `tune` 参数从 `-tune` 移到 `-x265-params` 中
   - 预计时间: 5 分钟

2. **测试视频生成**
   - 重启后端服务
   - 上传一个测试 PDF
   - 验证视频文件生成成功
   - 检查视频清晰度和文件大小

### 🟡 重要（建议完成）

3. **实现两阶段检索优化**
   - 强化 Summary 的作用，包含足够详细的信息
   - 实现智能判断：Summary 是否足够回答问题
   - 只在必要时调用全页 OCR
   - 预期效果：简单查询 <100ms，复杂查询 600-2100ms

4. **Summary 缓存优化**
   - 将 Summary 加载到内存或 Redis
   - 检索时直接从缓存读取，避免解码视频
   - 预期效果：检索速度提升 10-20 倍

### 🟢 可选（未来优化）

5. **考虑混合策略**
   - 存储两份数据：高分辨率图像 + 文本 QR 码
   - 简单查询使用 QR 码（<100ms）
   - 复杂查询使用 OCR（600-2100ms）
   - 权衡：文件大小增加 20-30%

6. **批量 OCR 优化**
   - 多个相关页面并行 OCR
   - 总耗时 = max(单页时间) 而不是 sum(单页时间)

---

## 🔍 关键代码位置

### 视频编码
- **配置**: `visual_memvid/config.py` (第 6-22 行)
- **编码器**: `visual_memvid/pdf_encoder.py` (第 200-385 行)
- **增强编码器**: `visual_memvid/enhanced_encoder.py` (第 119-226 行)

### 文档处理
- **上传 API**: `backend/app/api/documents.py` (第 75-85 行)
- **处理器**: `backend/app/core/document_processor.py`
- **库管理**: `backend/app/core/library_manager.py`

### 检索系统
- **Agent**: `backend/app/agent/dkr_agent.py`
- **检索器**: `backend/app/core/retriever.py`
- **视觉检索**: `visual_memvid/visual_retriever.py`
- **轻量级索引**: `visual_memvid/lightweight_index.py`

### Summary 生成
- **Prompt**: `prompts/summary_prompt.py`
- **客户端**: `visual_memvid/summary_client.py`

---

## 🚀 启动命令

### 后端
```powershell
cd e:\memvid-deepseekocr
python main.py
```

### 前端
```powershell
cd frontend
npm run dev
```

访问: `http://localhost:3001`

---

## 📞 参考资料

### Memvid 项目
- GitHub: https://github.com/Olow304/memvid
- 核心概念: QR 码 + H.265 压缩 + 向量检索
- 压缩比: 1/20 到 1/50

### FFmpeg H.265 参数
- **Presets**: ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow, placebo
- **FFmpeg -tune**: psnr, ssim, grain, zerolatency, fastdecode, animation
- **x265 tune**: stillimage, psnr, ssim, grain, zerolatency, fastdecode, animation
- **关键**: `stillimage` 只能通过 `-x265-params tune=stillimage` 使用

### 项目文档
- README: `README.md`
- 配置: `visual_memvid/config.py`
- 后端配置: `backend/app/config.py`

---

## 💡 重要提示

1. **Python 缓存**: 如果修改代码后没有生效，删除所有 `__pycache__` 目录
2. **CORS 配置**: 前端运行在 3001 端口，确保 CORS 配置包含此端口
3. **视频分辨率**: 不要强制缩放，保持 PDF 渲染的原始分辨率
4. **Summary 完整性**: 不要限制字数和数据项数量，确保数据完整
5. **两阶段检索**: Summary 是快速路径，OCR 是准确路径

---

## 📊 性能指标

### 当前性能
- **PDF 渲染**: ~2-3 秒/页（200 DPI）
- **视频编码**: ~1-2 秒/页（H.265, CRF 23）
- **Summary 生成**: ~2-3 秒/页（Gemini 2.5 Flash Lite）
- **轻量级检索**: 5-10ms（关键词匹配）
- **全页 OCR**: 500-2000ms（DeepSeek OCR API）

### 目标性能
- **简单查询**: <100ms（直接从 Summary 返回）
- **复杂查询**: 600-2100ms（需要 OCR）
- **文件大小**: 原 PDF 的 1/3 到 1/5

---

**交接完成！祝下一个 Agent 工作顺利！** 🎉

