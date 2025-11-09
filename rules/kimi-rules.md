## Kimi API 调用规则与最佳实践 (V1.0)

### 第一部分：核心概念与认证

#### 1.1 服务地址
所有 API 请求的基础 URL 是：
`https://api.moonshot.cn/v1`

#### 1.2 认证
所有请求都必须通过 HTTP Header 进行认证。您需要在 Header 中包含您的 API Key。

  * **Header:** `Authorization: Bearer $MOONSHOT_API_KEY`
  * 请将 `$MOONSHOT_API_KEY` 替换为您在 Moonshot AI 平台创建的 API Key。

#### 1.3 SDK 兼容性
Kimi API 兼容 OpenAI SDK（版本 >= 1.0.0）。您可以使用 OpenAI 官方的 Python 或 Node.js SDK 进行交互。

  * **Python 安装:** `pip install --upgrade 'openai>=1.0'`
  * **Node.js:** 版本需 >= 18

### 第二部分：核心对话功能 (Chat Completion)

#### 2.1 请求地址
  * `POST /v1/chat/completions`

#### 2.2 请求体核心参数

| 字段 | 是否必须 | 类型 | 说明与建议 |
| :--- | :--- | :--- | :--- |
| `model` | 是 | `string` | 模型 ID。可选值包括 `kimi-k2-0711-preview`, `moonshot-v1-8k`, `moonshot-v1-32k`, `moonshot-v1-128k`, `moonshot-v1-auto` 等。 |
| `messages` | 是 | `List[Dict]` | 对话历史列表。每个元素包含 `role` (`system`, `user`, `assistant`) 和 `content`。 |
| `temperature` | 否 | `float` | 采样温度，介于 0 和 1 之间。推荐值为 0.3，`kimi-k2-0711-preview` 模型建议为 0.6。 |
| `max_tokens`| 否 | `int` | 生成回复的最大 token 数。请注意，这个值是**输出**的最大长度，不是输入+输出的总和。需要确保 `输入token` + `max_tokens` <= 模型上下文总长度。 |
| `stream` | 否 | `bool` | 是否流式返回。默认为 `false`。设置为 `true` 可实现实时返回。 |
| `tools` | 否 | `List[Dict]`| 可供模型调用的工具列表。详见 **第三部分：工具调用**。 |
| `response_format`| 否 | `object` | 设置为 `{"type": "json_object"}` 可启用 JSON 模式，确保输出为有效 JSON。 |

#### 2.3 多轮对话
要实现多轮对话，只需将之前的对话历史（包括用户的提问和模型的回答）完整地加入到 `messages` 列表中再次请求即可。随着对话轮次增加，token 会线性增长，必要时需采取策略（如只保留最近N轮）进行优化。

#### 2.4 Vision (视觉模型)
使用视觉模型（如 `moonshot-v1-8k-vision-preview`）时，`messages` 中 `user`角色的 `content` 字段需要是一个列表，包含图片和文本对象。

  * **图片对象:** `{"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,{base64_encoded_image}"}}`
  * **文本对象:** `{"type": "text", "text": "请描述这张图片"}`

### 第三部分：工具调用 (Tool Use / Function Calling)

#### 3.1 启用方式
在 `POST /v1/chat/completions` 请求中，增加 `tools` 参数，它是一个工具列表。

#### 3.2 `tools` 参数结构
每个工具的结构如下：

```
{
  "type": "function",
  "function": {
    "name": "CodeRunner",
    "description": "代码执行器，支持运行 python 和 javascript 代码",
    "parameters": {
      "type": "object",
      "properties": {
        "language": {
          "type": "string",
          "enum": ["python", "javascript"]
        },
        "code": {
          "type": "string",
          "description": "代码写在这里"
        }
      }
    }
  }
}
```

  * `name`: 函数名，必须符合 `^[a-zA-Z_][a-zA-Z0-9-_]{1,63}$` 的正则表达式规范。
  * `description`: 功能描述，帮助模型理解何时调用该工具。
  * `parameters`: 函数的参数，使用 JSON Schema 的子集来定义。

#### 3.3 模型返回
当模型决定调用工具时，返回的 `assistant` 消息中会包含 `tool_calls` 字段，其中包含了要调用的函数名和参数。

### 第四部分：文件接口 (文件问答)

#### 4.1 核心流程
1.  **上传文件:** 将文件上传到 Moonshot 服务器，获取文件 ID。
2.  **获取内容:** 使用文件 ID 获取抽取后的文件内容。
3.  **发起对话:** 将文件内容作为一个 `role` 为 `system` 的 `message`，连同你的问题一起发送给 Chat Completion API。

#### 4.2 API 列表
  * `POST /v1/files`: 上传文件。`purpose` 参数当前仅支持 `"file-extract"`。
  * `GET /v1/files`: 列出所有已上传的文件。
  * `GET /v1/files/{file_id}`: 获取指定文件的元信息（如状态、大小等）。
  * `DELETE /v1/files/{file_id}`: 删除指定文件。
  * `GET /v1/files/{file_id}/content`: 获取文件抽取后的内容。

#### 4.3 使用限制
  * 单个用户最多上传 1000 个文件。
  * 单文件大小不超过 100MB。
  * 所有文件总大小不超过 10G。

### 第五部分：上下文缓存 (Context Caching)

#### 5.1 目的
对于需要重复使用的长文本（如多个文件内容），通过上下文缓存可以显著降低 token 消耗和成本，并提升响应速度。

#### 5.2 API 列表
  * `POST /v1/caching`: 创建一个缓存。需要提供 `model` (模型组，如 `moonshot-v1`) 和 `messages`。
  * `GET /v1/caching`: 列出已创建的缓存。
  * `DELETE /v1/caching/{cache-id}`: 删除指定缓存。
  * `POST /v1/caching/refs/tags`: 为一个 `cache_id` 创建一个固定的标签（Tag）。
  * `GET /v1/caching/refs/tags/{your_tag_name}`: 获取标签信息。

#### 5.3 使用方式
在调用 `POST /v1/chat/completions` 时，将一个特殊的 `message` 放在 `messages` 列表的**首位**：

  * **通过 Cache ID:**
    ```json
    {
      "role": "cache",
      "content": "cache_id={id};reset_ttl=300"
    }
    ```
  * **通过 Tag:**
    ```json
    {
      "role": "cache",
      "content": "tag={tag_name};reset_ttl=300"
    }
    ```
  * `reset_ttl`: 可选参数，每次请求成功时，都会将缓存的有效期重置为指定秒数。

### 第六部分：其它接口
  * **计算 Token:** `POST /v1/tokenizers/estimate-token-count` - 用于精确计算 `messages` 列表的 token 数量。
  * **查询余额:** `GET /v1/users/me/balance` - 查询账户的可用余额、代金券余额和现金余额。

### 第七部分：错误处理
API 会返回标准的 HTTP 状态码。常见的错误类型包括：

| 状态码 | 错误类型 (`error type`) | 描述 |
| :--- | :--- | :--- |
| `400` | `invalid_request_error` | 请求格式错误或参数无效。 |
| `401` | `invalid_authentication_error` | API Key 无效或未提供。 |
| `403` | `permission_denied_error` | 账户异常或无权限访问。 |
| `429` | `rate_limit_reached_error` | 达到速率限制（并发、RPM、TPM）。 |
| `429` | `exceeded_current_quota_error`| 账户额度不足。 |
