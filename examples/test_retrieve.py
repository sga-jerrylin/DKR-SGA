#!/usr/bin/env python3
"""
测试检索功能（需要 DeepSeek OCR 服务）

测试：视觉检索 + 自动前后页 + OCR 理解
"""

import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from visual_memvid import VisualMemvidRetriever, DeepSeekOCRClient
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_ocr_service():
    """
    测试 OCR 服务连接
    """
    print("\n" + "="*70)
    print("🔍 测试 DeepSeek OCR 服务")
    print("="*70 + "\n")
    
    try:
        client = DeepSeekOCRClient()
        print(f"✅ OCR 服务连接成功: {client.endpoint}")
        return True
    except Exception as e:
        print(f"❌ OCR 服务连接失败: {e}")
        print(f"\n💡 请确保 DeepSeek OCR 服务正在运行:")
        print(f"   - 检查服务地址: http://43.139.167.250:8200")
        print(f"   - 测试健康检查: curl http://43.139.167.250:8200/health")
        return False


def test_retrieve(video_path: str, index_path: str, queries: list):
    """
    测试视觉检索
    """
    print("\n" + "="*70)
    print("🚀 Visual-Memvid 检索测试")
    print("="*70 + "\n")
    
    video_path = Path(video_path)
    index_path = Path(index_path)
    
    if not video_path.exists():
        print(f"❌ 视频文件不存在: {video_path}")
        print(f"\n💡 请先运行编码测试:")
        print(f"   python examples/test_encode_only.py <pdf_path>")
        return
    
    if not index_path.exists():
        print(f"❌ 索引文件不存在: {index_path}")
        return
    
    print(f"📹 视频文件: {video_path}")
    print(f"📊 索引文件: {index_path}")
    
    # 初始化检索器
    print(f"\n🔧 初始化检索器...")
    retriever = VisualMemvidRetriever(str(video_path), str(index_path))
    
    print(f"✅ 检索器初始化完成")
    print(f"📚 知识库: {retriever.total_pages} 页\n")
    
    # 执行查询
    for i, query in enumerate(queries, 1):
        print("\n" + "━"*70)
        print(f"🔍 查询 {i}/{len(queries)}: {query}")
        print("━"*70 + "\n")
        
        try:
            # 检索（自动查看前后页）
            print(f"⏳ 检索中...")
            results = retriever.search(
                query,
                top_k=2,  # 返回前 2 个最相关的页面
                context_window=1,  # 前后各 1 页
                use_batch_ocr=True  # 使用批量 OCR
            )
            
            if not results:
                print("❌ 未找到匹配的页面\n")
                continue
            
            # 显示结果
            print(f"\n✅ 找到 {len(results)} 个相关页面\n")
            
            # 分组显示：核心页 vs 上下文页
            core_results = [r for r in results if r['is_core']]
            context_results = [r for r in results if not r['is_core']]
            
            # 显示核心页
            if core_results:
                print("┏" + "━"*68 + "┓")
                print("┃ 📌 核心结果 (最相关)" + " "*46 + "┃")
                print("┗" + "━"*68 + "┛\n")
                
                for result in core_results:
                    print(f"📄 第 {result['page_num']} 页 ⭐")
                    print(f"   ├─ 处理时间: {result['processing_time']:.2f}s")
                    
                    if result['metadata']:
                        meta = result['metadata']
                        if meta.get('chapter'):
                            print(f"   ├─ 章节: {meta['chapter']}")
                        if meta.get('has_table'):
                            print(f"   ├─ 包含表格: ✅")
                        if meta.get('has_formula'):
                            print(f"   ├─ 包含公式: ✅")
                        if meta.get('has_image'):
                            print(f"   ├─ 包含图片: ✅")
                    
                    print(f"   └─ 内容预览:")
                    content_preview = result['content'][:400].replace('\n', '\n      ')
                    print(f"      {content_preview}...")
                    print()
            
            # 显示上下文页
            if context_results:
                print("┏" + "━"*68 + "┓")
                print("┃ 📖 上下文 (前后页)" + " "*48 + "┃")
                print("┗" + "━"*68 + "┛\n")
                
                for result in context_results:
                    page_type_label = "⬅️ 前一页" if result['page_type'] == 'prev' else "➡️ 后一页"
                    print(f"📄 第 {result['page_num']} 页 {page_type_label}")
                    print(f"   ├─ 处理时间: {result['processing_time']:.2f}s")
                    print(f"   └─ 内容预览:")
                    content_preview = result['content'][:200].replace('\n', '\n      ')
                    print(f"      {content_preview}...")
                    print()
        
        except Exception as e:
            print(f"❌ 检索失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print("✅ 检索测试完成！")
    print("="*70 + "\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="测试 Visual-Memvid 检索")
    parser.add_argument(
        "--video",
        default="output/knowledge.mp4",
        help="视频文件路径"
    )
    parser.add_argument(
        "--index",
        default="output/index.json",
        help="索引文件路径"
    )
    parser.add_argument(
        "--query",
        action="append",
        help="查询（可多次指定）"
    )
    parser.add_argument(
        "--test-ocr-only",
        action="store_true",
        help="仅测试 OCR 服务连接"
    )
    
    args = parser.parse_args()
    
    if args.test_ocr_only:
        # 仅测试 OCR 服务
        test_ocr_service()
    else:
        # 先测试 OCR 服务
        if not test_ocr_service():
            print("\n⚠️ OCR 服务不可用，无法继续检索测试")
            sys.exit(1)
        
        # 默认查询
        queries = args.query or [
            "环保公益组织",
            "第 10 页",
            "表格",
        ]
        
        # 执行检索测试
        test_retrieve(args.video, args.index, queries)

