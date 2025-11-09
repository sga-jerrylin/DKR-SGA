"""
应用配置管理
"""
import os
from pathlib import Path
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """应用配置"""

    # DeepSeek Chat API
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # OpenRouter API (for Gemini and other models)
    openrouter_api_key: str = "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"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Agent LLM Configuration
    agent_llm_provider: str = "gemini"  # "deepseek" or "gemini"
    agent_llm_model: str = "google/gemini-2.5-flash-preview-09-2025"  # Gemini model via OpenRouter

    # DeepSeek OCR API
    ocr_api_url: str = "http://111.230.37.43:5010"
    ocr_timeout: int = 300

    # Application
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    backend_reload: bool = True

    # Data Storage - 统一数据目录结构
    data_dir: Path = Path("./data")
    documents_dir: Path = Path("./data/documents")  # PDF原文件
    videos_dir: Path = Path("./data/videos")        # MP4视频
    summaries_dir: Path = Path("./data/summaries")  # Summary JSON
    indexes_dir: Path = Path("./data/indexes")      # 索引文件
    temp_dir: Path = Path("./data/temp")            # 临时文件
    cache_dir: Path = Path("./data/cache")          # OCR缓存

    # Agent Configuration
    agent_max_iterations: int = 10
    agent_confidence_threshold: float = 0.9

    # Document Classification (DKR 1.0 固定分类)
    default_categories: str = "年度调研报告,申请书,中期报告,结项报告,其他"

    # Logging
    log_level: str = "INFO"
    log_file: str = "./logs/dkr.log"

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:3001,http://localhost:5173"

    # External Agent API
    enable_api_key_auth: bool = False
    api_keys: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )

    def get_categories_list(self) -> List[str]:
        """获取分类列表"""
        return [c.strip() for c in self.default_categories.split(",") if c.strip()]

    def get_cors_origins_list(self) -> List[str]:
        """获取 CORS 源列表"""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def get_api_keys_list(self) -> List[str]:
        """获取 API Keys 列表"""
        return [k.strip() for k in self.api_keys.split(",") if k.strip()]


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例"""
    return settings

