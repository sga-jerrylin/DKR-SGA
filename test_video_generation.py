"""
测试视频生成
"""
import sys
import os
from pathlib import Path

# 设置UTF-8编码
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from visual_memvid.enhanced_encoder import EnhancedPDFEncoder

def test_video_generation():
    """测试视频生成"""
    print("=" * 60)
    print("测试视频生成")
    print("=" * 60)
    
    # 使用已存在的PDF文件
    pdf_path = "backend/data/documents/doc_20251108_190509_7bf4c1b1.pdf"
    
    if not Path(pdf_path).exists():
        print(f"[ERROR] PDF file not found: {pdf_path}")
        return

    print(f"[OK] PDF file exists: {pdf_path}")
    
    # 初始化编码器
    print("\n初始化编码器...")
    encoder = EnhancedPDFEncoder(
        enable_summary=True,  # 启用Summary，测试完整流程
        enable_doris=False
    )
    
    # 编码
    print("\n开始编码...")
    result = encoder.encode_with_summary(
        pdf_path=pdf_path,
        output_dir="test_output",
        doc_id="test_video_002"  # 使用新的ID
    )
    
    print("\n" + "=" * 60)
    print("编码结果:")
    print("=" * 60)
    print(f"视频路径: {result.get('video_path')}")
    print(f"索引路径: {result.get('index_path')}")
    print(f"总页数: {result.get('total_pages')}")
    
    # 检查文件是否存在
    video_path = Path(result.get('video_path', ''))
    index_path = Path(result.get('index_path', ''))
    
    if video_path.exists():
        video_size = video_path.stat().st_size / (1024 * 1024)
        print(f"[OK] Video file exists: {video_size:.2f} MB")
    else:
        print(f"[ERROR] Video file not found: {video_path}")

    if index_path.exists():
        print(f"[OK] Index file exists")
    else:
        print(f"[ERROR] Index file not found: {index_path}")

if __name__ == "__main__":
    test_video_generation()

