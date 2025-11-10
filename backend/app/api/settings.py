"""
系统设置 API
"""
from pathlib import Path
from typing import Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger

from app.config import get_settings

router = APIRouter(prefix="/settings", tags=["settings"])


class ModelSettings(BaseModel):
    """模型配置"""
    classifier_model: str           # 分类智能体模型
    summary_model: str              # 页面总结智能体模型
    agent_model: str                # DKR 主智能体模型
    ocr_model: str                  # OCR 智能体模型
    agent_max_iterations: int
    agent_confidence_threshold: float


@router.get("/models")
async def get_model_settings():
    """获取当前模型配置"""
    try:
        settings = get_settings()

        # 根据当前配置推断模型选择
        # 1. 分类模型
        if settings.classification_model_provider == "deepseek":
            classifier_model = "deepseek-chat"
        else:
            classifier_model = settings.classification_model_name

        # 2. Summary 模型
        summary_model = settings.summary_model_name

        # 3. Agent 模型
        agent_model = settings.agent_llm_model

        # 4. OCR 模型
        if settings.ocr_model_provider == "deepseek_ocr":
            ocr_model = "deepseek-ocr"
        elif settings.ocr_model_provider == "paddle_ocr":
            ocr_model = "paddle-ocr"
        elif settings.ocr_model_provider == "gemini_flash":
            ocr_model = "gemini-flash-ocr"
        elif settings.ocr_model_provider == "qwen_vl":
            ocr_model = "qwen-235b-vl-ocr"
        else:
            ocr_model = "deepseek-ocr"

        return {
            "success": True,
            "settings": {
                "classifier_model": classifier_model,
                "summary_model": summary_model,
                "agent_model": agent_model,
                "ocr_model": ocr_model,
                "agent_max_iterations": settings.agent_max_iterations,
                "agent_confidence_threshold": settings.agent_confidence_threshold
            }
        }
    except Exception as e:
        logger.error(f"获取模型配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models")
