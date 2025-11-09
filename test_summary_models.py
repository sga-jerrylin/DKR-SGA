#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试不同 Summary 模型的性能对比

对比三个模型：
1. Gemini 2.5 Flash Lite
2. Gemini 2.5 Flash
3. Qwen3-VL-235B

测试指标：
- 处理速度（秒/页）
- Summary 质量（长度、关键词数量）
- 成本估算
"""
import sys
import time
import json
from pathlib import Path
from typing import Dict, List

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from visual_memvid import CONFIG
from visual_memvid.gemini_ocr_client import GeminiOCRClient
from visual_memvid.qwen_ocr_client import QwenOCRClient
from PIL import Image


def test_model(model_name: str, client, test_image_path: str, num_tests: int = 3) -> Dict:
    """
    测试单个模型
    
    Args:
        model_name: 模型名称
        client: OCR 客户端
        test_image_path: 测试图片路径
        num_tests: 测试次数
    
    Returns:
        测试结果字典
    """
    print(f"\n{'='*80}")
    print(f"🧪 测试模型: {model_name}")
    print(f"{'='*80}")
    
    # 加载测试图片
    test_image = Image.open(test_image_path)
    print(f"📄 测试图片: {test_image_path}")
    print(f"📐 图片尺寸: {test_image.size}")
    
    results = []
    total_time = 0
    
    for i in range(num_tests):
        print(f"\n🔄 第 {i+1}/{num_tests} 次测试...")
        
        start_time = time.time()
        result = client.ocr_image(test_image, mode="summary")
        elapsed_time = time.time() - start_time
        
        if result.get("success"):
            summary_text = result["text"]
            summary_length = len(summary_text)
            
            print(f"  ✅ 成功")
            print(f"  ⏱️  耗时: {elapsed_time:.2f} 秒")
            print(f"  📝 Summary 长度: {summary_length} 字符")
            print(f"  📄 Summary 预览: {summary_text[:100]}...")
            
            results.append({
                "success": True,
                "time": elapsed_time,
                "length": summary_length,
                "text": summary_text
            })
            total_time += elapsed_time
        else:
            print(f"  ❌ 失败: {result.get('error')}")
            results.append({
                "success": False,
                "time": elapsed_time,
                "error": result.get("error")
            })
    
    # 计算统计数据
    successful_results = [r for r in results if r.get("success")]
    
    if successful_results:
        avg_time = sum(r["time"] for r in successful_results) / len(successful_results)
        avg_length = sum(r["length"] for r in successful_results) / len(successful_results)
        
        return {
            "model": model_name,
            "success_rate": len(successful_results) / num_tests,
            "avg_time": avg_time,
            "avg_length": avg_length,
            "total_time": total_time,
            "results": results
        }
    else:
        return {
            "model": model_name,
            "success_rate": 0,
            "error": "所有测试均失败"
        }


def main():
    """主函数"""
    print("🚀 Summary 模型性能对比测试")
    print("="*80)
    
    # 检查测试图片
    test_image_path = "test_page.png"
    if not Path(test_image_path).exists():
        print(f"❌ 测试图片不存在: {test_image_path}")
        print("请提供一个测试图片（PDF 的某一页）")
        return
    
    # 获取 API Key
    api_key = CONFIG["api_keys"]["openrouter"]
    
    # 定义测试模型
    models = [
        {
            "name": "Gemini 2.5 Flash Lite",
            "client": GeminiOCRClient(
                api_key=api_key,
                model="google/gemini-2.5-flash-lite-preview-09-2025"
            )
        },
        {
            "name": "Gemini 2.5 Flash",
            "client": GeminiOCRClient(
                api_key=api_key,
                model="google/gemini-2.5-flash-preview-09-2025"
            )
        },
        {
            "name": "Qwen3-VL-235B",
            "client": QwenOCRClient(
                api_key=api_key,
                model="qwen/qwen3-vl-235b-a22b-instruct"
            )
        }
    ]
    
    # 测试所有模型
    all_results = []
    for model_config in models:
        result = test_model(
            model_name=model_config["name"],
            client=model_config["client"],
            test_image_path=test_image_path,
            num_tests=3
        )
        all_results.append(result)
    
    # 打印对比结果
    print(f"\n\n{'='*80}")
    print("📊 性能对比结果")
    print(f"{'='*80}\n")
    
    print(f"{'模型':<30} {'成功率':<10} {'平均耗时':<15} {'平均长度':<15}")
    print("-"*80)
    
    for result in all_results:
        if result.get("success_rate", 0) > 0:
            print(f"{result['model']:<30} "
                  f"{result['success_rate']*100:>6.1f}%   "
                  f"{result['avg_time']:>10.2f} 秒   "
                  f"{result['avg_length']:>10.0f} 字符")
        else:
            print(f"{result['model']:<30} {'失败':<10}")
    
    # 保存详细结果
    output_file = "summary_model_comparison.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 详细结果已保存到: {output_file}")


if __name__ == "__main__":
    main()

