"""
工具函数
"""
from .file_utils import generate_doc_id, get_file_hash
from .json_utils import load_json, save_json

__all__ = [
    "generate_doc_id",
    "get_file_hash",
    "load_json",
    "save_json",
]

