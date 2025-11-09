"""
OCR 缓存模块

缓存已 OCR 的页面，避免重复处理
"""

import json
import hashlib
from pathlib import Path
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class OCRCache:
    """
    OCR 结果缓存
    
    缓存策略：
    - 键: video_path + frame_num 的哈希
    - 值: OCR 结果（JSON）
    - 存储: 本地文件系统
    """
    
    def __init__(self, cache_dir: str = "ocr_cache"):
        """
        初始化缓存
        
        Args:
            cache_dir: 缓存目录
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        
        logger.info(f"📦 OCR 缓存目录: {self.cache_dir}")
    
    def _get_cache_key(self, video_path: str, frame_num: int) -> str:
        """
        生成缓存键
        
        Args:
            video_path: 视频文件路径
            frame_num: 帧号
        
        Returns:
            缓存键（哈希）
        """
        # 使用视频路径 + 帧号生成唯一键
        key_str = f"{Path(video_path).resolve()}_{frame_num}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_cache_file(self, video_path: str, frame_num: int) -> Path:
        """
        获取缓存文件路径
        
        Args:
            video_path: 视频文件路径
            frame_num: 帧号
        
        Returns:
            缓存文件路径
        """
        cache_key = self._get_cache_key(video_path, frame_num)
        
        # 使用视频名称作为子目录（便于管理）
        video_name = Path(video_path).stem
        cache_subdir = self.cache_dir / video_name
        cache_subdir.mkdir(exist_ok=True)
        
        return cache_subdir / f"{cache_key}.json"
    
    def get(self, video_path: str, frame_num: int) -> Optional[str]:
        """
        获取缓存的 OCR 结果
        
        Args:
            video_path: 视频文件路径
            frame_num: 帧号
        
        Returns:
            OCR 结果，如果不存在则返回 None
        """
        cache_file = self._get_cache_file(video_path, frame_num)
        
        if not cache_file.exists():
            return None
        
        try:
            with cache_file.open('r', encoding='utf-8') as f:
                data = json.load(f)
                logger.debug(f"✅ 缓存命中: 第 {frame_num + 1} 页")
                return data.get('content')
        except Exception as e:
            logger.warning(f"⚠️ 缓存读取失败: {e}")
            return None
    
    def set(self, video_path: str, frame_num: int, content: str):
        """
        设置缓存
        
        Args:
            video_path: 视频文件路径
            frame_num: 帧号
            content: OCR 结果
        """
        cache_file = self._get_cache_file(video_path, frame_num)
        
        try:
            with cache_file.open('w', encoding='utf-8') as f:
                json.dump({
                    'video_path': str(video_path),
                    'frame_num': frame_num,
                    'content': content
                }, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"💾 缓存已保存: 第 {frame_num + 1} 页")
        except Exception as e:
            logger.warning(f"⚠️ 缓存保存失败: {e}")
    
    def clear(self, video_path: Optional[str] = None):
        """
        清除缓存
        
        Args:
            video_path: 如果指定，只清除该视频的缓存；否则清除所有缓存
        """
        if video_path:
            # 清除特定视频的缓存
            video_name = Path(video_path).stem
            cache_subdir = self.cache_dir / video_name
            
            if cache_subdir.exists():
                import shutil
                shutil.rmtree(cache_subdir)
                logger.info(f"🗑️ 已清除缓存: {video_name}")
        else:
            # 清除所有缓存
            import shutil
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(exist_ok=True)
            logger.info(f"🗑️ 已清除所有缓存")
    
    def get_stats(self, video_path: Optional[str] = None) -> Dict:
        """
        获取缓存统计信息
        
        Args:
            video_path: 如果指定，只统计该视频的缓存
        
        Returns:
            统计信息
        """
        if video_path:
            video_name = Path(video_path).stem
            cache_subdir = self.cache_dir / video_name
            
            if not cache_subdir.exists():
                return {
                    'video': video_name,
                    'cached_pages': 0,
                    'total_size': 0
                }
            
            cache_files = list(cache_subdir.glob('*.json'))
            total_size = sum(f.stat().st_size for f in cache_files)
            
            return {
                'video': video_name,
                'cached_pages': len(cache_files),
                'total_size': total_size,
                'avg_size': total_size / len(cache_files) if cache_files else 0
            }
        else:
            # 统计所有缓存
            all_cache_files = list(self.cache_dir.rglob('*.json'))
            total_size = sum(f.stat().st_size for f in all_cache_files)
            
            # 按视频分组
            videos = {}
            for cache_file in all_cache_files:
                video_name = cache_file.parent.name
                if video_name not in videos:
                    videos[video_name] = 0
                videos[video_name] += 1
            
            return {
                'total_cached_pages': len(all_cache_files),
                'total_size': total_size,
                'videos': videos
            }

