# 文件结构清理和重组计划

## 📋 新的文件结构规划

### **统一数据目录：backend/data/**

```
backend/data/
├── documents/              # 📄 上传的PDF原文件
│   └── {doc_id}.pdf
├── videos/                 # 🎬 生成的MP4视频
│   └── {doc_id}.mp4
├── summaries/              # 📝 Summary JSON文件（按文档分文件夹）
│   └── {doc_id}/
│       └── summaries.json
├── indexes/                # 📋 索引文件
│   └── {doc_id}_index.json
├── library_index.json      # 📚 文档库总索引
└── temp/                   # 🗑️ 临时文件（图片等，处理完自动删除）
```

### **配置更新**

**backend/app/config.py**:
```python
DATA_DIR = Path("data")  # backend/data/
DOCUMENTS_DIR = DATA_DIR / "documents"
VIDEOS_DIR = DATA_DIR / "videos"
SUMMARIES_DIR = DATA_DIR / "summaries"
INDEXES_DIR = DATA_DIR / "indexes"
TEMP_DIR = DATA_DIR / "temp"
```

---

## 🗑️ 清理列表

### **删除的文件/文件夹**

1. **根目录空文件夹**：
   - `data/` - 空文件夹
   - `output/` - 测试输出
   - `ocr_cache/` - OCR缓存（移到backend）
   - `test_frames/` - 测试图片

2. **根目录测试脚本**：
   - `test_gemini_summary.py`
   - `test_new_system.py`
   - `test_ocr_simple.py`
   - `test_prompt.py`

3. **根目录测试结果**：
   - `gemini_test_results.json`
   - `prompt_test_results.json`
   - `test_results_analysis.md`

4. **backend重复文件**：
   - `backend/ocr_cache/` - 重复
   - `backend/test_server.py` - 测试脚本

5. **backend/data 中的旧文件**：
   - `backend/data/knowledge.mp4` - 旧测试文件
   - `backend/data/index.json` - 旧索引
   - `backend/data/summaries.json` - 旧格式
   - `backend/data/doc_*.pdf` - 移到 documents/

---

## ✅ 保留的文件/文件夹

1. **核心代码**：
   - `backend/` - 后端服务
   - `frontend/` - 前端服务
   - `visual_memvid/` - 核心库

2. **配置和文档**：
   - `prompts/` - 提示词文件
   - `rules/` - 规则文档
   - `README.md`, `PRD_V1.0_AGENT_FIRST.md` 等

3. **示例代码**：
   - `examples/` - 示例代码

---

## 🔧 需要修改的代码

### **1. backend/app/config.py**
添加新的目录配置

### **2. visual_memvid/enhanced_encoder.py**
修改 Summary 保存逻辑：
- 从保存到 `output_dir/summaries.json`
- 改为保存到 `backend/data/summaries/{doc_id}/summaries.json`

### **3. backend/app/core/document_processor.py**
修改文件路径逻辑：
- PDF 保存到 `backend/data/documents/{doc_id}.pdf`
- 视频保存到 `backend/data/videos/{doc_id}.mp4`
- 索引保存到 `backend/data/indexes/{doc_id}_index.json`

---

## 📝 执行步骤

1. ✅ 创建新的目录结构
2. ✅ 移动现有文件到新位置
3. ✅ 更新代码中的路径配置
4. ✅ 删除旧文件和测试文件
5. ✅ 测试上传功能
6. ✅ 验证文件保存位置正确

