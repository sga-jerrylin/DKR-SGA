# Minimax API 调用规则

本文档定义了与 Minimax 开放平台 API 交互的规则和最佳实践，涵盖文本、语音、视频、图像、文件管理等核心功能。

## 目录

- [通用规则](#通用规则)
- [文本生成 (ChatCompletion)](#文本生成-chatcompletion)
- [批量处理 (Batch)](#批量处理-batch)
- [语音合成](#语音合成)
  - [同步语音合成 (T2A)](#同步语音合成-t2a)
  - [异步长文本语音合成 (T2A Async)](#异步长文本语音合成-t2a-async)
  - [快速复刻 (Voice Cloning)](#快速复刻-voice-cloning)
  - [音色设计 (Voice Design)](#音色设计-voice-design)
  - [声音管理](#声音管理)
- [视频生成](#视频生成)
  - [视频生成](#视频生成-1)
  - [视频生成 Agent](#视频生成-agent)
- [音乐生成](#音乐生成)
- [图像生成](#图像生成)
- [文件管理](#文件管理)
- [错误码查询](#错误码查询)

---

## 通用规则

- **认证 (Authentication)**：所有 API 请求都必须在 HTTP Header 中包含 `Authorization: Bearer {API_KEY}`。
- **内容类型 (Content-Type)**：所有 POST 请求，Content-Type 应为 `application/json`。
- **分组ID (GroupId)**：部分接口需在 URL 参数中携带 GroupId，请使用平台发放的专属值。
- **回调 (Callback)**：部分异步接口支持 `callback_url`。服务器会向该 URL 发送 POST 请求进行校验和结果通知。校验时需在3秒内返回请求体中的 `challenge` 字段。

---

## 文本生成 (ChatCompletion)

此 API 支持标准对话能力和 tools 调用能力。

- **接口地址**：`POST https://api.minimaxi.com/v1/text/chatcompletion_v2`

### 核心模型

- `MiniMax-M1`：推理模型，建议使用流式输出。
- `MiniMax-Text-01`：支持结构化输出。

### 关键参数

- `model` (string, 必填)：模型 ID。
- `messages` (array, 必填)：对话内容，遵循 `{role: "user/assistant/system", content: "..."}` 格式。
- `stream` (boolean, 可选)：是否流式返回，默认为 false。
- `tools` (array, 可选)：定义可供模型调用的工具列表。
- `tool_choice` (string, 可选)：控制工具调用模式 (none 或 auto)。
- `response_format` (object, 可选)：仅 MiniMax-Text-01 支持，用于指定 JSON Schema 实现结构化输出。

### SDK 接入

支持通过标准 OpenAI SDK 进行接入，需配置 `api_key` 和 `base_url` (`https://api.minimaxi.com/v1`)。

### 函数调用 (Function Calling)

- 在 `tools` 中定义函数 `name`, `description`, `parameters`。
- 设置 `tool_choice` 为 `auto`。
- 模型判断需要调用函数时，会在返回的 message 中包含 `tool_calls`。
- 将函数执行结果以 `role: "tool"` 的形式追加到 `messages` 中，再次请求模型，即可获得基于函数返回内容的总结性回复。

---

## 批量处理 (Batch)

适用于大批量、非实时的请求，如数据标注、舆情分析等。

### 工作流程

1. **准备批处理文件**：创建一个 `.jsonl` 文件，每行是一个独立的 API 请求 JSON 对象，必须包含 `custom_id` (唯一), `method` (POST), `url` (`/v1/text/chatcompletion_v2`) 和 `body`。
2. **上传文件**：使用文件上传接口上传该 `.jsonl` 文件，`purpose` 设置为 `batch`，获取 `file_id`。
3. **创建任务**：调用创建接口，提交 `input_file_id`。
4. **查询状态**：使用任务 id 轮询查询接口，或使用 `callback_url` 接收状态更新。
5. **获取结果**：任务完成后，从返回的 `output_file_id` 或 `error_file_id` 中获取结果文件ID，并通过文件下载接口下载。

### 核心接口

- 创建任务：`POST https://api.minimaxi.com/v1/batches`
- 查询任务：`GET https://api.minimaxi.com/v1/batches/{batch_id}`
- 取消任务：`POST https://api.minimaxi.com/v1/batches/{batch_id}/cancel`
- 列出任务：`GET https://api.minimaxi.com/v1/batches`

---

## 语音合成

### 同步语音合成 (T2A)

适用于短句生成、实时语音聊天等场景。

- **接口地址**：
  - HTTP: `POST https://api.minimaxi.com/v1/t2a_v2`
  - WebSocket: `wss://api.minimaxi.com/ws/v1/t2a_v2`
- **核心模型**：`speech-02-hd`, `speech-02-turbo` 等。

#### 关键参数

- `model` (string, 必填)：模型 ID。
- `text` (string, 必填)：待合成文本，可使用 `<#x#>` (x为秒数) 控制停顿。
- `voice_setting` (object, 必填)：包含 `voice_id`, `speed`, `vol`, `pitch`。
- `audio_setting` (object, 可选)：设置音频格式、采样率、比特率。
- `stream` (boolean, 可选)：是否使用流式传输。

#### WebSocket 流程

1. 建立连接。
2. 发送 `task_start` 事件并携带配置参数。
3. 收到 `task_started` 后，发送 `task_continue` 事件并携带文本。
4. 处理返回的音频数据。
5. 发送 `task_finish` 事件结束任务。

### 异步长文本语音合成 (T2A Async)

适用于书籍、长篇文章的语音生成。

#### 工作流程

1. **创建任务**：调用创建接口，通过 `text` 或 `text_file_id` (需先用文件上传接口上传) 提交文本，获取 `task_id`。
2. **查询状态**：使用 `task_id` 轮询查询接口。
3. **获取结果**：任务成功后，返回 `file_id`，通过文件下载接口下载音频及字幕文件。

#### 核心接口

- 创建任务：`POST https://api.minimaxi.com/v1/t2a_async_v2`
- 查询任务：`GET https://api.minimaxi.com/v1/query/t2a_async_query_v2`

### 快速复刻 (Voice Cloning)

通过上传音频文件，快速克隆音色。

#### 工作流程

1. **上传音频**：使用文件上传接口上传音频 (mp3, m4a, wav)，`purpose` 设为 `voice_clone`，获取 `file_id`。
2. **复刻音色**：调用复刻接口，传入 `file_id` 和自定义的 `voice_id`。

- **接口地址**：`POST https://api.minimaxi.com/v1/voice_clone`

> **注意**：复刻的音色为临时音色，168小时（7天）内需在T2A接口中调用一次（试听除外）方可永久保留。调用本接口不收费，在首次使用该复刻音色进行语音合成时收费。

### 音色设计 (Voice Design)

通过文本描述生成个性化音色。

- **接口地址**：`POST https://api.minimaxi.com/v1/voice_design`

#### 关键参数

- `prompt` (string, 必填)：音色描述。
- `preview_text` (string, 必填)：用于生成试听音频的文本。
- `voice_id` (string, 可选)：自定义音色ID。

> **注意**：生成的音色为临时音色，规则同快速复刻。

### 声音管理

- 删除声音：`POST https://api.minimaxi.com/v1/delete_voice`
  - 参数：`voice_type` (`voice_cloning`/`voice_generation`), `voice_id`。
- 查询可用声音ID：`POST https://api.minimaxi.com/v1/get_voice`
  - 参数：`voice_type` (`system`/`voice_cloning`/`voice_generation`/`music_generation`/`all`)。

---

## 视频生成

### 视频生成

通过文本或图片生成视频。

#### 工作流程

1. **创建任务**：调用创建接口，提交 `prompt` 等参数，获取 `task_id`。
2. **查询状态**：使用 `task_id` 轮询查询接口。
3. **获取结果**：任务成功后，返回 `file_id`，通过文件下载接口下载视频。

#### 核心接口

- 创建任务：`POST https://api.minimaxi.com/v1/video_generation`
- 查询任务：`GET https://api.minimaxi.com/v1/query/video_generation`

#### 关键参数

- `model` (string, 必填)：如 `MiniMax-Hailuo-02`。
- `prompt` (string, 必填)：视频描述，支持运镜指令，如 `[左移,推进]`。
- `first_frame_image` (string, 可选)：图生视频的参考图 (Base64或URL)。
- `duration` (int, 可选)：视频时长（秒）。
- `resolution` (string, 可选)：分辨率 (`768P`, `1080P`)。

### 视频生成 Agent

使用预设模板进行视频生成。

#### 工作流程

1. **创建任务**：调用创建接口，选择 `template_id` 并提供 `media_inputs` (图片) 或 `text_inputs` (文本)，获取 `task_id`。
2. **查询状态**：使用 `task_id` 轮询查询接口。
3. **获取结果**：任务成功后，直接返回视频的 `video_url`。

#### 核心接口

- 创建任务：`POST https://api.minimaxi.com/v1/video_template_generation`
- 查询任务：`GET https://api.minimaxi.com/v1/query/video_template_generation`

---

## 音乐生成

根据灵感和歌词生成音乐。

- **接口地址**：`POST https://api.minimaxi.com/v1/music_generation`
- **核心模型**：`music-1.5`

### 关键参数

- `prompt` (string, 必填)：音乐灵感描述（风格、情绪等）。
- `lyrics` (string, 必填)：歌词，用 `\n` 分隔，支持 `[Intro]`, `[Verse]` 等结构标签。
- `audio_setting` (object, 可选)：设置音频格式等。
- `output_format` (string, 可选)：返回格式 (`hex` 或 `url`)。

---

## 图像生成

根据文本或图片生成创意图像。

- **接口地址**：`POST https://api.minimaxi.com/v1/image_generation`
- **核心模型**：`image-01`, `image-01-live`

### 关键参数

- `prompt` (string, 必填)：图像描述。
- `subject_reference` (array, 可选)：图生图的参考图。
- `aspect_ratio` (string, 可选)：宽高比，如 `16:9`。
- `width` / `height` (int, 可选)：自定义宽高像素。
- `response_format` (string, 可选)：返回格式 (`url` 或 `base64`)。
- `n` (int, 可选)：生成图片数量。

---

## 文件管理

用于配合其他接口进行文件上传、下载和管理。

- 上传：`POST https://api.minimaxi.com/v1/files/upload`
  - 参数：`purpose` (string, 必填，如 `retrieval`, `batch`, `voice_clone`), `file` (file, 必填)。
- 列出：`GET https://api.minimaxi.com/v1/files/list`
- 检索：`GET https://api.minimaxi.com/v1/files/retrieve`
  - 参数：`file_id`。
- 删除：`POST https://api.minimaxi.com/v1/files/delete`
  - 参数：`file_id`。
- 下载：`GET https://api.minimaxi.com/v1/files/retrieve_content`
  - 参数：`file_id`。

---

## 错误码查询

| 错误码 | 含义                   | 解决方法                                 |
|--------|------------------------|------------------------------------------|
| 1000   | 未知错误/系统默认错误  | 请稍后再试                               |
| 1002   | 请求频率超限           | 请稍后再试或降低请求频率                 |
| 1004   | 未授权/Token不匹配     | 请检查您的 API Key 是否正确              |
| 1008   | 余额不足               | 请检查您的账户余额                       |
| 1026   | 输入内容涉敏           | 请调整输入内容                           |
| 1027   | 输出内容涉敏           | 请调整输入内容                           |
| 1039   | Token限制              | 请调整 max_tokens 参数或缩短输入         |
| 2013   | 参数错误               | 请检查请求参数是否符合文档规范           |
| 2037   | 语音时长不符合要求     | 语音克隆文件时长应在10秒到5分钟之间      |
| 2038   | 用户语音克隆功能被禁用 | 请完成账户身份认证                       |
| 2039   | 语音克隆voice_id重复   | 请修改 voice_id，确保其唯一性            |
| 2042   | 无权访问该voice_id     | 请确认是否为该 voice_id 的创建者         |
| 2049   | 无效的API Key          | 请检查API Key                            |