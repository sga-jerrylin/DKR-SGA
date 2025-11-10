"""
应用配置管理

配置规范请参考: PROJECT_RULES.md
"""
import os
from pathlib import Path
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# 加载根目录的 .env 文件
project_root = Path(__file__).parent.parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    """
    应用配置

    配置规范请参考: PROJECT_RULES.md
    """

    # ==================== DeepSeek 官方 API ====================
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # ==================== OpenRouter API ====================
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # ==================== 预留：Kimi API ====================
    kimi_api_key: str = ""
    kimi_base_url: str = "https://api.moonshot.cn/v1"

    # ==================== 预留：MiniMax API ====================
    minimax_api_key: str = ""
    minimax_base_url: str = "https://api.minimax.chat/v1"

    # ==================== 分类模型配置 ====================
    classification_model_provider: str = "deepseek"  # deepseek, gemini
    classification_model_name: str = "deepseek-chat"

    # ==================== Summary 模型配置 ====================
    summary_model_provider: str = "gemini"  # gemini, qwen
    summary_model_name: str = "google/gemini-2.5-flash-preview-09-2025"

    # ==================== Agent 模型配置 ====================
    agent_llm_provider: str = "deepseek"  # deepseek, claude, gpt4, kimi, minimax
    agent_llm_model: str = "deepseek-chat"  # deepseek-chat, anthropic/claude-haiku-4.5, openai/gpt-4.1

    # ==================== OCR 模型配置 ====================
    ocr_model_provider: str = "deepseek_ocr"  # deepseek_ocr, paddle_ocr, gemini_flash, qwen_vl
    ocr_api_url: str = ""
    ocr_timeout: int = 300
    paddle_ocr_model_path: str = ""  # 预留：PaddleOCR 模型路径

    # ==================== 应用配置 ====================
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    backend_reload: bool = True

    # ==================== 数据存储路径 ====================
    # 所有路径都指向根目录的 data 文件夹
    @property
    def _project_root(self) -> Path:
        """获取项目根目录的绝对路径"""
        # config.py 在 backend/app/ 目录下，所以需要向上三级到达项目根目录
        return Path(__file__).parent.parent.parent

    @property
    def data_dir(self) -> Path:
        """数据根目录"""
        return self._project_root / "data"

    @property
    def documents_dir(self) -> Path:
        """PDF 文档目录"""
        return self.data_dir / "documents"

    @property
    def videos_dir(self) -> Path:
        """视频文件目录"""
        return self.data_dir / "videos"

    @property
    def summaries_dir(self) -> Path:
        """摘要文件目录"""
        return self.data_dir / "summaries"

    @property
    def indexes_dir(self) -> Path:
        """索引文件目录"""
        return self.data_dir / "indexes"

    @property
    def cache_dir(self) -> Path:
        """缓存目录"""
        return self.data_dir / "cache"

    @property
    def temp_dir(self) -> Path:
        """临时文件目录"""
        return self.data_dir / "temp"

    # ==================== Agent 配置 ====================
    agent_max_iterations: int = 10
    agent_confidence_threshold: float = 0.9

    # ==================== 文档分类 ====================
    default_categories: str = "年度调研报告,申请书,中期报告,结项报告,其他"

    # ==================== 日志配置 ====================
    log_level: str = "INFO"
    log_file: str = "./logs/dkr.log"

    # ==================== CORS 配置 ====================
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # ==================== 外部 Agent API ====================
    enable_api_key_auth: bool = False
    api_keys: str = ""

    model_config = SettingsConfigDict(
        env_file=str(project_root / ".env"),  # 使用根目录的 .env
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

