"""
DeepSeek LLM 客户端 - 用于 Agent 决策和自动分类
"""
from typing import List, Dict, Any, Optional
from openai import OpenAI
from loguru import logger

from app.config import get_settings


class DeepSeekLLMClient:
    """DeepSeek LLM 客户端（OpenAI 兼容）"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(
            api_key=self.settings.deepseek_api_key,
            base_url=self.settings.deepseek_base_url
        )
        self.model = self.settings.deepseek_model
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        发送聊天请求
        
        Args:
            messages: 消息列表 [{"role": "user/assistant/system", "content": "..."}]
            temperature: 采样温度 (0-1)
            max_tokens: 最大 token 数
            response_format: 响应格式（如 {"type": "json_object"}）
        
        Returns:
            响应字典
        """
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature
            }
            
            if max_tokens:
                kwargs["max_tokens"] = max_tokens
            
            if response_format:
                kwargs["response_format"] = response_format
            
            response = self.client.chat.completions.create(**kwargs)
            
            return {
                "success": True,
                "content": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "finish_reason": response.choices[0].finish_reason,
                "error": None
            }
        
        except Exception as e:
            logger.error(f"LLM 请求失败: {e}", exc_info=True)
            return {
                "success": False,
                "content": None,
                "usage": None,
                "error": str(e)
            }
    
    def classify_document(
        self,
        title: str,
        first_pages_summary: str,
        categories: List[str]
    ) -> Dict[str, Any]:
        """
        自动分类文档（从 Prompt 文件读取）

        Args:
            title: 文档标题
            first_pages_summary: 前几页的摘要（通常是前 5 页）
            categories: 可选分类列表

        Returns:
            分类结果 {"category": str, "confidence": float, "reasoning": str}
        """
        from pathlib import Path

        # 读取 Prompt 文件（llm_client.py 在 backend/app/core/，所以需要 parent.parent.parent）
        prompts_dir = Path(__file__).parent.parent.parent / "prompts"
        system_prompt_file = prompts_dir / "classifier_system_prompt.txt"
        user_prompt_file = prompts_dir / "classifier_user_prompt.txt"

        # 准备 categories_str（在 try 外面，以便 except 中也能使用）
        categories_str = "、".join(categories)

        try:
            # 读取系统 Prompt
            with open(system_prompt_file, 'r', encoding='utf-8') as f:
                system_prompt = f.read()

            # 读取用户 Prompt 模板
            with open(user_prompt_file, 'r', encoding='utf-8') as f:
                user_prompt_template = f.read()

            # 替换占位符
            user_prompt = user_prompt_template.format(
                title=title,
                first_pages_summary=first_pages_summary,
                categories=categories_str
            )

        except Exception as e:
            logger.error(f"读取分类 Prompt 文件失败: {e}")
            # 降级到默认 Prompt
            system_prompt = "你是一个文档分类专家。请以 JSON 格式返回分类结果。"
            user_prompt = f"文档标题: {title}\n\n前几页内容摘要:\n{first_pages_summary}\n\n可选分类: {categories_str}\n\n请分类此文档。"

        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]

        result = self.chat(
            messages=messages,
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        if result["success"]:
            try:
                import json
                classification = json.loads(result["content"])
                return {
                    "success": True,
                    "category": classification.get("category", "其他"),
                    "confidence": float(classification.get("confidence", 0.5)),
                    "reasoning": classification.get("reasoning", ""),
                    "usage": result["usage"]
                }
            except Exception as e:
                logger.error(f"解析分类结果失败: {e}")
                return {
                    "success": False,
                    "category": "其他",
                    "confidence": 0.0,
                    "reasoning": f"解析失败: {e}",
                    "usage": result["usage"]
                }
        else:
            return {
                "success": False,
                "category": "其他",
                "confidence": 0.0,
                "reasoning": f"LLM 请求失败: {result['error']}",
                "usage": None
            }
    
    def evaluate_confidence(
        self,
        query: str,
        answer: str,
        sources: List[Dict[str, Any]]
    ) -> float:
        """
        评估答案置信度
        
        Args:
            query: 用户查询
            answer: 生成的答案
            sources: 来源引用列表
        
        Returns:
            置信度 (0-1)
        """
        sources_text = "\n".join([
            f"- 文档: {s['doc_title']}, 页码: {s['page_number']}, "
            f"相关度: {s['relevance_score']:.2f}"
            for s in sources
        ])
        
        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个答案质量评估专家。根据用户查询、生成的答案和来源引用，"
                    "评估答案的置信度（0-1）。\n"
                    "评估标准：\n"
                    "- 答案是否直接回答了问题\n"
                    "- 来源是否相关且可靠\n"
                    "- 答案是否有充分的证据支持\n"
                    "请只返回一个 0-1 之间的数字。"
                )
            },
            {
                "role": "user",
                "content": (
                    f"用户查询: {query}\n\n"
                    f"生成的答案: {answer}\n\n"
                    f"来源引用:\n{sources_text}\n\n"
                    f"请评估置信度（0-1）："
                )
            }
        ]
        
        result = self.chat(messages=messages, temperature=0.1, max_tokens=10)
        
        if result["success"]:
            try:
                confidence = float(result["content"].strip())
                return max(0.0, min(1.0, confidence))
            except:
                return 0.5
        else:
            return 0.5

