# DKR Agent API 文档

## 概述

DKR (Deep Knowledge Retrieval) Agent 提供了一套完整的 RESTful API，供外部 Agent 或应用程序调用。系统采用 **无状态架构**，每次查询都是独立的，适合作为外部 Agent 编排系统的子 Agent。

**Base URL**: `http://localhost:8105/api/v1`

**Docker 部署**: `http://localhost:8105/api/v1`

---

## 目录

1. [核心 Agent API](#1-核心-agent-api)
2. [文档管理 API](#2-文档管理-api)
3. [查询 API](#3-查询-api)
4. [系统设置 API](#4-系统设置-api)
5. [健康检查](#5-健康检查)
6. [错误处理](#6-错误处理)
7. [使用示例](#7-使用示例)

---

## 1. 核心 Agent API

### 1.1 Agent 查询（推荐用于外部 Agent）

**端点**: `POST /agent/ask`

**描述**: 供外部 Agent 调用的主要接口。提供自然语言查询，Agent 会自动：
- 理解查询意图
- 选择相关文档
- 定位关键页面
- 调用 OCR 理解内容
- 生成答案并评估置信度

**请求参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| query | string | 是 | 自然语言查询问题 |

**请求示例**:

```bash
curl -X POST "http://localhost:8105/api/v1/agent/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "2023年的研发费用是多少？"
  }'
```

**响应示例**:

```json
{
  "success": true,
  "answer": "根据《2023年度财务报告》第15页，2023年研发费用为1,250万元，同比增长23.5%。",
  "execution_steps": [
    {
      "step": 1,
      "action": "get_library_catalog",
      "description": "查看文档库目录",
      "result": {
        "total_documents": 12,
        "categories": ["财务类", "研究类", "制度类"]
      }
    },
    {
      "step": 2,
      "action": "get_documents_table_of_contents",
      "description": "查看《2023年度财务报告》目录",
      "result": {
        "page_count": 45,
        "relevant_pages": [15, 16, 17]
      }
    },
    {
      "step": 3,
      "action": "get_pages_full_summary",
      "description": "获取第15-17页详细信息",
      "result": {
        "entities": ["研发费用", "1250万元"],
        "key_data": [{"metric": "研发费用", "value": "1250万元"}]
      }
    },
    {
      "step": 4,
      "action": "evaluate_answer_confidence",
      "description": "评估答案质量",
      "result": {
        "confidence": 0.95,
        "reasoning": "数据来源明确，页码准确"
      }
    }
  ],
  "processing_time": 8.5,
  "confidence": 0.95
}
```

**响应字段**:

| 字段 | 类型 | 描述 |
|------|------|------|
| success | boolean | 查询是否成功 |
| answer | string | 生成的答案（包含来源引用） |
| execution_steps | array | Agent 执行步骤详情 |
| processing_time | float | 处理耗时（秒） |
| confidence | float | 答案置信度（0-1） |
| error | string | 错误信息（失败时） |

---

### 1.2 获取文档库概览

**端点**: `GET /agent/library/overview`

**描述**: 获取文档库的分类和文档概览，用于外部 Agent 了解可用资源。

**请求示例**:

```bash
curl -X GET "http://localhost:8105/api/v1/agent/library/overview"
```

**响应示例**:

```json
{
  "success": true,
  "library_overview": {
    "财务类": {
      "document_count": 5,
      "documents": [
        {
          "doc_id": "doc_20251110_001",
          "title": "2023年度财务报告",
          "page_count": 45
        }
      ]
    },
    "研究类": {
      "document_count": 7,
      "documents": [...]
    }
  }
}
```

---

### 1.3 获取分类列表

**端点**: `GET /agent/library/categories`

**描述**: 获取所有文档分类及文档数量。

**请求示例**:

```bash
curl -X GET "http://localhost:8105/api/v1/agent/library/categories"
```

**响应示例**:

```json
{
  "success": true,
  "categories": [
    {
      "name": "财务类",
      "document_count": 5
    },
    {
      "name": "研究类",
      "document_count": 7
    },
    {
      "name": "制度类",
      "document_count": 3
    }
  ]
}
```

---

### 1.4 获取分类下的文档

**端点**: `GET /agent/library/documents/{category}`

**描述**: 获取指定分类下的所有文档。

**路径参数**:

| 参数 | 类型 | 描述 |
|------|------|------|
| category | string | 分类名称（如 "财务类"） |

**请求示例**:

```bash
curl -X GET "http://localhost:8105/api/v1/agent/library/documents/财务类"
```

**响应示例**:

```json
{
  "success": true,
  "category": "财务类",
  "documents": [
    {
      "doc_id": "doc_20251110_001",
      "title": "2023年度财务报告",
      "category": "财务类",
      "page_count": 45,
      "upload_time": "2025-11-10T14:30:00",
      "metadata": {
        "filename": "2023年度财务报告.pdf",
        "doc_summary": "本报告总结了2023年度的财务状况..."
      }
    }
  ]
}
```

---

## 2. 文档管理 API

### 2.1 上传文档

**端点**: `POST /documents/upload`

**描述**: 上传 PDF 文档，系统会自动：
1. 处理文档（PDF → Video + Summary）
2. 使用 LLM 自动分类
3. 添加到文档库

**请求参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| file | file | 是 | PDF 文件（multipart/form-data） |

**请求示例**:

```bash
curl -X POST "http://localhost:8105/api/v1/documents/upload" \
  -F "file=@/path/to/document.pdf"
```

**响应示例**:

```json
{
  "success": true,
  "doc_id": "doc_20251110_143052_a1b2c3d4",
  "category": "财务类",
  "message": "文档已成功上传并分类到 '财务类'"
}
```

---

### 2.2 批量上传文档

**端点**: `POST /documents/upload/batch`

**描述**: 批量上传多个 PDF 文档。

**请求示例**:

```bash
curl -X POST "http://localhost:8105/api/v1/documents/upload/batch" \
  -F "files=@/path/to/doc1.pdf" \
  -F "files=@/path/to/doc2.pdf" \
  -F "files=@/path/to/doc3.pdf"
```

**响应示例**:

```json
{
  "success": true,
  "total": 3,
  "success_count": 2,
  "failed_count": 1,
  "results": [
    {
      "filename": "doc1.pdf",
      "success": true,
      "doc_id": "doc_20251110_001",
      "category": "财务类"
    },
    {
      "filename": "doc2.pdf",
      "success": true,
      "doc_id": "doc_20251110_002",
      "category": "研究类"
    },
    {
      "filename": "doc3.pdf",
      "success": false,
      "error": "文件格式错误"
    }
  ]
}
```

---

### 2.3 获取文档列表

**端点**: `GET /documents/`

**描述**: 获取所有文档或按分类筛选。

**查询参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| category | string | 否 | 分类名称（不填则返回所有） |

**请求示例**:

```bash
# 获取所有文档
curl -X GET "http://localhost:8105/api/v1/documents/"

# 按分类筛选
curl -X GET "http://localhost:8105/api/v1/documents/?category=财务类"
```

**响应示例**:

```json
[
  {
    "doc_id": "doc_20251110_001",
    "title": "2023年度财务报告",
    "category": "财务类",
    "category_confidence": 0.95,
    "metadata": {
      "filename": "2023年度财务报告.pdf",
      "page_count": 45,
      "upload_time": "2025-11-10T14:30:00"
    }
  }
]
```

---

### 2.4 获取单个文档详情

**端点**: `GET /documents/{doc_id}`

**描述**: 获取指定文档的详细信息。

**请求示例**:

```bash
curl -X GET "http://localhost:8105/api/v1/documents/doc_20251110_001"
```

---

### 2.5 删除文档

**端点**: `DELETE /documents/{doc_id}`

**描述**: 删除指定文档及其相关数据。

**请求示例**:

```bash
curl -X DELETE "http://localhost:8105/api/v1/documents/doc_20251110_001"
```

**响应示例**:

```json
{
  "success": true,
  "message": "文档 doc_20251110_001 已删除"
}
```

---

## 3. 查询 API

### 3.1 自然语言查询

**端点**: `POST /query/`

**描述**: 前端用户查询接口（与 `/agent/ask` 功能相同，但返回格式略有不同）。

**请求体**:

```json
{
  "query": "2023年的研发费用是多少？",
  "context": {},
  "options": {}
}
```

**请求示例**:

```bash
curl -X POST "http://localhost:8105/api/v1/query/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "2023年的研发费用是多少？"
  }'
```

**响应示例**:

```json
{
  "success": true,
  "answer": "根据《2023年度财务报告》第15页...",
  "execution_steps": [...],
  "processing_time": 8.5
}
```

---

## 4. 系统设置 API

### 4.1 获取模型配置

**端点**: `GET /settings/models`

**描述**: 获取当前系统使用的模型配置。

**请求示例**:

```bash
curl -X GET "http://localhost:8105/api/v1/settings/models"
```

**响应示例**:

```json
{
  "success": true,
  "settings": {
    "classifier_model": "deepseek-chat",
    "summary_model": "google/gemini-2.5-flash-preview-09-2025",
    "agent_model": "openai/gpt-4.1",
    "ocr_model": "deepseek-ocr",
    "agent_max_iterations": 10,
    "agent_confidence_threshold": 0.9
  }
}
```

---

### 4.2 更新模型配置

**端点**: `POST /settings/models`

**描述**: 更新模型配置并持久化到 `.env` 文件，支持热加载（无需重启）。

**请求体**:

```json
{
  "classifier_model": "deepseek-chat",
  "summary_model": "google/gemini-2.5-flash-preview-09-2025",
  "agent_model": "openai/gpt-4.1",
  "ocr_model": "deepseek-ocr",
  "agent_max_iterations": 10,
  "agent_confidence_threshold": 0.9
}
```

**响应示例**:

```json
{
  "success": true,
  "message": "配置已保存并立即生效，无需重启服务"
}
```

---

### 4.3 获取提示词

**端点**: `GET /settings/prompts`

**描述**: 获取所有提示词文件内容。

**响应示例**:

```json
{
  "success": true,
  "prompts": {
    "dkr_agent_system": "你是林溪源（Vera Lin）...",
    "classifier_system": "你是一个文档分类专家...",
    "summary_system": "你是一个文档总结专家..."
  }
}
```

---

### 4.4 更新提示词

**端点**: `POST /settings/prompts/{prompt_name}`

**描述**: 更新指定提示词文件。

**请求体**:

```json
{
  "content": "你是林溪源（Vera Lin），一位严谨的数据分析师..."
}
```

---

## 5. 健康检查

**端点**: `GET /health`

**描述**: 检查服务是否正常运行。

**请求示例**:

```bash
curl -X GET "http://localhost:8105/health"
```

**响应示例**:

```json
{
  "status": "healthy",
  "service": "DKR 1.0",
  "version": "1.0.0"
}
```

---

## 6. 错误处理

所有 API 在发生错误时返回统一格式：

```json
{
  "detail": "错误描述信息"
}
```

**HTTP 状态码**:

| 状态码 | 描述 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 7. 使用示例

### 7.1 Python 示例

```python
import requests

# 基础 URL
BASE_URL = "http://localhost:8105/api/v1"

# 1. 上传文档
def upload_document(pdf_path):
    url = f"{BASE_URL}/documents/upload"
    with open(pdf_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(url, files=files)
    return response.json()

# 2. Agent 查询
def ask_agent(query):
    url = f"{BASE_URL}/agent/ask"
    data = {"query": query}
    response = requests.post(url, json=data)
    return response.json()

# 3. 获取文档库概览
def get_library_overview():
    url = f"{BASE_URL}/agent/library/overview"
    response = requests.get(url)
    return response.json()

# 使用示例
if __name__ == "__main__":
    # 上传文档
    result = upload_document("2023年度财务报告.pdf")
    print(f"上传成功: {result['doc_id']}, 分类: {result['category']}")
    
    # 查询
    answer = ask_agent("2023年的研发费用是多少？")
    print(f"答案: {answer['answer']}")
    print(f"置信度: {answer.get('confidence', 'N/A')}")
    print(f"耗时: {answer['processing_time']}秒")
    
    # 获取文档库
    overview = get_library_overview()
    print(f"文档库概览: {overview['library_overview']}")
```

### 7.2 JavaScript 示例

```javascript
const BASE_URL = "http://localhost:8105/api/v1";

// 1. 上传文档
async function uploadDocument(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(`${BASE_URL}/documents/upload`, {
    method: 'POST',
    body: formData
  });
  
  return await response.json();
}

// 2. Agent 查询
async function askAgent(query) {
  const response = await fetch(`${BASE_URL}/agent/ask`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ query })
  });
  
  return await response.json();
}

// 3. 获取文档库概览
async function getLibraryOverview() {
  const response = await fetch(`${BASE_URL}/agent/library/overview`);
  return await response.json();
}

// 使用示例
(async () => {
  // 查询
  const answer = await askAgent("2023年的研发费用是多少？");
  console.log("答案:", answer.answer);
  console.log("置信度:", answer.confidence);
  console.log("耗时:", answer.processing_time, "秒");
  
  // 获取文档库
  const overview = await getLibraryOverview();
  console.log("文档库概览:", overview.library_overview);
})();
```

### 7.3 cURL 完整示例

```bash
#!/bin/bash

BASE_URL="http://localhost:8105/api/v1"

# 1. 健康检查
echo "=== 健康检查 ==="
curl -X GET "${BASE_URL}/../health"
echo -e "\n"

# 2. 上传文档
echo "=== 上传文档 ==="
curl -X POST "${BASE_URL}/documents/upload" \
  -F "file=@2023年度财务报告.pdf"
echo -e "\n"

# 3. 获取文档库概览
echo "=== 文档库概览 ==="
curl -X GET "${BASE_URL}/agent/library/overview"
echo -e "\n"

# 4. Agent 查询
echo "=== Agent 查询 ==="
curl -X POST "${BASE_URL}/agent/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "2023年的研发费用是多少？"
  }'
echo -e "\n"

# 5. 获取分类列表
echo "=== 分类列表 ==="
curl -X GET "${BASE_URL}/agent/library/categories"
echo -e "\n"

# 6. 获取指定分类的文档
echo "=== 财务类文档 ==="
curl -X GET "${BASE_URL}/agent/library/documents/财务类"
echo -e "\n"
```

---

## 8. 最佳实践

### 8.1 外部 Agent 集成建议

1. **使用 `/agent/ask` 作为主要接口**
   - 无状态设计，每次查询独立
   - 自动处理文档检索和答案生成
   - 返回详细的执行步骤和置信度

2. **先获取文档库概览**
   - 调用 `/agent/library/overview` 了解可用资源
   - 帮助外部 Agent 决策是否需要查询

3. **批量上传文档**
   - 使用 `/documents/upload/batch` 提高效率
   - 系统会自动分类和索引

4. **监控置信度**
   - 检查返回的 `confidence` 字段
   - 低于阈值时可以要求人工审核

### 8.2 性能优化

1. **缓存文档库概览**
   - 文档库不常变化，可以缓存概览信息
   - 减少不必要的 API 调用

2. **异步上传**
   - 文档处理耗时较长（OCR + Summary）
   - 建议使用异步方式上传

3. **并发控制**
   - Agent 查询会调用 LLM，有一定延迟
   - 建议控制并发数，避免超时

---

## 9. 常见问题

**Q: 如何处理超时？**

A: Agent 查询可能需要 5-15 秒，建议设置 30 秒超时。

**Q: 支持哪些文件格式？**

A: 目前仅支持 PDF 格式。

**Q: 如何提高答案准确性？**

A: 
1. 确保文档质量（清晰的 PDF）
2. 调整 Agent 提示词（`/settings/prompts`）
3. 使用更强的模型（`/settings/models`）

**Q: 是否支持多租户？**

A: 当前版本不支持，所有文档共享同一个库。

---

## 10. 技术架构

```
外部 Agent
    ↓
POST /agent/ask
    ↓
DKR Agent (LangGraph)
    ↓
┌─────────────────────────────────┐
│ 5 Tools:                        │
│ 1. get_library_catalog          │
│ 2. get_documents_table_of_contents │
│ 3. get_pages_full_summary       │
│ 4. search_in_document           │
│ 5. evaluate_answer_confidence   │
└─────────────────────────────────┘
    ↓
Visual-Memvid RAG System
    ↓
DeepSeek OCR API
```

---

## 11. 联系方式

- **GitHub**: https://github.com/sga-jerrylin/DKR-SGA
- **Release**: https://github.com/sga-jerrylin/DKR-SGA/releases/tag/v1.2

---

**版本**: v1.2 (Docker Production Ready)

**最后更新**: 2025-11-10

