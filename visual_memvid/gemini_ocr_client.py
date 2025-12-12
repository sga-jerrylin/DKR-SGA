"""
Gemini OCR Client via OpenRouter
用于通过 OpenRouter 调用 Gemini 模型进行 OCR
"""

from openai import OpenAI
from PIL import Image
import base64
from io import BytesIO
from typing import Dict, Optional
import time
from pathlib import Path


class GeminiOCRClient:
    """Gemini OCR 客户端（通过 OpenRouter）"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "google/gemini-2.5-flash-lite-preview-09-2025",
        base_url: str = "https://openrouter.ai/api/v1"
    ):
        """
        初始化 Gemini OCR 客户端
        
        Args:
            api_key: OpenRouter API Key
            model: Gemini 模型名称
            base_url: OpenRouter API 地址
        """
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )
        self.model = model
        self.is_available = True
        
        # 加载默认提示词
        self.default_summary_prompt = self._load_prompt("prompts/summary_rich_json.txt")
        self.default_fullpage_prompt = self._load_prompt("prompts/full_page_ocr_markdown.txt")
    
    def _load_prompt(self, prompt_path: str) -> str:
        """加载提示词文件"""
        try:
            # 支持相对路径和绝对路径
            path = Path(prompt_path)
            if not path.is_absolute():
                # 尝试多个可能的路径
                project_root = Path(__file__).parent.parent
                possible_paths = [
                    project_root / "backend" / prompt_path,  # 开发环境
                    project_root / prompt_path,  # Docker 环境
                    Path("/app") / prompt_path,  # Docker 绝对路径
                ]

                for p in possible_paths:
                    if p.exists():
                        path = p
                        break
                else:
                    print(f"⚠️ 提示词文件不存在: {prompt_path}")
                    return ""

            if path.exists():
                return path.read_text(encoding="utf-8")
            else:
                print(f"⚠️ 提示词文件不存在: {prompt_path}")
                return ""
        except Exception as e:
            print(f"❌ 加载提示词失败: {e}")
            return ""
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """将PIL图片转换为base64编码"""
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/png;base64,{img_base64}"
    
    def ocr_image(
        self,
        image: Image.Image,
        prompt: Optional[str] = None,
        mode: str = "summary"
    ) -> Dict:
        """
        对图片进行 OCR
        
        Args:
            image: PIL Image 对象
            prompt: 自定义提示词（如果为None，使用默认提示词）
            mode: OCR模式 ("summary" 或 "fullpage")
        
        Returns:
            {
                "success": True/False,
                "text": "OCR结果",
                "processing_time": 处理时间（秒）
            }
        """
        try:
            start_time = time.time()
            
            # 选择提示词
            if prompt is None:
                if mode == "summary":
                    prompt = self.default_summary_prompt
                else:
                    prompt = self.default_fullpage_prompt
            
            # 转换图片为base64
            img_url = self._image_to_base64(image)
            
            # 调用 Gemini API
            completion = self.client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "https://dkr-system.com",
                    "X-Title": "DKR Document Processing",
                },
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": img_url}}
                        ]
                    }
                ]
            )
            
            text = completion.choices[0].message.content
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "text": text,
                "processing_time": processing_time
            }
            
        except Exception as e:
            return {
                "success": False,
                "text": "",
                "error": str(e),
                "processing_time": time.time() - start_time
            }
    
    def _check_health(self) -> bool:
        """检查服务是否可用"""
        # Gemini 通过 OpenRouter 调用，不需要健康检查
        return True

