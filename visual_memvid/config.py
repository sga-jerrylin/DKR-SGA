"""
Configuration for Visual-Memvid
"""

CONFIG = {
    # PDF rendering settings
    "pdf": {
        "dpi": 400,  # 渲染分辨率（400 DPI 极致清晰度，确保 OCR 准确性）
        "color_space": "RGB",
    },

    # Video encoding settings (优化：平衡质量和压缩率)
    "video": {
        "codec": "h265",  # h265 压缩率最好
        "fps": 30,
        "crf": 20,  # 质量参数 (20 是高质量，接近无损)
        "preset": "slower",  # 编码速度（slower 提供更好的压缩率）
        "file_type": "mkv",
        # H.265 静态图像优化参数（参考 Memvid）
        "tune": "stillimage",  # 针对静态图像优化
        "extra_params": "keyint=1:no-scenecut:strong-intra-smoothing",
    },

    # OCR settings - 全页OCR（Layer 3）
    "ocr": {
        "provider": "deepseek_ocr",  # deepseek_ocr, gemini, openrouter, dify
        "endpoint": "http://111.230.37.43:5010",  # DeepSeek OCR 服务地址
        "batch_size": 5,  # 批量处理大小
        "prompt_file": "prompts/full_page_ocr_markdown.txt",  # 提示词文件路径
        "base_size": 4096,  # 极限配置：4096 支持超高分辨率图像
        "image_size": 2048,  # 极限配置：2048 保持最多细节
        "crop_mode": True,
    },
    
    # Retrieval settings
    "retrieval": {
        "context_window": 1,  # 前后页窗口（1 = 前后各 1 页）
        "top_k": 3,  # 返回最相关的 K 个结果
        "max_workers": 4,  # 并行处理线程数
    },
    
    # Index settings
    "index": {
        "min_keyword_length": 3,  # 最小关键词长度
        "max_keywords_per_page": 20,  # 每页最多关键词数
    },
    
    # LLM settings (for smart retrieval)
    "llm": {
        "provider": "openai",  # openai, anthropic, deepseek
        "model": "gpt-4o-mini",  # 或 deepseek-chat
        "temperature": 0.1,
        "max_tokens": 1000,
    },

    # Doris 4.0 settings
    "doris": {
        "host": "localhost",
        "port": 9030,
        "user": "root",
        "password": "",
        "database": "visual_memvid",
        "enabled": False,  # 是否启用 Doris（默认关闭，使用轻量级索引）
    },

    # Summary generation settings - Summary生成（Layer 2）
    "summary": {
        "provider": "gemini",  # gemini, qwen, grok, deepseek_chat, openrouter, dify
        "model": "google/gemini-2.5-flash-preview-09-2025",  # Grok-4-Fast 模型（可选：google/gemini-2.5-flash-preview-09-2025, qwen/qwen3-vl-235b-a22b-instruct）
        "prompt_file": "prompts/summary_rich_json.txt",  # 提示词文件路径
        "enabled": True,  # 是否生成 Summary
    },

    # AI Agent settings - 总调度智能体（LangGraph）
    "agent": {
        "provider": "deepseek_chat",  # deepseek_chat, openrouter, dify
        "model": "deepseek-chat",  # 模型名称
        "temperature": 0.1,
        "max_tokens": 4000,
    },

    # API Keys configuration
    "api_keys": {
        "deepseek": "",  # DeepSeek 官方 API Key
        "openrouter": "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",  # OpenRouter API Key
        "dify": "",  # Dify API Key
    },
}


def get_config():
    """Get configuration dictionary"""
    return CONFIG


def update_config(updates: dict):
    """Update configuration with custom values"""
    def deep_update(d, u):
        for k, v in u.items():
            if isinstance(v, dict):
                d[k] = deep_update(d.get(k, {}), v)
            else:
                d[k] = v
        return d
    
    deep_update(CONFIG, updates)

