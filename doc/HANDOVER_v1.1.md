# DKR Agent 交接文档 v1.1

**交接日期**: 2025-11-10
**当前版本**: v1.1
**GitHub 仓库**: https://github.com/sga-jerrylin/DKR-SGA
**Release**: v1.0 (BM25S版本) / v1.1 (DeepSeek版本)
**交接给**: 下一个 Agent（负责 Docker 封装 + 提示词优化）

---

## 📋 快速导航

1. [项目概述](#1-项目概述)
2. [当前架构](#2-当前架构)
3. [已完成工作](#3-已完成工作)
4. [待完成任务](#4-待完成任务)
5. [环境配置](#5-环境配置)
6. [关键文件](#6-关键文件)
7. [已知问题](#7-已知问题)
8. [优化建议](#8-优化建议)

---

## 1. 项目概述

### 1.1 项目名称
**DKR (Deep Knowledge Retrieval) Agent v1.1**

### 1.2 核心功能
基于 DeepSeek OCR 的智能文档检索系统，采用"目录式检索"策略，模拟人类在图书馆查找资料的过程。

### 1.3 技术栈
- **后端**: Python 3.11+ / FastAPI / LangGraph
- **LLM**: DeepSeek Chat (via DeepSeek API)
- **OCR**: DeepSeek OCR API (自建服务 http://111.230.37.43:5010)
- **前端**: (待开发)

### 1.4 核心特性
- **无状态 Agent**: 每次对话独立，适合外部 Agent 编排
- **目录式检索**: Library → TOC → Pages → Full Text
- **深度分析**: 4 层分析框架（描述性、诊断性、预测性、处方性）
- **防幻觉**: 严格基于文档内容回答，引用具体页码

---

## 2. 当前架构

### 2.1 系统架构

```
External Agent (上下文 + 记忆)
    ↓ HTTP API
DKR Agent (无状态)
    ├─ LangGraph Agent (DeepSeek Chat)
    │   ├─ System Prompt: 林溪源人设
    │   ├─ "5个为什么"追问法
    │   └─ 4层分析框架
    └─ 5 Tools
        ├─ get_library_catalog
        ├─ get_documents_table_of_contents
        ├─ get_pages_full_summary
        ├─ search_in_document (全量 OCR)
        └─ evaluate_answer_confidence
    ↓
Data Layer
    ├─ library_index.json (文档库索引)
    ├─ summaries/*.json (Rich Summary)
    ├─ documents/*.pdf (原始文档)
    └─ videos/*.mp4 (视频文件)
```

### 2.2 检索流程

```
用户查询
  ↓
Step 1: get_library_catalog() → 查看所有文档
  ↓
Step 2: get_documents_table_of_contents() → 查看目录（page_summary）
  ↓
Step 3: get_pages_full_summary() → 查看详细信息（entities, key_data）
  ↓
Step 4: (可选) search_in_document() → 全量 OCR
  ↓
Step 5: 生成答案（Level 1-4 分析）
```

---

## 3. 已完成工作

### 3.1 v1.0 (BM25S 版本) - Tag: v1.0
- ✅ BM25S 检索引擎
- ✅ Rich Summary 生成
- ✅ 6 个工具
- ✅ 基础 Agent 实现

### 3.2 v1.1 (当前版本) - Tag: v1.1
- ✅ 切换到 DeepSeek Chat 模型（解决 Gemini 死循环）
- ✅ 重构工具系统（6 → 5 工具）
- ✅ 目录式检索策略
- ✅ 林溪源人设 + "5个为什么" + 4层分析框架
- ✅ 移除记忆功能（无状态）
- ✅ 防幻觉措施
- ✅ Bug 修复（页码类型、chart_info 列表）
- ✅ 安全性（移除 API Key）

---

## 4. 待完成任务

### 4.1 优先级 P0（必须完成）

#### 4.1.1 Docker 封装

**目标**: 将整个系统 Docker 化

**任务清单**:
1. 编写 `Dockerfile`
   - 基础镜像: `python:3.11-slim`
   - 安装依赖: `requirements.txt`
   - 暴露端口: `8000`

2. 编写 `docker-compose.yml`
   - 服务: `dkr-backend` (FastAPI)
   - 环境变量: 通过 `.env` 注入
   - Volume: `./data`, `./logs`

3. 测试
   - `docker-compose up -d`
   - 访问 `http://localhost:8000/docs`
   - 测试查询 `POST /agent/ask`

**参考**: `backend/requirements.txt`

---

#### 4.1.2 提示词优化

**目标**: 提高回答质量和效率

**当前问题**:
1. Summary 数据过于详细 → Agent 不需要 OCR
2. OCR 工具使用率低
3. 回答可能过于冗长

**优化方向**:
1. 调整 Summary 粒度（可选）
   - `entities`: 只保留前 10 个
   - `key_data`: 只保留前 5 个
   - `table_info`: 只提供结构
   - `chart_info`: 只提供类型

2. 优化 System Prompt
   - 增加"第 6 层追问：是否需要查看原文"
   - 明确 OCR 触发条件

3. 测试不同查询类型
   - 简单: "福建有多少家组织？"
   - 复杂: "福建的组织机构在2022年的表现"
   - 深度: "福建的组织机构详细名单和收入"

**关键文件**:
- `backend/prompts/agent_system_prompt.txt`
- `backend/prompts/summary_generation_prompt.txt`

---

### 4.2 优先级 P1（建议完成）

#### 4.2.1 性能优化
1. **并发处理**: 支持多个查询并发
2. **缓存机制**: 缓存 LLM 响应
3. **OCR 成本优化**: 监控调用次数

#### 4.2.2 监控和日志
1. **结构化日志**: 添加 trace_id
2. **性能监控**: 记录工具调用时间
3. **错误追踪**: 集成 Sentry

---

## 5. 环境配置

### 5.1 环境变量

复制 `backend/.env.example` 到 `backend/.env`，填入：

```bash
# DeepSeek API
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# DeepSeek OCR API
DEEPSEEK_OCR_URL=http://111.230.37.43:5010

# OpenRouter API (for Gemini)
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

**⚠️ 重要**: API Key 已从代码中移除，保存在 `KEYS_BACKUP.txt`（本地文件，不在 Git 中）

### 5.2 本地运行

```bash
# 1. 安装依赖
cd backend
pip install -r requirements.txt

# 2. 启动后端
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 3. 测试
python ../test_agent.py
```

### 5.3 API 文档

启动后访问: `http://localhost:8000/docs`

---

## 6. 关键文件

### 6.1 核心代码

| 文件 | 说明 |
|------|------|
| `backend/main.py` | FastAPI 入口 |
| `backend/app/agent/dkr_agent.py` | DKR Agent 核心逻辑 |
| `backend/app/api/agent.py` | Agent API 端点 |
| `backend/app/config.py` | 配置管理 |
| `backend/app/core/document_processor.py` | 文档处理 |

### 6.2 提示词

| 文件 | 说明 |
|------|------|
| `backend/prompts/agent_system_prompt.txt` | Agent System Prompt |
| `backend/prompts/summary_generation_prompt.txt` | Summary 生成 |
| `backend/prompts/summary_rich_json.txt` | Rich Summary 结构 |

### 6.3 数据文件

| 文件 | 说明 |
|------|------|
| `backend/data/library_index.json` | 文档库索引 |
| `backend/data/summaries/*/summaries.json` | Rich Summary |
| `backend/data/documents/*.pdf` | 原始 PDF |
| `backend/data/videos/*.mp4` | 视频文件 |

---

## 7. 已知问题

### 7.1 Summary 数据过于详细
**问题**: Agent 不需要 OCR 就能获取所有信息

**影响**:
- OCR 成本浪费
- Agent 缺乏"深挖"动力

**解决方案**: 见 [4.1.2 提示词优化](#412-提示词优化)

### 7.2 无前端界面
**问题**: 当前只有 API

**影响**: 用户体验不佳

**解决方案**: 开发 Web 前端（优先级 P2）

---

## 8. 优化建议

### 8.1 提示词优化策略

#### 策略 1: 调整 Summary 粒度（推荐）
**思路**: 让 Summary 只提供"线索"，而不是"答案"

**具体做法**:
1. 修改 `backend/prompts/summary_generation_prompt.txt`
2. 限制 `entities`、`key_data` 数量
3. `table_info`、`chart_info` 只提供结构

**效果**:
- Agent 看到"福建有 108 家组织"（Summary）
- 但看不到具体名单（需要 OCR）
- 必须调用 `search_in_document`

#### 策略 2: 优化 System Prompt（推荐）
**思路**: 增加 OCR 触发条件

**具体做法**:
在 Step 6（"5个为什么"）中，增加：

```
**第 6 层追问：是否需要查看原文**
- 如果用户要求"详细名单"、"完整数据" → 必须调用 search_in_document
- 如果 Summary 显示"...（还有 X 个）" → 必须调用 search_in_document
- 如果需要验证数据准确性 → 必须调用 search_in_document
```

#### 策略 3: 混合策略（最推荐）
结合策略 1 和策略 2

---

### 8.2 Docker 优化建议

1. **多阶段构建**: 减小镜像体积
2. **健康检查**: 添加 `HEALTHCHECK`
3. **日志管理**: 集成 ELK 或 Loki

---

### 8.3 测试建议

1. **单元测试**: 测试每个工具
2. **集成测试**: 测试完整查询流程
3. **性能测试**: 测试并发查询

---

## 9. 恢复 API Keys

推送到 GitHub 后，从 `KEYS_BACKUP.txt` 恢复 API Keys：

```bash
# 1. 查看备份
cat KEYS_BACKUP.txt

# 2. 手动恢复到以下文件：
# - backend/app/config.py (Line 23)
# - backend/.env (Line 2, 7)

# 3. 删除备份文件
rm KEYS_BACKUP.txt
```

---

## 10. 版本历史

| 版本 | 日期 | Tag | 主要变更 |
|------|------|-----|---------|
| v1.0 | 2025-11-09 | v1.0 | BM25S 版本 |
| v1.1 | 2025-11-10 | v1.1 | DeepSeek + 目录式检索 + 林溪源人设 |

---

## 11. 联系方式

- **GitHub**: https://github.com/sga-jerrylin/DKR-SGA
- **Issues**: https://github.com/sga-jerrylin/DKR-SGA/issues

---

**祝工作顺利！🎉**

   - `table_info`: 只提供结构
   - `chart_info`: 只提供类型

2. 优化 System Prompt
   - 增加"第 6 层追问：是否需要查看原文"
   - 明确 OCR 触发条件

3. 测试不同查询类型
   - 简单: "福建有多少家组织？"
   - 复杂: "福建的组织机构在2022年的表现"
   - 深度: "福建的组织机构详细名单和收入"

**关键文件**:
- `backend/prompts/agent_system_prompt.txt`
- `backend/prompts/summary_generation_prompt.txt`

---


