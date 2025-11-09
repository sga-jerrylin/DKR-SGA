# DKR 1.0 产品需求文档（Agent-First 版本）

**版本**: v1.0 Agent-First  
**日期**: 2025-01-15  
**状态**: 准备开发  
**前端技术栈**: Vue 3 + TypeScript + Element Plus  
**核心理念**: Agent-First - 一切交给 Agent 决策

---

## 📋 目录

1. [产品概述](#1-产品概述)
2. [核心理念：Agent-First](#2-核心理念agent-first)
3. [功能需求](#3-功能需求)
4. [技术架构](#4-技术架构)
5. [数据结构设计](#5-数据结构设计)
6. [API 设计](#6-api-设计)
7. [前端设计（Vue 3）](#7-前端设计vue-3)
8. [Agent 工作流程](#8-agent-工作流程)
9. [开发计划](#9-开发计划)
10. [成功指标](#10-成功指标)

---

## 1. 产品概述

### 1.1 产品定位

**DKR (Deep Knowledge Retrieval)** - 基于 Claude Agent SDK + DeepSeek OCR 的智能文档检索系统

**核心创新**:
- ✅ **Agent-First**: 用户只需自然语言交互，Agent 自动决策一切
- ✅ **视觉原生存储**: PDF → H.265 视频（50x 压缩）
- ✅ **4 层渐进式检索**: 图书馆 → 分类 → 文档 → 页面
- ✅ **自动分类**: Agent 自动识别文档类型并分类
- ✅ **本地化部署**: 零 API 成本，数据安全

### 1.2 目标用户

- 金融分析师（年报分析）
- 研究人员（学术论文）
- 法务人员（合同审查）
- 企业知识管理

### 1.3 商业模式

**私有部署**（闭源 6-12 个月）:
- 基础版: $999/月（100 份文档）
- 专业版: $2,999/月（1000 份文档）
- 企业版: $9,999/月（无限文档 + 定制）

---

## 2. 核心理念：Agent-First

### 2.1 传统软件 vs Agent-First 软件

| 维度 | 传统软件 | Agent-First 软件 |
|------|---------|-----------------|
| **文档上传** | 用户选择分类 | Agent 自动分类 |
| **文档查询** | 用户选择文档 + 输入关键词 | 用户自然语言提问 |
| **结果展示** | 返回结果列表 | Agent 生成答案 + 来源 |
| **交互方式** | 表单 + 按钮 | 对话界面 |
| **用户体验** | 需要学习使用 | 像和人聊天一样 |

### 2.2 Agent-First 原则

1. **前端极简**: 只有上传 + 对话框
2. **后端智能**: Agent 全自动决策
3. **自然语言**: 用户只需说话
4. **零配置**: Agent 处理一切

### 2.3 示例对比

**传统软件**:
```
用户操作：
1. 选择分类：财务类 ▼
2. 选择文档：2023年度财务审计报告.pdf ☑
3. 输入关键词：总收入
4. 点击搜索 [搜索]
```

**Agent-First 软件**:
```
用户输入：
"帮我找一下 2023 年的财务审计报告中的总收入"

Agent 自动：
1. 分析意图：财务类、2023、审计报告、总收入
2. 搜索分类：财务类
3. 匹配文档：2023年度财务审计报告.pdf
4. 检索页面：第 5 页
5. 返回答案："2023 年总收入为 5 亿元"
```

---

## 3. 功能需求

### 3.1 核心功能

#### 3.1.1 文档上传与自动处理

**用户操作**:
- 拖拽 PDF 文件到上传区域

**Agent 自动处理**:
1. ✅ 接收文件
2. ✅ 快速生成前 10 页 Summary（8 分钟）
3. ✅ **自动分类**（基于文档名 + 内容摘要）
4. ✅ 更新图书馆索引
5. ✅ 后台异步生成完整 Summary

**用户看到**:
```
✅ "文档已上传，正在处理..."
✅ "文档已自动分类为：财务类"
✅ "文档已就绪，可以开始查询"
```

#### 3.1.2 自然语言查询

**用户输入**:
```
示例 1: "帮我找一下 2023 年的财务审计报告"
示例 2: "公司有哪些关于员工福利的制度？"
示例 3: "最近的研究报告里提到了什么技术趋势？"
```

**Agent 自动决策**:
1. ✅ 分析查询意图（关键词、时间、文档类型）
2. ✅ 搜索图书馆（Layer 0）
3. ✅ 搜索分类（Layer 1）
4. ✅ 搜索文档（Layer 2）
5. ✅ 搜索页面（Layer 3）
6. ✅ 评估置信度（提前终止或深入挖掘）
7. ✅ 生成答案

**用户看到**:
```
✅ 答案："我找到了《2023年度财务审计报告.pdf》..."
✅ 来源：第 5-8 页
✅ 置信度：95%
```

#### 3.1.3 文档管理

**功能**:
- ✅ 文档列表展示（卡片式）
- ✅ 按分类筛选
- ✅ 搜索文档名称
- ✅ 查看文档详情
- ✅ 删除文档（级联删除所有关联文件）

**界面**:
- 侧边栏：分类树
- 主区域：文档卡片列表
- 每个卡片显示：
  - 文档名称
  - 分类标签
  - 页数
  - 上传时间
  - 处理状态

#### 3.1.4 配置管理

**可配置项**:
- ✅ DeepSeek OCR URL
- ✅ LLM API URL + Key（用于 Agent 决策）
- ✅ 分类定义（名称、关键词、描述）
- ✅ Agent 参数（置信度阈值、最大迭代次数）

---

### 3.2 Agent 自动分类

#### 3.2.1 分类定义

**默认分类**:
```json
[
  {
    "name": "财务类",
    "keywords": ["财务", "审计", "预算", "成本", "收入", "支出"],
    "description": "财务报表、审计报告、预算文件等"
  },
  {
    "name": "制度类",
    "keywords": ["制度", "规章", "管理办法", "流程", "规定"],
    "description": "公司制度、管理规定、流程文档等"
  },
  {
    "name": "研究类",
    "keywords": ["研究", "报告", "分析", "趋势", "技术"],
    "description": "研究报告、技术分析、市场调研等"
  },
  {
    "name": "其他",
    "keywords": [],
    "description": "其他类型文档"
  }
]
```

#### 3.2.2 自动分类流程

**输入**:
- 文档名称：`2023年度财务审计报告.pdf`
- 前 10 页 Summary：`本报告是 XX 公司 2023 年度财务审计...`

**Agent 决策**:
```python
prompt = f"""
你是一个文档分类专家。请根据文档名称和内容摘要，将文档分类。

可选分类：
{json.dumps(categories, ensure_ascii=False, indent=2)}

文档名称：{doc_name}
内容摘要：{summary}

请返回 JSON 格式：
{{
    "category": "分类名称",
    "confidence": 0.0-1.0,
    "reasoning": "分类理由"
}}
"""
```

**输出**:
```json
{
  "category": "财务类",
  "confidence": 0.95,
  "reasoning": "文档名称包含'财务'和'审计'，内容涉及财务数据和审计结论"
}
```

---

### 3.3 4 层渐进式检索

#### Layer 0: 图书馆总览

**数据**:
```json
{
  "total_documents": 140,
  "categories": [
    {"name": "财务类", "count": 60},
    {"name": "制度类", "count": 50},
    {"name": "研究类", "count": 30}
  ]
}
```

**Agent 决策**:
- 分析查询意图
- 匹配相关分类
- Token 消耗：~500

#### Layer 1: 分类内文档

**数据**:
```json
{
  "category": "财务类",
  "documents": [
    {
      "doc_id": "uuid-1",
      "doc_name": "2023年度财务审计报告.pdf",
      "doc_summary": "本报告是 XX 公司 2023 年度财务审计...",
      "keywords": ["审计", "2023", "财务"]
    }
  ]
}
```

**Agent 决策**:
- 匹配相关文档（Top 3-5）
- Token 消耗：~3000

#### Layer 2: 文档内页面

**数据**:
```json
{
  "doc_id": "uuid-1",
  "pages": [
    {
      "page": 5,
      "summary": "2023 年总收入 5 亿元，净利润 8000 万元",
      "keywords": ["收入", "利润", "2023"]
    }
  ]
}
```

**Agent 决策**:
- 匹配相关页面（Top 5-10）
- Token 消耗：~6000

#### Layer 3: 完整 OCR

**数据**:
- 完整页面文本（5-10 页）

**Agent 决策**:
- 提取精确答案
- Token 消耗：~5000

**总 Token 消耗**: ~14,500 tokens（远低于一次性加载所有内容）

---

## 4. 技术架构

### 4.1 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│              前端（Vue 3 + TypeScript + Element Plus）        │
│  - 文档上传  - 对话界面  - 文档列表  - 配置管理               │
└─────────────────────────────────────────────────────────────┘
                              ↓ HTTP API / WebSocket
┌─────────────────────────────────────────────────────────────┐
│                      后端 API（FastAPI）                      │
│  - /api/documents/upload  - /api/library/search              │
│  - /api/documents         - /api/config                      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  Agent 层（Claude Agent SDK）                 │
│  - DKR Skills（SKILL.md）                                    │
│  - Agent Loop（动态决策）                                     │
│  - 工具箱：search_library, auto_classify, evaluate_confidence│
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    核心处理层（现有代码）                      │
│  - EnhancedPDFEncoder  - VisualRetriever  - OCRClient       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      存储层（本地文件系统）                    │
│  - library_index.json  - document_summaries.json             │
│  - summaries/  - videos/  - documents/  - ocr_cache/         │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 技术栈

#### 后端
- **框架**: FastAPI
- **Agent SDK**: Claude Agent SDK (Python)
- **任务队列**: FastAPI BackgroundTasks（V1.0 简化版）
- **LLM**: DeepSeek Chat API（用于 Agent 决策）
- **OCR**: DeepSeek OCR（本地部署）
- **存储**: 本地文件系统（JSON）

#### 前端
- **框架**: Vue 3 + TypeScript
- **UI 库**: Element Plus
- **状态管理**: Pinia
- **HTTP 客户端**: Axios
- **WebSocket**: Socket.IO Client
- **构建工具**: Vite

#### 部署
- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx

---

## 5. 数据结构设计

### 5.1 library_index.json

```json
{
  "library": {
    "total_documents": 140,
    "last_updated": "2025-01-15T10:30:00Z",
    "categories": [
      {
        "category_id": "cat-finance",
        "name": "财务类",
        "count": 60,
        "keywords": ["财务", "审计", "预算"],
        "doc_ids": ["uuid-1", "uuid-2"],
        "auto_classified": 58,
        "manual_classified": 2
      }
    ]
  }
}
```

### 5.2 document_summaries.json

```json
{
  "documents": [
    {
      "doc_id": "uuid-1",
      "doc_name": "2023年度财务审计报告.pdf",
      "category": "财务类",
      "category_confidence": 0.95,
      "auto_classified": true,
      "doc_summary": "本报告是 XX 公司 2023 年度财务审计报告...",
      "pages": 120,
      "keywords": ["审计", "2023", "财务"],
      "key_data": {
        "年份": "2023",
        "总收入": "5亿元"
      },
      "upload_time": "2025-01-15T10:00:00Z",
      "processing_status": "completed"
    }
  ]
}
```

### 5.3 summaries/{doc_id}.json

```json
{
  "doc_id": "uuid-1",
  "doc_name": "2023年度财务审计报告.pdf",
  "total_pages": 120,
  "summaries": [
    {
      "page": 1,
      "frame_num": 0,
      "summary": "2023年度财务审计报告封面",
      "keywords": ["2023", "财务", "审计"],
      "has_table": false,
      "has_formula": false,
      "has_chart": false
    }
  ]
}
```

---

## 6. API 设计

### 6.1 RESTful API

#### 6.1.1 文档管理

**上传文档**
```http
POST /api/v1/documents/upload
Content-Type: multipart/form-data

Request:
- file: PDF 文件

Response:
{
  "doc_id": "uuid-1",
  "doc_name": "2023年度财务审计报告.pdf",
  "status": "processing",
  "message": "文档已上传，正在处理..."
}
```

**获取文档列表**
```http
GET /api/v1/documents?category=财务类&page=1&page_size=20

Response:
{
  "total": 60,
  "documents": [
    {
      "doc_id": "uuid-1",
      "doc_name": "2023年度财务审计报告.pdf",
      "category": "财务类",
      "pages": 120,
      "upload_time": "2025-01-15T10:00:00Z",
      "status": "completed"
    }
  ]
}
```

**删除文档**
```http
DELETE /api/v1/documents/{doc_id}

Response:
{
  "success": true,
  "message": "文档已删除"
}
```

#### 6.1.2 查询与问答

**提交查询（Agent 处理）**
```http
POST /api/v1/query
Content-Type: application/json

Request:
{
  "query": "帮我找一下 2023 年的财务审计报告中的总收入"
}

Response:
{
  "query_id": "query-uuid-1",
  "status": "processing",
  "message": "Agent 正在处理您的查询..."
}
```

**获取查询结果**
```http
GET /api/v1/query/{query_id}

Response:
{
  "query_id": "query-uuid-1",
  "status": "completed",
  "answer": "2023 年总收入为 5 亿元",
  "sources": [
    {
      "doc_id": "uuid-1",
      "doc_name": "2023年度财务审计报告.pdf",
      "pages": [5, 6]
    }
  ],
  "confidence": 0.95,
  "agent_steps": [
    "分析查询意图：财务类、2023、总收入",
    "搜索分类：财务类（60 份文档）",
    "匹配文档：2023年度财务审计报告.pdf",
    "检索页面：第 5-6 页",
    "提取答案：5 亿元"
  ]
}
```

#### 6.1.3 配置管理

**获取配置**
```http
GET /api/v1/config

Response:
{
  "ocr": {
    "endpoint": "http://43.139.167.250:8200",
    "model": "deepseek-vl"
  },
  "llm": {
    "provider": "deepseek",
    "endpoint": "https://api.deepseek.com/v1",
    "model": "deepseek-chat"
  },
  "categories": [
    {
      "name": "财务类",
      "keywords": ["财务", "审计"],
      "description": "财务报表、审计报告等"
    }
  ]
}
```

**更新配置**
```http
PUT /api/v1/config
Content-Type: application/json

Request:
{
  "ocr": {
    "endpoint": "http://new-ocr-url:8200"
  }
}

Response:
{
  "success": true,
  "message": "配置已更新"
}
```

### 6.2 外部 Agent 调用 API（重要！）

**设计理念**：DKR 本身也是一个 Skill/Tool，可以被其他 Agent 调用

#### 6.2.1 Agent-to-Agent API

**简化查询接口（推荐）**
```http
POST /api/v1/agent/ask
Content-Type: application/json
Authorization: Bearer {api_key}

Request:
{
  "query": "帮我找一下 2023 年的财务审计报告中的总收入",
  "context": {
    "user_id": "external-agent-123",
    "session_id": "session-456"
  },
  "options": {
    "return_sources": true,
    "return_agent_steps": false,
    "max_results": 5
  }
}

Response:
{
  "success": true,
  "answer": "2023 年总收入为 5 亿元",
  "sources": [
    {
      "doc_id": "uuid-1",
      "doc_name": "2023年度财务审计报告.pdf",
      "pages": [5, 6],
      "relevance_score": 0.95
    }
  ],
  "confidence": 0.95,
  "token_usage": {
    "total": 14500,
    "breakdown": {
      "layer_0": 500,
      "layer_1": 3000,
      "layer_2": 6000,
      "layer_3": 5000
    }
  }
}
```

#### 6.2.2 批量查询接口

**用于外部 Agent 批量处理**
```http
POST /api/v1/agent/batch-ask
Content-Type: application/json
Authorization: Bearer {api_key}

Request:
{
  "queries": [
    "2023 年总收入是多少？",
    "2023 年净利润是多少？",
    "2023 年研发投入占比？"
  ],
  "context": {
    "user_id": "external-agent-123"
  }
}

Response:
{
  "success": true,
  "results": [
    {
      "query": "2023 年总收入是多少？",
      "answer": "5 亿元",
      "confidence": 0.95
    },
    {
      "query": "2023 年净利润是多少？",
      "answer": "8000 万元",
      "confidence": 0.92
    },
    {
      "query": "2023 年研发投入占比？",
      "answer": "15%",
      "confidence": 0.88
    }
  ],
  "total_token_usage": 42000
}
```

#### 6.2.3 文档检索接口（结构化）

**用于外部 Agent 获取结构化数据**
```http
POST /api/v1/agent/search
Content-Type: application/json
Authorization: Bearer {api_key}

Request:
{
  "query": "2023 财务数据",
  "filters": {
    "category": "财务类",
    "time_range": {
      "start": "2023-01-01",
      "end": "2023-12-31"
    },
    "doc_types": ["审计报告", "财务报表"]
  },
  "return_format": "structured"  // structured | raw | summary
}

Response:
{
  "success": true,
  "results": [
    {
      "doc_id": "uuid-1",
      "doc_name": "2023年度财务审计报告.pdf",
      "matched_pages": [
        {
          "page": 5,
          "content": "2023 年总收入为 5 亿元，同比增长 20%",
          "structured_data": {
            "年份": "2023",
            "总收入": "5亿元",
            "同比增长": "20%"
          },
          "relevance_score": 0.95
        }
      ]
    }
  ]
}
```

#### 6.2.4 Claude Skills 格式接口

**符合 Claude Skills 规范的接口**
```http
GET /api/v1/agent/skill-metadata

Response:
{
  "name": "dkr-document-retrieval",
  "version": "1.0.0",
  "description": "DKR 文档检索 Skill - 支持多文档智能检索",
  "capabilities": [
    "document_search",
    "batch_query",
    "structured_extraction"
  ],
  "endpoints": {
    "ask": "/api/v1/agent/ask",
    "batch_ask": "/api/v1/agent/batch-ask",
    "search": "/api/v1/agent/search"
  },
  "authentication": {
    "type": "bearer_token",
    "header": "Authorization"
  },
  "rate_limits": {
    "requests_per_minute": 60,
    "tokens_per_day": 1000000
  }
}
```

#### 6.2.5 API Key 管理

**生成 API Key**
```http
POST /api/v1/admin/api-keys
Content-Type: application/json

Request:
{
  "name": "External Agent - Finance Bot",
  "permissions": ["read", "query"],
  "rate_limit": {
    "requests_per_minute": 60
  },
  "expires_at": "2025-12-31T23:59:59Z"
}

Response:
{
  "api_key": "dkr_sk_1234567890abcdef",
  "name": "External Agent - Finance Bot",
  "created_at": "2025-01-15T10:00:00Z",
  "expires_at": "2025-12-31T23:59:59Z"
}
```

**列出 API Keys**
```http
GET /api/v1/admin/api-keys

Response:
{
  "api_keys": [
    {
      "id": "key-1",
      "name": "External Agent - Finance Bot",
      "permissions": ["read", "query"],
      "created_at": "2025-01-15T10:00:00Z",
      "last_used_at": "2025-01-15T15:30:00Z",
      "usage": {
        "requests_today": 150,
        "tokens_today": 45000
      }
    }
  ]
}
```

**撤销 API Key**
```http
DELETE /api/v1/admin/api-keys/{key_id}

Response:
{
  "success": true,
  "message": "API Key 已撤销"
}
```

### 6.3 WebSocket API

**实时进度推送**
```javascript
// 连接 WebSocket
ws://localhost:8000/ws/documents/{doc_id}

// 接收消息
{
  "type": "progress",
  "doc_id": "uuid-1",
  "stage": "summary_generation",
  "progress": 45,
  "message": "正在生成 Summary... (45/120 页)"
}

{
  "type": "completed",
  "doc_id": "uuid-1",
  "category": "财务类",
  "message": "文档处理完成，已自动分类为：财务类"
}
```

### 6.4 外部 Agent 调用示例

#### 示例 1: Python Agent 调用

```python
import requests

class DKRClient:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def ask(self, query: str) -> dict:
        response = requests.post(
            f"{self.api_url}/api/v1/agent/ask",
            headers=self.headers,
            json={"query": query}
        )
        return response.json()

# 使用示例
dkr = DKRClient(
    api_url="http://localhost:8000",
    api_key="dkr_sk_1234567890abcdef"
)

result = dkr.ask("2023 年总收入是多少？")
print(result["answer"])  # "5 亿元"
```

#### 示例 2: Claude Agent 调用（使用 Skills）

```python
# skills/dkr_retrieval/SKILL.md
from anthropic import Anthropic
import requests

def search_documents(query: str) -> str:
    """
    在 DKR 文档库中搜索信息

    Args:
        query: 自然语言查询

    Returns:
        搜索结果和来源
    """
    response = requests.post(
        "http://localhost:8000/api/v1/agent/ask",
        headers={"Authorization": "Bearer dkr_sk_xxx"},
        json={"query": query}
    )

    result = response.json()
    return f"{result['answer']}\n来源：{result['sources'][0]['doc_name']}"

# Claude Agent 使用
client = Anthropic(api_key="sk-xxx")

response = client.messages.create(
    model="claude-sonnet-4",
    tools=[{
        "name": "search_documents",
        "description": "在 DKR 文档库中搜索信息",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"}
            }
        }
    }],
    messages=[{
        "role": "user",
        "content": "帮我查一下公司 2023 年的财务数据"
    }]
)
```

#### 示例 3: LangChain 集成

```python
from langchain.tools import Tool
from langchain.agents import initialize_agent

def dkr_search(query: str) -> str:
    """DKR 文档检索工具"""
    response = requests.post(
        "http://localhost:8000/api/v1/agent/ask",
        headers={"Authorization": "Bearer dkr_sk_xxx"},
        json={"query": query}
    )
    return response.json()["answer"]

dkr_tool = Tool(
    name="DKR Document Search",
    func=dkr_search,
    description="在公司文档库中搜索信息，支持财务、制度、研究等文档"
)

agent = initialize_agent(
    tools=[dkr_tool],
    llm=llm,
    agent="zero-shot-react-description"
)

agent.run("公司 2023 年的研发投入是多少？")
```

---

## 7. 前端设计（Vue 3）

### 7.1 页面结构

```
frontend/
├── src/
│   ├── views/
│   │   ├── Home.vue              # 主页（上传 + 对话）
│   │   ├── Documents.vue         # 文档管理
│   │   └── Settings.vue          # 配置管理
│   ├── components/
│   │   ├── ChatInterface.vue     # 对话界面
│   │   ├── DocumentUpload.vue    # 文档上传
│   │   ├── DocumentList.vue      # 文档列表
│   │   ├── DocumentCard.vue      # 文档卡片
│   │   └── CategoryTree.vue      # 分类树
│   ├── stores/
│   │   ├── documents.ts          # 文档状态管理
│   │   ├── chat.ts               # 对话状态管理
│   │   └── config.ts             # 配置状态管理
│   ├── api/
│   │   ├── documents.ts          # 文档 API
│   │   ├── query.ts              # 查询 API
│   │   └── config.ts             # 配置 API
│   └── types/
│       ├── document.ts           # 文档类型定义
│       ├── query.ts              # 查询类型定义
│       └── config.ts             # 配置类型定义
```

### 7.2 主页设计（Home.vue）

**核心原则**：极简、自然语言优先

```vue
<template>
  <el-container class="home-container">
    <!-- 顶部：上传区域 -->
    <el-header height="200px">
      <DocumentUpload @upload-success="handleUploadSuccess" />
    </el-header>

    <!-- 中间：对话界面 -->
    <el-main>
      <ChatInterface
        :messages="messages"
        @send-message="handleSendMessage"
      />
    </el-main>

    <!-- 右侧：文档列表（可折叠） -->
    <el-aside width="300px" v-if="showDocumentList">
      <DocumentList :documents="documents" />
    </el-aside>
  </el-container>
</template>
```

### 7.3 对话界面（ChatInterface.vue）

**特点**：
- ✅ 纯自然语言输入
- ✅ 显示 Agent 决策过程（可折叠）
- ✅ 显示来源文档（可点击跳转）
- ✅ 支持 Ctrl+Enter 发送

```vue
<template>
  <div class="chat-interface">
    <!-- 消息列表 -->
    <div class="messages-container">
      <div
        v-for="msg in messages"
        :key="msg.id"
        :class="['message', msg.role]"
      >
        <div class="message-content">
          {{ msg.content }}
        </div>

        <!-- Agent 步骤（可选） -->
        <div v-if="msg.agent_steps" class="agent-steps">
          <el-collapse>
            <el-collapse-item title="查看 Agent 决策过程">
              <div v-for="(step, idx) in msg.agent_steps" :key="idx">
                {{ idx + 1 }}. {{ step }}
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>

        <!-- 来源文档 -->
        <div v-if="msg.sources" class="sources">
          <el-tag
            v-for="source in msg.sources"
            :key="source.doc_id"
            @click="jumpToDocument(source)"
          >
            {{ source.doc_name }} (第 {{ source.pages.join(', ') }} 页)
          </el-tag>
        </div>
      </div>
    </div>

    <!-- 输入框 -->
    <div class="input-container">
      <el-input
        v-model="inputText"
        type="textarea"
        :rows="3"
        placeholder="问我任何问题，比如：
        - 帮我找一下 2023 年的财务审计报告
        - 公司有哪些关于员工福利的制度？
        - 最近的研究报告里提到了什么技术趋势？"
        @keydown.enter.ctrl="handleSend"
      />
      <el-button
        type="primary"
        :loading="loading"
        @click="handleSend"
      >
        发送 (Ctrl+Enter)
      </el-button>
    </div>
  </div>
</template>
```

### 7.4 文档上传（DocumentUpload.vue）

**特点**：
- ✅ 拖拽上传
- ✅ WebSocket 实时进度
- ✅ 自动分类提示

```vue
<template>
  <el-upload
    class="upload-demo"
    drag
    :action="uploadUrl"
    :on-success="handleSuccess"
    :before-upload="beforeUpload"
    accept=".pdf"
  >
    <el-icon class="el-icon--upload"><upload-filled /></el-icon>
    <div class="el-upload__text">
      拖拽 PDF 文件到这里，或 <em>点击上传</em>
    </div>
    <template #tip>
      <div class="el-upload__tip">
        Agent 会自动分类和处理文档
      </div>
    </template>
  </el-upload>

  <!-- 处理进度（WebSocket 实时更新） -->
  <el-progress
    v-if="uploading"
    :percentage="progress"
    :status="progressStatus"
  >
    <template #default="{ percentage }">
      <span>{{ progressMessage }} ({{ percentage }}%)</span>
    </template>
  </el-progress>
</template>
```

---

## 8. Agent 工作流程

### 8.1 Agent 架构

```python
class DKRAgent:
    """DKR Agent - 完全自主决策的文档检索 Agent"""

    def __init__(self, llm_client, tools):
        self.llm = llm_client
        self.tools = tools  # search_library, auto_classify, evaluate_confidence
        self.max_iterations = 10
        self.confidence_threshold = 0.9

    async def ask(self, user_query: str) -> Dict:
        """处理用户查询"""
        # Step 1: 分析查询意图
        intent = await self.tools["analyze_query"](user_query)

        # Step 2: Agent Loop - 动态决策
        confidence = 0.0
        results = []
        agent_steps = []

        for iteration in range(self.max_iterations):
            # Agent 决定下一步行动
            action = await self._decide_next_action(
                query=user_query,
                intent=intent,
                current_results=results,
                confidence=confidence
            )

            agent_steps.append(action["description"])

            # 执行工具
            tool_result = await self.tools[action["tool"]](**action["params"])
            results = self._merge_results(results, tool_result)

            # 评估置信度
            confidence = await self.tools["evaluate_confidence"](
                query=user_query,
                results=results
            )

            # 提前终止
            if confidence > self.confidence_threshold:
                break

        return {
            "answer": await self._generate_answer(user_query, results),
            "sources": results,
            "confidence": confidence,
            "agent_steps": agent_steps
        }
```

### 8.2 Agent 工具箱

#### 8.2.1 analyze_query

**功能**：分析查询意图

**输入**：
```python
{
  "query": "帮我找一下 2023 年的财务审计报告中的总收入"
}
```

**输出**：
```python
{
  "intent": {
    "keywords": ["2023", "财务", "审计", "总收入"],
    "time_range": {"year": 2023},
    "doc_type": "财务类",
    "query_type": "factual",  # factual, exploratory, comparative
    "expected_answer_type": "number"
  }
}
```

#### 8.2.2 search_library

**功能**：4 层渐进式检索

**输入**：
```python
{
  "query": "帮我找一下 2023 年的财务审计报告中的总收入",
  "intent": {...},
  "layer": 0  # 0: library, 1: category, 2: document, 3: page
}
```

**输出**：
```python
{
  "layer": 0,
  "matched_categories": ["财务类"],
  "confidence": 0.9,
  "next_layer": 1
}
```

#### 8.2.3 auto_classify

**功能**：自动分类文档

**输入**：
```python
{
  "doc_name": "2023年度财务审计报告.pdf",
  "doc_summary": "本报告是 XX 公司 2023 年度财务审计..."
}
```

**输出**：
```python
{
  "category": "财务类",
  "confidence": 0.95,
  "reasoning": "文档名称包含'财务'和'审计'，内容涉及财务数据"
}
```

#### 8.2.4 evaluate_confidence

**功能**：评估当前结果的置信度

**输入**：
```python
{
  "query": "帮我找一下 2023 年的财务审计报告中的总收入",
  "results": [
    {
      "doc_id": "uuid-1",
      "page": 5,
      "content": "2023 年总收入为 5 亿元"
    }
  ]
}
```

**输出**：
```python
{
  "confidence": 0.95,
  "reasoning": "找到明确的数字答案，与查询高度匹配",
  "should_continue": false
}
```

### 8.3 Agent 决策流程图

```
用户查询："帮我找一下 2023 年的财务审计报告中的总收入"
    ↓
[Step 1] analyze_query
    → 意图：财务类、2023、总收入
    ↓
[Step 2] search_library (Layer 0)
    → 匹配分类：财务类（60 份文档）
    → 置信度：0.7（需要继续）
    ↓
[Step 3] search_library (Layer 1)
    → 匹配文档：2023年度财务审计报告.pdf
    → 置信度：0.85（需要继续）
    ↓
[Step 4] search_library (Layer 2)
    → 匹配页面：第 5-6 页
    → 置信度：0.92（可以终止）
    ↓
[Step 5] generate_answer
    → 答案："2023 年总收入为 5 亿元"
    → 来源：第 5 页
```

---

## 9. 开发计划

### 9.1 总体时间表

**总计**：3-4 周

| 阶段 | 时间 | 主要任务 | 交付物 |
|------|------|---------|--------|
| **Phase 1** | 1 周 | 后端重构 + Agent 实现 | Agent SDK 集成、自动分类、4 层检索 |
| **Phase 2** | 1 周 | API 开发 + WebSocket | RESTful API、实时进度推送 |
| **Phase 3** | 1 周 | Vue 3 前端开发 | 上传界面、对话界面、文档管理 |
| **Phase 4** | 3-5 天 | 集成测试 + 优化 | 端到端测试、性能优化 |

### 9.2 Phase 1: 后端重构 + Agent 实现（1 周）

#### 9.2.1 项目结构重构

**目标**：将现有 MVP 代码重构为模块化架构

**任务**：
- ✅ 创建 `backend/` 目录
- ✅ 迁移现有代码到 `backend/core/`
- ✅ 创建 `backend/agent/` 目录（Agent 相关）
- ✅ 创建 `backend/api/` 目录（FastAPI 路由）
- ✅ 创建 `backend/storage/` 目录（数据存储）

**新目录结构**：
```
backend/
├── core/                      # 核心处理层（现有代码）
│   ├── pdf_encoder.py
│   ├── ocr_client.py
│   ├── enhanced_encoder.py
│   ├── visual_retriever.py
│   └── ocr_cache.py
├── agent/                     # Agent 层
│   ├── dkr_agent.py          # DKR Agent 主类
│   ├── tools/                # Agent 工具箱
│   │   ├── analyze_query.py
│   │   ├── search_library.py
│   │   ├── auto_classify.py
│   │   └── evaluate_confidence.py
│   └── skills/               # Claude Skills
│       └── document_retrieval/
│           ├── SKILL.md
│           └── tools.py
├── api/                       # FastAPI 路由
│   ├── documents.py
│   ├── query.py
│   └── config.py
├── storage/                   # 数据存储管理
│   ├── library_manager.py    # 图书馆索引管理
│   ├── document_manager.py   # 文档管理
│   └── config_manager.py     # 配置管理
├── models/                    # 数据模型
│   ├── document.py
│   ├── query.py
│   └── config.py
└── main.py                    # FastAPI 应用入口
```

#### 9.2.2 Agent SDK 集成

**任务**：
- ✅ 安装 Claude Agent SDK
- ✅ 创建 DKRAgent 类
- ✅ 实现 Agent Loop
- ✅ 实现工具箱（analyze_query, search_library, auto_classify, evaluate_confidence）

**关键代码**：
```python
# backend/agent/dkr_agent.py
from anthropic import Anthropic

class DKRAgent:
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.tools = self._load_tools()

    async def ask(self, user_query: str) -> Dict:
        # Agent Loop 实现
        pass
```

#### 9.2.3 自动分类实现

**任务**：
- ✅ 实现 `auto_classify` 工具
- ✅ 定义默认分类（财务类、制度类、研究类、其他）
- ✅ 实现分类 Prompt
- ✅ 测试分类准确率（目标 >90%）

**关键代码**：
```python
# backend/agent/tools/auto_classify.py
async def auto_classify(doc_name: str, doc_summary: str) -> Dict:
    prompt = f"""
    你是一个文档分类专家。请根据文档名称和内容摘要，将文档分类。

    可选分类：
    - 财务类：财务报表、审计报告、预算文件等
    - 制度类：公司制度、管理规定、流程文档等
    - 研究类：研究报告、技术分析、市场调研等
    - 其他：其他类型文档

    文档名称：{doc_name}
    内容摘要：{doc_summary}

    请返回 JSON 格式：
    {{
        "category": "分类名称",
        "confidence": 0.0-1.0,
        "reasoning": "分类理由"
    }}
    """

    response = await llm_client.complete(prompt)
    return json.loads(response)
```

#### 9.2.4 4 层检索实现

**任务**：
- ✅ 创建 `library_index.json`（Layer 0）
- ✅ 创建 `document_summaries.json`（Layer 1）
- ✅ 复用现有 `summaries/{doc_id}.json`（Layer 2）
- ✅ 实现 `search_library` 工具（支持 4 层）

**关键代码**：
```python
# backend/agent/tools/search_library.py
async def search_library(query: str, intent: Dict, layer: int) -> Dict:
    if layer == 0:
        # 搜索图书馆（分类）
        return search_categories(query, intent)
    elif layer == 1:
        # 搜索分类内文档
        return search_documents(query, intent)
    elif layer == 2:
        # 搜索文档内页面
        return search_pages(query, intent)
    elif layer == 3:
        # 完整 OCR
        return extract_full_content(query, intent)
```

### 9.3 Phase 2: API 开发 + WebSocket（1 周）

#### 9.3.1 FastAPI 应用搭建

**任务**：
- ✅ 创建 FastAPI 应用
- ✅ 配置 CORS
- ✅ 配置 WebSocket
- ✅ 实现路由（documents, query, config）

**关键代码**：
```python
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="DKR API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由
app.include_router(documents_router, prefix="/api/v1/documents")
app.include_router(query_router, prefix="/api/v1/query")
app.include_router(config_router, prefix="/api/v1/config")
```

#### 9.3.2 文档管理 API

**任务**：
- ✅ `POST /api/v1/documents/upload`（上传文档）
- ✅ `GET /api/v1/documents`（获取文档列表）
- ✅ `GET /api/v1/documents/{doc_id}`（获取文档详情）
- ✅ `DELETE /api/v1/documents/{doc_id}`（删除文档）

#### 9.3.3 查询 API

**任务**：
- ✅ `POST /api/v1/query`（提交查询）
- ✅ `GET /api/v1/query/{query_id}`（获取查询结果）

#### 9.3.4 外部 Agent API（重要！）

**任务**：
- ✅ `POST /api/v1/agent/ask`（简化查询接口）
- ✅ `POST /api/v1/agent/batch-ask`（批量查询）
- ✅ `POST /api/v1/agent/search`（结构化检索）
- ✅ `GET /api/v1/agent/skill-metadata`（Skills 元数据）
- ✅ API Key 管理（生成、列出、撤销）
- ✅ API Key 认证中间件
- ✅ 速率限制（Rate Limiting）

**关键代码**：
```python
# backend/api/agent.py
from fastapi import APIRouter, Depends, HTTPException
from backend.auth import verify_api_key

router = APIRouter()

@router.post("/ask")
async def agent_ask(
    request: AgentAskRequest,
    api_key: str = Depends(verify_api_key)
):
    """外部 Agent 调用接口"""
    # 调用 DKR Agent
    result = await dkr_agent.ask(request.query)

    return {
        "success": True,
        "answer": result["answer"],
        "sources": result["sources"],
        "confidence": result["confidence"],
        "token_usage": result["token_usage"]
    }

@router.post("/batch-ask")
async def agent_batch_ask(
    request: AgentBatchAskRequest,
    api_key: str = Depends(verify_api_key)
):
    """批量查询接口"""
    results = []
    total_tokens = 0

    for query in request.queries:
        result = await dkr_agent.ask(query)
        results.append({
            "query": query,
            "answer": result["answer"],
            "confidence": result["confidence"]
        })
        total_tokens += result["token_usage"]["total"]

    return {
        "success": True,
        "results": results,
        "total_token_usage": total_tokens
    }
```

**API Key 认证**：
```python
# backend/auth.py
from fastapi import Header, HTTPException

async def verify_api_key(authorization: str = Header(None)):
    """验证 API Key"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing API Key")

    api_key = authorization.replace("Bearer ", "")

    # 验证 API Key
    key_info = await api_key_manager.verify(api_key)
    if not key_info:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    # 检查速率限制
    if not await rate_limiter.check(api_key):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    return api_key
```

#### 9.3.5 WebSocket 实时进度

**任务**：
- ✅ 实现 WebSocket 连接
- ✅ 推送文档处理进度
- ✅ 推送自动分类结果

**关键代码**：
```python
# backend/api/websocket.py
from fastapi import WebSocket

@app.websocket("/ws/documents/{doc_id}")
async def websocket_endpoint(websocket: WebSocket, doc_id: str):
    await websocket.accept()

    # 监听文档处理进度
    async for progress in document_processor.process(doc_id):
        await websocket.send_json({
            "type": "progress",
            "doc_id": doc_id,
            "progress": progress["percentage"],
            "message": progress["message"]
        })

    await websocket.send_json({
        "type": "completed",
        "doc_id": doc_id,
        "category": progress["category"]
    })
```

### 9.4 Phase 3: Vue 3 前端开发（1 周）

#### 9.4.1 项目初始化

**任务**：
- ✅ 使用 Vite 创建 Vue 3 + TypeScript 项目
- ✅ 安装 Element Plus
- ✅ 安装 Pinia（状态管理）
- ✅ 安装 Axios（HTTP 客户端）
- ✅ 安装 Socket.IO Client（WebSocket）

**命令**：
```bash
npm create vite@latest frontend -- --template vue-ts
cd frontend
npm install element-plus
npm install pinia
npm install axios
npm install socket.io-client
```

#### 9.4.2 核心组件开发

**任务**：
- ✅ `DocumentUpload.vue`（文档上传 + 实时进度）
- ✅ `ChatInterface.vue`（对话界面）
- ✅ `DocumentList.vue`（文档列表）
- ✅ `DocumentCard.vue`（文档卡片）

#### 9.4.3 页面开发

**任务**：
- ✅ `Home.vue`（主页：上传 + 对话）
- ✅ `Documents.vue`（文档管理）
- ✅ `Settings.vue`（配置管理）

#### 9.4.4 状态管理

**任务**：
- ✅ `stores/documents.ts`（文档状态）
- ✅ `stores/chat.ts`（对话状态）
- ✅ `stores/config.ts`（配置状态）

### 9.5 Phase 4: 集成测试 + 优化（3-5 天）

#### 9.5.1 端到端测试

**测试场景**：
1. ✅ 上传文档 → 自动分类 → 查询 → 返回答案
2. ✅ 上传多个文档 → 跨文档查询
3. ✅ 删除文档 → 验证级联删除
4. ✅ 修改配置 → 验证生效

#### 9.5.2 Agent 决策测试

**测试场景**：
1. ✅ 简单查询（直接匹配）
2. ✅ 复杂查询（需要多层检索）
3. ✅ 模糊查询（需要 Agent 推理）
4. ✅ 无结果查询（Agent 提示）

#### 9.5.3 性能优化

**优化目标**：
- ✅ 查询响应时间 <5 秒
- ✅ Token 消耗 <20,000/查询
- ✅ 文档处理速度（快速 Summary <10 分钟）

---

## 10. 成功指标

### 10.1 功能指标

| 指标 | 目标 | 验证方式 |
|------|------|---------|
| **自动分类准确率** | >90% | 人工验证 100 份文档 |
| **查询响应时间** | <5 秒 | 性能测试（100 次查询） |
| **Token 消耗** | <20,000/查询 | 监控 LLM API 调用 |
| **文档处理速度** | 快速 Summary <10 分钟 | 测试 100 页文档 |
| **WebSocket 实时性** | <1 秒延迟 | 网络测试 |

### 10.2 用户体验指标

| 指标 | 目标 | 验证方式 |
|------|------|---------|
| **自然语言理解** | >95% 意图识别准确率 | 用户测试（50 个查询） |
| **界面简洁度** | 无需培训即可使用 | 用户测试（5 人） |
| **Agent 透明度** | 用户能理解 Agent 决策 | 用户反馈 |

### 10.3 技术指标

| 指标 | 目标 | 验证方式 |
|------|------|---------|
| **API 可用性** | >99.9% | 监控 |
| **错误率** | <1% | 日志分析 |
| **并发支持** | 10 用户同时使用 | 压力测试 |

### 10.4 外部 Agent API 指标

| 指标 | 目标 | 验证方式 |
|------|------|---------|
| **API 响应时间** | <5 秒（P95） | 性能监控 |
| **API Key 认证成功率** | >99.9% | 日志分析 |
| **速率限制准确性** | 100% | 单元测试 |
| **批量查询吞吐量** | >10 查询/秒 | 压力测试 |
| **Skills 兼容性** | 100% 符合 Claude Skills 规范 | 集成测试 |

---

## 11. 风险与应对

### 11.1 技术风险

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| **Claude Agent SDK 学习曲线** | 延期 1-2 周 | 提前学习官方文档和示例 |
| **自动分类准确率不达标** | 用户体验差 | 降级为半自动（Agent 建议 + 人工确认） |
| **Token 消耗过高** | 成本高 | 优化 Prompt、缓存结果 |
| **WebSocket 稳定性** | 实时性差 | 降级为轮询 |

### 11.2 产品风险

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| **用户不习惯自然语言** | 使用率低 | 提供示例查询、引导教程 |
| **Agent 决策不透明** | 信任度低 | 显示 Agent 决策过程 |
| **文档处理速度慢** | 用户流失 | 两阶段生成（快速 + 完整） |

---

## 12. 后续版本规划

### V1.5（+1 个月）
- ✅ 多文档联合检索（跨文档分析）
- ✅ 用户权限管理（多租户）
- ✅ 高级 Agent 功能（对比分析、趋势预测）

### V2.0（+3 个月）
- ✅ 分布式部署（负载均衡）
- ✅ 向量数据库集成（更快检索）
- ✅ 多模态支持（图片、表格、公式）

---

## 13. 附录

### 13.1 参考资料

- **Claude Agent SDK**: https://github.com/anthropics/anthropic-sdk-python
- **Claude Skills**: https://github.com/anthropics/skills
- **DeepSeek OCR API**: 内部文档
- **Vue 3 官方文档**: https://vuejs.org/
- **Element Plus**: https://element-plus.org/

### 13.2 术语表

| 术语 | 定义 |
|------|------|
| **Agent-First** | 以 Agent 为中心的软件设计理念，用户只需自然语言交互 |
| **4 层检索** | 图书馆 → 分类 → 文档 → 页面的渐进式检索架构 |
| **自动分类** | Agent 基于文档名称和内容自动识别文档类型 |
| **置信度** | Agent 对当前结果的信心程度（0-1） |
| **Agent Loop** | Agent 动态决策的循环过程（分析 → 行动 → 评估 → 重复） |

---

**PRD 版本**: v1.0 Agent-First
**最后更新**: 2025-01-15
**状态**: ✅ 准备开发

