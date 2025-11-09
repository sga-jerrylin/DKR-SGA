"""
测试 Summary 生成（不需要 Doris）

这个脚本只测试：
1. PDF → 视频编码
2. VLM Summary 生成
3. Summary 保存到 JSON

不需要 Doris，可以快速验证 Summary 功能
"""

import sys
import logging
import time
import json
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from visual_memvid import (
    EnhancedPDFEncoder,
    DeepSeekOCRClient,
    CONFIG
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """主函数"""
    logger.info("🚀 开始测试 Summary 生成")
    logger.info("=" * 80)
    
    # 检查 PDF 文件
    pdf_path = "2023中国环保公益组织现状调研报告.pdf"
    if not Path(pdf_path).exists():
        logger.error(f"❌ PDF 文件不存在: {pdf_path}")
        logger.info("请将测试 PDF 放在项目根目录")
        return
    
    try:
        # 创建 OCR 客户端
        logger.info("初始化 DeepSeek OCR 客户端...")
        ocr_client = DeepSeekOCRClient(endpoint=CONFIG["ocr"]["endpoint"])
        
        # 测试连接
        health = ocr_client._check_health()
        if not health:
            logger.error("❌ DeepSeek OCR 服务不可用")
            logger.info(f"请检查服务是否启动: {CONFIG['ocr']['endpoint']}")
            return
        
        logger.info("✅ DeepSeek OCR 服务正常")
        
        # 创建增强编码器（不使用 Doris）
        logger.info("\n创建增强编码器...")
        encoder = EnhancedPDFEncoder(
            ocr_client=ocr_client,
            doris_client=None,  # 不使用 Doris
            enable_summary=True,
            enable_doris=False
        )
        
        # 编码 PDF
        logger.info(f"\n开始编码: {pdf_path}")
        logger.info("=" * 80)
        start_time = time.time()
        
        result = encoder.encode_with_summary(
            pdf_path=pdf_path,
            output_dir="output"
        )
        
        total_time = time.time() - start_time
        
        # 打印结果
        logger.info("\n" + "=" * 80)
        logger.info("📊 编码结果:")
        logger.info("=" * 80)
        logger.info(f"  文档ID: {result['doc_id']}")
        logger.info(f"  文档名: {result['doc_name']}")
        logger.info(f"  总页数: {result['total_pages']}")
        logger.info(f"  视频路径: {result['video_path']}")
        logger.info(f"  索引路径: {result['index_path']}")
        logger.info(f"  Summary 数量: {len(result['summaries'])}")
        logger.info(f"  总耗时: {total_time:.1f} 秒")
        logger.info(f"  平均每页: {total_time/result['total_pages']:.1f} 秒")
        logger.info("=" * 80)
        
        # 打印前 5 页的 Summary
        logger.info("\n📄 前 5 页的 Summary:")
        logger.info("=" * 80)
        for i, summary in enumerate(result['summaries'][:5]):
            logger.info(f"\n第 {summary['page_num']} 页:")
            logger.info(f"  Summary: {summary['summary']}")
            logger.info(f"  关键词: {', '.join(summary['keywords'][:10])}")
            logger.info(f"  特征: 表格={summary['has_table']}, 公式={summary['has_formula']}, 图表={summary['has_chart']}")
            logger.info(f"  处理时间: {summary['processing_time']:.1f}秒")
        
        # 保存完整 Summary 到文件
        summary_file = Path("output") / "summaries.json"
        logger.info(f"\n💾 完整 Summary 已保存到: {summary_file}")
        
        # 统计信息
        logger.info("\n📈 统计信息:")
        logger.info("=" * 80)
        total_keywords = sum(len(s['keywords']) for s in result['summaries'])
        table_pages = sum(1 for s in result['summaries'] if s['has_table'])
        formula_pages = sum(1 for s in result['summaries'] if s['has_formula'])
        chart_pages = sum(1 for s in result['summaries'] if s['has_chart'])
        
        logger.info(f"  总关键词数: {total_keywords}")
        logger.info(f"  平均每页关键词: {total_keywords/len(result['summaries']):.1f}")
        logger.info(f"  包含表格的页数: {table_pages}")
        logger.info(f"  包含公式的页数: {formula_pages}")
        logger.info(f"  包含图表的页数: {chart_pages}")
        
        # 测试 Summary 搜索（简单关键词匹配）
        logger.info("\n🔍 测试 Summary 搜索:")
        logger.info("=" * 80)
        
        test_queries = [
            "环保公益组织",
            "614",
            "问卷调研",
            "占比"
        ]
        
        for query in test_queries:
            logger.info(f"\n查询: {query}")
            matches = []
            for summary in result['summaries']:
                if query in summary['summary'] or query in ','.join(summary['keywords']):
                    matches.append(summary)
            
            logger.info(f"  找到 {len(matches)} 个匹配页面")
            for match in matches[:2]:
                logger.info(f"    第 {match['page_num']} 页: {match['summary'][:60]}...")
        
        logger.info("\n" + "=" * 80)
        logger.info("🎉 测试完成！")
        logger.info("=" * 80)
        
        logger.info("\n💡 下一步:")
        logger.info("  1. 查看 output/summaries.json 了解完整 Summary")
        logger.info("  2. 如果有 Doris，运行 test_doris_integration.py 测试完整功能")
        logger.info("  3. 使用 test_retrieve.py 测试检索功能")
    
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

