# DKR (Deep Knowledge Retrieval) 项目规范

**版本**: 1.0  
**最后更新**: 2025-11-10  
**状态**: ACTIVE

---

## 📋 目录结构规范

### 1. 数据文件夹统一规范

**规则**: 所有数据文件统一存放在**根目录的 `data/` 文件夹**下。

```
memvid-deepseekocr/
├── data/                          # 统一数据目录（根目录）
│   ├── documents/                 # PDF 原始文件
│   ├── videos/                    # 编码后的 MP4 视频文件
│   ├── summaries/                 # Summary JSON 文件
│   ├── indexes/                   # 索引文件
│   ├── cache/                     # OCR 缓存
│   ├── temp/                      # 临时文件
│   └── library_index.json         # 文档库索引
├── backend/                       # 后端代码（不包含 data 文件夹）
├── frontend/                      # 前端代码
└── visual_memvid/                 # Visual Memvid 核心库
```

**禁止事项**:
- ❌ 不允许在 `backend/` 下创建 `data/` 文件夹
- ❌ 不允许在其他位置创建数据存储文件夹
- ❌ 所有代码必须使用配置文件中的路径，不允许硬编码路径

---

### 2. 环境变量统一规范

**规则**: 所有环境变量统一配置在**根目录的 `.env` 文件**中。

```
memvid-deepseekocr/
├── .env                           # 统一环境变量配置（根目录）
├── backend/                       # 后端代码（不包含 .env）
└── ...
```

**禁止事项**:
- ❌ 不允许在 `backend/` 或其他子目录下创建 `.env` 文件
- ❌ 不允许在代码中硬编码 API Key 或配置信息

---

## 🤖 模型配置规范

### 3. 四大模型配置

DKR 项目使用 4 种不同的 AI 模型，每种模型有明确的用途和配置规范。

#### 3.1 分类模型 (Classification Model)

**用途**: 文档自动分类

**可选模型**:
- `deepseek-chat` (推荐) - 使用 DeepSeek 官方 API Key
- `google/gemini-2.5-flash-preview-09-2025` - 使用 OpenRouter API Key

**配置示例**:
```env
# 分类模型配置
CLASSIFICATION_MODEL_PROVIDER=deepseek          # 可选: deepseek, gemini
CLASSIFICATION_MODEL_NAME=deepseek-chat         # deepseek: deepseek-chat, gemini: google/gemini-2.5-flash-preview-09-2025

# API Keys
DEEPSEEK_API_KEY=sk-xxx                         # DeepSeek 官方 Key
OPENROUTER_API_KEY=sk-or-v1-xxx                 # OpenRouter Key (用于 Gemini)
```

---

#### 3.2 Summary 模型 (Summary Generation Model)

**用途**: 生成文档页面摘要（Layer 2）

**可选模型**:
- `google/gemini-2.5-flash-preview-09-2025` (推荐) - 使用 OpenRouter API Key
- `qwen/qwen3-vl-235b-a22b-instruct` - 使用 OpenRouter API Key

**配置示例**:
```env
# Summary 模型配置
SUMMARY_MODEL_PROVIDER=gemini                   # 可选: gemini, qwen
SUMMARY_MODEL_NAME=google/gemini-2.5-flash-preview-09-2025

# API Key (统一使用 OpenRouter)
OPENROUTER_API_KEY=sk-or-v1-xxx
```

**注意**: Summary 模型的所有选项都通过 OpenRouter 调用，不使用官方 API。

---

#### 3.3 DKR Agent 模型 (Agent Reasoning Model)

**用途**: 智能检索 Agent 的推理和决策

**可选模型**:
- `deepseek-chat` (当前支持) - 使用 DeepSeek 官方 API Key
- `kimi-k2` (预留接口) - 未来支持
- `minimax-m2` (预留接口) - 未来支持

**配置示例**:
```env
# Agent 模型配置
AGENT_LLM_PROVIDER=deepseek                     # 可选: deepseek, kimi, minimax
AGENT_LLM_MODEL=deepseek-chat                   # 模型名称

# API Keys
DEEPSEEK_API_KEY=sk-xxx                         # DeepSeek 官方 Key
KIMI_API_KEY=                                   # 预留：Kimi K2 Key
MINIMAX_API_KEY=                                # 预留：MiniMax M2 Key
```

**预留接口说明**:
- `kimi-k2`: 月之暗面 Kimi K2 模型（未来支持）
- `minimax-m2`: MiniMax M2 模型（未来支持）

---

#### 3.4 OCR 模型 (OCR Recognition Model)

**用途**: 文档 OCR 识别（Layer 3）

**可选模型**:
- `deepseek-ocr` (当前支持) - 自部署 DeepSeek OCR 服务
- `paddle-ocr` (预留接口) - 未来支持
- `gemini-flash` (预留接口) - 未来支持，使用 OpenRouter
- `qwen-235b-vl` (预留接口) - 未来支持，使用 OpenRouter

**配置示例**:
```env
# OCR 模型配置
OCR_MODEL_PROVIDER=deepseek_ocr                 # 可选: deepseek_ocr, paddle_ocr, gemini_flash, qwen_vl
OCR_API_URL=http://111.230.37.43:5010           # DeepSeek OCR 服务地址
OCR_TIMEOUT=300

# 预留配置
PADDLE_OCR_MODEL_PATH=                          # 预留：PaddleOCR 模型路径
OPENROUTER_API_KEY=sk-or-v1-xxx                 # Gemini/Qwen OCR 使用 OpenRouter
```

---

## 🔑 API Key 管理规范

### 4. API Key 统一纳管

**规则**: 所有 API Key 统一在根目录 `.env` 文件中配置。

**API Key 分类**:

