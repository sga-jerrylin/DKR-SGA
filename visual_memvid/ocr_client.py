"""
DeepSeek OCR Client

封装 DeepSeek OCR API 调用，支持单张和批量处理
"""

import requests
import base64
import io
import time
from typing import List, Dict, Optional, Union
from pathlib import Path
import numpy as np
from PIL import Image
import cv2
import logging

from .config import CONFIG

logger = logging.getLogger(__name__)


class DeepSeekOCRClient:
    """
    DeepSeek OCR 客户端
    
    支持：
    - 单张图片 OCR
    - 批量图片 OCR
    - Base64 图片 OCR
    - 自动重试和错误处理
    """
    
    def __init__(self, endpoint: Optional[str] = None):
        """
        初始化 OCR 客户端

        Args:
            endpoint: OCR 服务地址，默认从配置读取
        """
        self.endpoint = endpoint or CONFIG["ocr"]["endpoint"]
        self.batch_size = CONFIG["ocr"]["batch_size"]

        # 从提示词文件加载默认提示词
        self.default_prompt = self._load_prompt(CONFIG["ocr"]["prompt_file"])

        self.is_available = False

        # 检查服务健康状态（不抛出异常）
        self.is_available = self._check_health()

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
                    logger.warning(f"⚠️ 提示词文件不存在: {prompt_path}，使用默认提示词")
                    return "<image>\n请将这页文档的全部内容转换为Markdown格式。"

            if path.exists():
                return path.read_text(encoding="utf-8")
            else:
                logger.warning(f"⚠️ 提示词文件不存在: {prompt_path}，使用默认提示词")
                return "<image>\n请将这页文档的全部内容转换为Markdown格式。"
        except Exception as e:
            logger.error(f"❌ 加载提示词失败: {e}，使用默认提示词")
            return "<image>\n请将这页文档的全部内容转换为Markdown格式。"
    
    def _check_health(self) -> bool:
        """检查 OCR 服务是否可用"""
        logger.info(f"🔍 检查 OCR 服务健康状态: {self.endpoint}")
        try:
            # 禁用代理
            proxies = {
                'http': None,
                'https': None,
            }
            logger.debug(f"   发送健康检查请求 (禁用代理)...")
            response = requests.get(f"{self.endpoint}/health", timeout=5, proxies=proxies)
            logger.debug(f"   收到响应: {response.status_code}")

            if response.status_code == 200:
                health = response.json()
                logger.info(f"✅ DeepSeek OCR 服务正常: {health}")
                return True
            else:
                logger.warning(f"⚠️ DeepSeek OCR 服务异常: {response.status_code}")
                return False
        except Exception as e:
            logger.warning(f"⚠️ 无法连接到 DeepSeek OCR 服务: {e}")
            logger.warning(f"⚠️ OCR 服务将不可用: {self.endpoint}")
            return False
    
    def ocr_image(
        self,
        image: Union[str, Path, np.ndarray, Image.Image],
        prompt: Optional[str] = None,
        **kwargs
    ) -> Dict:
        """
        单张图片 OCR

        Args:
            image: 图片路径、numpy 数组或 PIL Image
            prompt: OCR 提示词
            **kwargs: 其他参数 (base_size, image_size, crop_mode)

        Returns:
            {
                "success": bool,
                "text": str,
                "processing_time": float,
                "error": str or None
            }
        """
        import time
        start_time = time.time()

        try:
            prompt = prompt or self.default_prompt

            # 禁用代理
            proxies = {
                'http': None,
                'https': None,
            }

            logger.debug(f"📡 开始 OCR 请求: 图片类型={type(image).__name__}")

            # 转换图片为文件对象
            if isinstance(image, (str, Path)):
                # 文件路径
                with open(image, "rb") as f:
                    files = {"file": (Path(image).name, f, "image/png")}
                    data = {
                        "prompt": prompt,
                        "base_size": str(kwargs.get("base_size", CONFIG["ocr"]["base_size"])),
                        "image_size": str(kwargs.get("image_size", CONFIG["ocr"]["image_size"])),
                        "crop_mode": "true" if kwargs.get("crop_mode", CONFIG["ocr"]["crop_mode"]) else "false",
                    }
                    logger.debug(f"   发送 OCR 请求到: {self.endpoint}/ocr/image")
                    response = requests.post(
                        f"{self.endpoint}/ocr/image",
                        files=files,
                        data=data,
                        proxies=proxies,
                        timeout=300
                    )
                    logger.debug(f"   收到响应: {response.status_code}")
            elif isinstance(image, np.ndarray):
                # OpenCV 图片
                _, buffer = cv2.imencode('.png', image)
                files = {"file": ("image.png", io.BytesIO(buffer), "image/png")}
                data = {
                    "prompt": prompt,
                    "base_size": str(kwargs.get("base_size", CONFIG["ocr"]["base_size"])),
                    "image_size": str(kwargs.get("image_size", CONFIG["ocr"]["image_size"])),
                    "crop_mode": "true" if kwargs.get("crop_mode", CONFIG["ocr"]["crop_mode"]) else "false",
                }
                logger.debug(f"   发送 OCR 请求到: {self.endpoint}/ocr/image")
                response = requests.post(
                    f"{self.endpoint}/ocr/image",
                    files=files,
                    data=data,
                    proxies=proxies,
                    timeout=300
                )
                logger.debug(f"   收到响应: {response.status_code}")
            elif isinstance(image, Image.Image):
                # PIL Image
                buffer = io.BytesIO()
                image.save(buffer, format='PNG')
                buffer.seek(0)
                files = {"file": ("image.png", buffer, "image/png")}
                data = {
                    "prompt": prompt,
                    "base_size": str(kwargs.get("base_size", CONFIG["ocr"]["base_size"])),
                    "image_size": str(kwargs.get("image_size", CONFIG["ocr"]["image_size"])),
                    "crop_mode": "true" if kwargs.get("crop_mode", CONFIG["ocr"]["crop_mode"]) else "false",
                }
                logger.debug(f"   发送 OCR 请求到: {self.endpoint}/ocr/image")
                response = requests.post(
                    f"{self.endpoint}/ocr/image",
                    files=files,
                    data=data,
                    proxies=proxies,
                    timeout=300
                )
                logger.debug(f"   收到响应: {response.status_code}")
            else:
                raise ValueError(f"不支持的图片类型: {type(image)}")

            # 解析响应
            elapsed_time = time.time() - start_time

            if response.status_code == 200:
                result = response.json()
                # 安全获取 text 字段（可能为 None）
                text = result.get('text') or ''
                logger.info(f"✅ OCR 成功: 耗时 {elapsed_time:.2f}秒, 文本长度 {len(text)}")
                return result
            else:
                logger.error(f"❌ OCR 请求失败: {response.status_code} - {response.text[:200]}")
                return {
                    "success": False,
                    "text": None,
                    "processing_time": elapsed_time,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }

        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"❌ OCR 异常: {e}", exc_info=True)
            return {
                "success": False,
                "text": None,
                "processing_time": elapsed_time,
                "error": f"OCR 异常: {str(e)}"
            }
    
    def ocr_batch(
        self,
        images: List[Union[str, Path, np.ndarray]],
        prompt: Optional[str] = None,
        **kwargs
    ) -> List[Dict]:
        """
        批量图片 OCR
        
        Args:
            images: 图片列表（路径或 numpy 数组）
            prompt: OCR 提示词
            **kwargs: 其他参数
        
        Returns:
            List of OCR results
        """
        prompt = prompt or self.default_prompt
        
        # 准备文件列表
        files = []
        temp_buffers = []  # 保持引用，避免被垃圾回收
        
        for i, image in enumerate(images):
            if isinstance(image, (str, Path)):
                # 文件路径
                f = open(image, "rb")
                files.append(("files", (f"image_{i}.png", f, "image/png")))
                temp_buffers.append(f)
            elif isinstance(image, np.ndarray):
                # OpenCV 图片
                _, buffer = cv2.imencode('.png', image)
                bio = io.BytesIO(buffer)
                files.append(("files", (f"image_{i}.png", bio, "image/png")))
                temp_buffers.append(bio)
            else:
                raise ValueError(f"不支持的图片类型: {type(image)}")
        
        # 发送批量请求
        data = {
            "prompt": prompt,
            "base_size": kwargs.get("base_size", CONFIG["ocr"]["base_size"]),
            "image_size": kwargs.get("image_size", CONFIG["ocr"]["image_size"]),
            "crop_mode": kwargs.get("crop_mode", CONFIG["ocr"]["crop_mode"]),
        }
        
        try:
            response = requests.post(
                f"{self.endpoint}/ocr/batch",
                files=files,
                data=data
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"批量 OCR 请求失败: {response.status_code}")
                return [
                    {
                        "success": False,
                        "text": None,
                        "processing_time": None,
                        "error": f"HTTP {response.status_code}"
                    }
                    for _ in images
                ]
        finally:
            # 关闭文件句柄
            for buf in temp_buffers:
                if hasattr(buf, 'close'):
                    buf.close()
    
    def ocr_base64(
        self,
        image_base64: str,
        prompt: Optional[str] = None,
        **kwargs
    ) -> Dict:
        """
        Base64 图片 OCR
        
        Args:
            image_base64: Base64 编码的图片
            prompt: OCR 提示词
            **kwargs: 其他参数
        
        Returns:
            OCR result
        """
        prompt = prompt or self.default_prompt
        
        payload = {
            "image_base64": image_base64,
            "prompt": prompt,
            "base_size": kwargs.get("base_size", CONFIG["ocr"]["base_size"]),
            "image_size": kwargs.get("image_size", CONFIG["ocr"]["image_size"]),
            "crop_mode": kwargs.get("crop_mode", CONFIG["ocr"]["crop_mode"]),
        }
        
        response = requests.post(
            f"{self.endpoint}/ocr/base64",
            json=payload
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Base64 OCR 请求失败: {response.status_code}")
            return {
                "success": False,
                "text": None,
                "processing_time": None,
                "error": f"HTTP {response.status_code}"
            }

