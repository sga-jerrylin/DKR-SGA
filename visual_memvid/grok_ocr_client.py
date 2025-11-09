"""
Grok OCR Client via OpenRouter
用于通过 OpenRouter 调用 Grok-4-Fast 模型进行 OCR
"""

from openai import OpenAI
from PIL import Image
import base64
from io import BytesIO
from typing import Dict, Optional
import time
from pathlib import Path


class GrokOCRClient:
    """Grok OCR 客户端（通过 OpenRouter）"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "x-ai/grok-4-fast",
        base_url: str = "https://openrouter.ai/api/v1"
    ):
        """
        初始化 Grok OCR 客户端
        
        Args:
            api_key: OpenRouter API Key
            model: Grok 模型名称
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
                # 相对于项目根目录的 backend/prompts/
                project_root = Path(__file__).parent.parent
                path = project_root / "backend" / prompt_path

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
            
            # 调用 Grok API（通过 OpenRouter）
            completion = self.client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "https://dkr-system.com",
                    "X-Title": "DKR Document Processing",
                },
                extra_body={},  # Grok 需要 extra_body
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
                "processing_time": 0
            }