async def update_model_settings(model_settings: ModelSettings):
    """
    更新模型配置并持久化到 .env 文件
    """
    try:
        settings = get_settings()

        # 读取现有的 .env 文件
        env_path = settings._project_root / ".env"

        if not env_path.exists():
            raise HTTPException(status_code=500, detail=".env 文件不存在")

        # 读取所有行
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 准备要更新的配置
        keys_to_update = {}

        # 1. 分类模型
        if model_settings.classifier_model == "deepseek-chat":
            keys_to_update["CLASSIFICATION_MODEL_PROVIDER"] = "deepseek"
            keys_to_update["CLASSIFICATION_MODEL_NAME"] = "deepseek-chat"
        else:  # Gemini
            keys_to_update["CLASSIFICATION_MODEL_PROVIDER"] = "gemini"
            keys_to_update["CLASSIFICATION_MODEL_NAME"] = model_settings.classifier_model

        # 2. Summary 模型
        if "gemini" in model_settings.summary_model:
            keys_to_update["SUMMARY_MODEL_PROVIDER"] = "gemini"
        elif "qwen" in model_settings.summary_model:
            keys_to_update["SUMMARY_MODEL_PROVIDER"] = "qwen"
        keys_to_update["SUMMARY_MODEL_NAME"] = model_settings.summary_model

        # 3. Agent 模型
        if model_settings.agent_model == "deepseek-chat":
            keys_to_update["AGENT_LLM_PROVIDER"] = "deepseek"
        elif "claude" in model_settings.agent_model:
            keys_to_update["AGENT_LLM_PROVIDER"] = "claude"
        elif "gpt" in model_settings.agent_model:
            keys_to_update["AGENT_LLM_PROVIDER"] = "gpt4"
        elif "kimi" in model_settings.agent_model:
            keys_to_update["AGENT_LLM_PROVIDER"] = "kimi"
        elif "minimax" in model_settings.agent_model:
            keys_to_update["AGENT_LLM_PROVIDER"] = "minimax"
        keys_to_update["AGENT_LLM_MODEL"] = model_settings.agent_model

        # 4. OCR 模型
        if model_settings.ocr_model == "deepseek-ocr":
            keys_to_update["OCR_MODEL_PROVIDER"] = "deepseek_ocr"
        elif model_settings.ocr_model == "paddle-ocr":
            keys_to_update["OCR_MODEL_PROVIDER"] = "paddle_ocr"
        elif model_settings.ocr_model == "gemini-flash-ocr":
            keys_to_update["OCR_MODEL_PROVIDER"] = "gemini_flash"
        elif model_settings.ocr_model == "qwen-235b-vl-ocr":
            keys_to_update["OCR_MODEL_PROVIDER"] = "qwen_vl"

        # 5. Agent 参数
        keys_to_update["AGENT_MAX_ITERATIONS"] = str(model_settings.agent_max_iterations)
        keys_to_update["AGENT_CONFIDENCE_THRESHOLD"] = str(model_settings.agent_confidence_threshold)

        # 更新 .env 文件
        updated_lines = []
        keys_found = set()

        for line in lines:
            line_stripped = line.strip()

            # 跳过空行和注释
            if not line_stripped or line_stripped.startswith('#'):
                updated_lines.append(line)
                continue

            # 检查是否是要更新的键
            updated = False
            for key, value in keys_to_update.items():
                if line_stripped.startswith(f"{key}="):
                    updated_lines.append(f"{key}={value}\n")
                    keys_found.add(key)
                    updated = True
                    break

            if not updated:
                updated_lines.append(line)

        # 添加缺失的键
        for key, value in keys_to_update.items():
            if key not in keys_found:
                updated_lines.append(f"{key}={value}\n")

        # 写回文件
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(updated_lines)

        logger.info(f"模型配置已保存到 .env 文件")
        logger.info(f"分类模型: {model_settings.classifier_model}")
        logger.info(f"Summary 模型: {model_settings.summary_model}")
        logger.info(f"Agent 模型: {model_settings.agent_model}")
        logger.info(f"OCR 模型: {model_settings.ocr_model}")

        # 热加载配置：重新加载环境变量并更新 settings 实例
        try:
            from dotenv import load_dotenv
            import os

            # 重新加载 .env 文件
            load_dotenv(dotenv_path=env_path, override=True)

            # 更新 settings 实例
            settings.classification_model_provider = os.getenv("CLASSIFICATION_MODEL_PROVIDER", settings.classification_model_provider)
            settings.classification_model_name = os.getenv("CLASSIFICATION_MODEL_NAME", settings.classification_model_name)
            settings.summary_model_provider = os.getenv("SUMMARY_MODEL_PROVIDER", settings.summary_model_provider)
            settings.summary_model_name = os.getenv("SUMMARY_MODEL_NAME", settings.summary_model_name)
            settings.agent_llm_provider = os.getenv("AGENT_LLM_PROVIDER", settings.agent_llm_provider)
            settings.agent_llm_model = os.getenv("AGENT_LLM_MODEL", settings.agent_llm_model)
            settings.ocr_model_provider = os.getenv("OCR_MODEL_PROVIDER", settings.ocr_model_provider)
            settings.agent_max_iterations = int(os.getenv("AGENT_MAX_ITERATIONS", settings.agent_max_iterations))
            settings.agent_confidence_threshold = float(os.getenv("AGENT_CONFIDENCE_THRESHOLD", settings.agent_confidence_threshold))

            logger.info("✅ 配置已热加载，无需重启服务")

            # 重新初始化 DKR Agent（使其使用新配置）
            try:
                from app.api.agent import reset_agent
                reset_agent()
                logger.info("✅ DKR Agent 已重置，下次调用时将使用新配置")
            except Exception as agent_reset_error:
                logger.warning(f"重置 Agent 失败: {agent_reset_error}")

        except Exception as reload_error:
            logger.error(f"热加载配置失败: {reload_error}", exc_info=True)
            return {
                "success": True,
                "message": "配置已保存到文件，但热加载失败，请重启后端服务以应用新配置"
            }

        return {
            "success": True,
            "message": "配置已保存并立即生效，无需重启服务"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新模型配置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 提示词管理 ====================

class PromptUpdate(BaseModel):
    """提示词更新"""
    content: str


@router.get("/prompts")
async def get_prompts():
    """获取所有提示词文件"""
    try:
        # 提示词文件路径
        prompts_dir = Path(__file__).parent.parent.parent / "prompts"

        if not prompts_dir.exists():
            raise HTTPException(status_code=404, detail="提示词目录不存在")

        # 读取所有 .txt 文件
        prompts = {}
        for prompt_file in prompts_dir.glob("*.txt"):
            prompt_name = prompt_file.stem
            try:
                with open(prompt_file, "r", encoding="utf-8") as f:
                    prompts[prompt_name] = f.read()
            except Exception as e:
                logger.error(f"读取提示词文件失败 {prompt_file}: {e}")
                prompts[prompt_name] = f"读取失败: {str(e)}"

        return {
            "success": True,
            "prompts": prompts
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取提示词失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prompts/{prompt_name}")
async def update_prompt(prompt_name: str, prompt_update: PromptUpdate):
    """更新指定提示词文件"""
    try:
        # 提示词文件路径
        prompts_dir = Path(__file__).parent.parent.parent / "prompts"
        prompt_file = prompts_dir / f"{prompt_name}.txt"

        if not prompt_file.exists():
            raise HTTPException(status_code=404, detail=f"提示词文件 {prompt_name}.txt 不存在")

        # 备份原文件
        backup_file = prompts_dir / f"{prompt_name}.txt.backup"
        try:
            with open(prompt_file, "r", encoding="utf-8") as f:
                backup_content = f.read()
            with open(backup_file, "w", encoding="utf-8") as f:
                f.write(backup_content)
        except Exception as e:
            logger.warning(f"备份提示词文件失败: {e}")

        # 写入新内容
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write(prompt_update.content)

        logger.info(f"提示词文件已更新: {prompt_name}.txt")

        return {
            "success": True,
            "message": f"提示词 {prompt_name} 已更新",
            "backup_created": backup_file.exists()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新提示词失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