| API Key | 用途 | 使用模型 |
|---------|------|----------|
| `DEEPSEEK_API_KEY` | DeepSeek 官方 API | 分类模型（deepseek-chat）<br>Agent 模型（deepseek-chat） |
| `OPENROUTER_API_KEY` | OpenRouter 统一 API | 分类模型（gemini）<br>Summary 模型（gemini-flash, qwen3-vl）<br>OCR 模型（gemini-flash, qwen-vl，预留） |
| `KIMI_API_KEY` | Kimi 官方 API（预留） | Agent 模型（kimi-k2，预留） |
| `MINIMAX_API_KEY` | MiniMax 官方 API（预留） | Agent 模型（minimax-m2，预留） |

**完整 .env 模板**:
```env
# ==================== DeepSeek 官方 API ====================
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# ==================== OpenRouter API ====================
OPENROUTER_API_KEY=sk-or-v1-xxx
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# ==================== 预留：Kimi API ====================
KIMI_API_KEY=
KIMI_BASE_URL=https://api.moonshot.cn/v1

# ==================== 预留：MiniMax API ====================
MINIMAX_API_KEY=
MINIMAX_BASE_URL=https://api.minimax.chat/v1

# ==================== 分类模型配置 ====================
CLASSIFICATION_MODEL_PROVIDER=deepseek
CLASSIFICATION_MODEL_NAME=deepseek-chat

# ==================== Summary 模型配置 ====================
SUMMARY_MODEL_PROVIDER=gemini
SUMMARY_MODEL_NAME=google/gemini-2.5-flash-preview-09-2025

# ==================== Agent 模型配置 ====================
AGENT_LLM_PROVIDER=deepseek
AGENT_LLM_MODEL=deepseek-chat

# ==================== OCR 模型配置 ====================
OCR_MODEL_PROVIDER=deepseek_ocr
OCR_API_URL=http://111.230.37.43:5010
OCR_TIMEOUT=300

# ==================== 数据存储路径 ====================
DATA_DIR=./data
DOCUMENTS_DIR=./data/documents
VIDEOS_DIR=./data/videos
SUMMARIES_DIR=./data/summaries
INDEXES_DIR=./data/indexes
CACHE_DIR=./data/cache
TEMP_DIR=./data/temp

# ==================== 应用配置 ====================
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
BACKEND_RELOAD=true

# ==================== Agent 配置 ====================
AGENT_MAX_ITERATIONS=10
AGENT_CONFIDENCE_THRESHOLD=0.9

# ==================== 文档分类 ====================
DEFAULT_CATEGORIES=年度调研报告,申请书,中期报告,结项报告,其他

# ==================== 日志配置 ====================
LOG_LEVEL=INFO
LOG_FILE=./logs/dkr.log

# ==================== CORS 配置 ====================
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

---

## 🚫 禁止事项

### 5. 严格禁止的操作

1. **❌ 硬编码路径**
   - 不允许在代码中硬编码文件路径
   - 必须使用配置文件中的路径变量

2. **❌ 硬编码 API Key**
   - 不允许在代码中硬编码 API Key
   - 必须从环境变量读取

3. **❌ 多处配置文件**
   - 不允许在多个位置创建 `.env` 文件
   - 只能在根目录维护一个 `.env` 文件

4. **❌ 多处数据文件夹**
   - 不允许在多个位置创建 `data/` 文件夹
   - 只能在根目录维护一个 `data/` 文件夹

5. **❌ 直接使用 CONFIG 字典**
   - 不允许直接修改 `visual_memvid/config.py` 中的 CONFIG 字典
   - 必须通过环境变量覆盖配置

---

## ✅ 最佳实践

### 6. 代码规范

#### 6.1 路径引用规范

**正确示例**:
```python
from app.config import get_settings

settings = get_settings()
data_dir = settings.data_dir  # 使用配置
documents_dir = settings.documents_dir
```

**错误示例**:
```python
# ❌ 硬编码路径
data_dir = "./backend/data"
data_dir = "E:/memvid-deepseekocr/backend/data"
```

#### 6.2 API Key 引用规范

**正确示例**:
```python
from app.config import get_settings

settings = get_settings()
api_key = settings.deepseek_api_key  # 从配置读取
```

**错误示例**:
```python
# ❌ 硬编码 API Key
api_key = "sk-xxx"
```

#### 6.3 模型配置规范

**正确示例**:
```python
from app.config import get_settings

settings = get_settings()

# 根据配置选择模型
if settings.agent_llm_provider == "deepseek":
    api_key = settings.deepseek_api_key
    base_url = settings.deepseek_base_url
elif settings.agent_llm_provider == "kimi":
    api_key = settings.kimi_api_key
    base_url = settings.kimi_base_url
```

---

## 📝 变更日志

### Version 1.0 (2025-11-10)
- ✅ 统一数据文件夹到根目录
- ✅ 统一环境变量到根目录 .env
- ✅ 规范化 4 种模型配置
- ✅ 统一 API Key 管理
- ✅ 预留 Kimi K2 和 MiniMax M2 接口

---

## 🔄 未来扩展

### 7. 预留接口说明

#### 7.1 Agent 模型扩展
- **Kimi K2**: 月之暗面的长上下文模型，适合处理超长文档
- **MiniMax M2**: MiniMax 的多模态模型，适合复杂推理任务

#### 7.2 OCR 模型扩展
- **PaddleOCR**: 开源 OCR 方案，支持离线部署
- **Gemini Flash**: Google 的多模态模型，通过 OpenRouter 调用
- **Qwen 235B VL**: 阿里的视觉语言模型，通过 OpenRouter 调用

---

## 📞 联系方式

如有疑问或建议，请联系项目维护者。

**项目维护者**: DKR Team  
**最后更新**: 2025-11-10

