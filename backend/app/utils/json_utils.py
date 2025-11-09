"""
JSON 处理工具
"""
import json
from pathlib import Path
from typing import Any, Dict, Union


def load_json(file_path: Union[str, Path]) -> Dict[str, Any]:
    """加载 JSON 文件（自动处理 UTF-8 BOM）"""
    with open(file_path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def save_json(data: Dict[str, Any], file_path: Union[str, Path], indent: int = 2) -> None:
    """保存 JSON 文件"""
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


def update_json(file_path: Union[str, Path], updates: Dict[str, Any]) -> Dict[str, Any]:
    """更新 JSON 文件"""
    if Path(file_path).exists():
        data = load_json(file_path)
    else:
        data = {}
    
    data.update(updates)
    save_json(data, file_path)
    return data

