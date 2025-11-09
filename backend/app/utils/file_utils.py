"""
文件处理工具
"""
import hashlib
import uuid
from pathlib import Path
from typing import Union


def generate_doc_id() -> str:
    """生成文档 ID"""
    return str(uuid.uuid4())


def get_file_hash(file_path: Union[str, Path]) -> str:
    """计算文件 SHA256 哈希值"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_file_size(file_path: Union[str, Path]) -> int:
    """获取文件大小（字节）"""
    return Path(file_path).stat().st_size


def ensure_dir(directory: Union[str, Path]) -> Path:
    """确保目录存在"""
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    return path

